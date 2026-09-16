from __future__ import annotations

from typing import Sequence

from django.db import models, transaction
from django.db.models import Avg, Count, Max, Min, Q

from . import anomaly
from .csv_import import ParsedReading

# Keep the insert batches modest so a large upload does not build one enormous
# SQL statement.
BULK_BATCH_SIZE = 1_000


class ReadingQuerySet(models.QuerySet):
    """Query vocabulary for readings, so views never build filters by hand."""

    def in_distance_range(
        self, from_m: float | None = None, to_m: float | None = None
    ) -> "ReadingQuerySet":
        """Narrow to an inclusive distance window.

        An inverted or out-of-range window is a legitimate question with an
        empty answer, so it yields no rows rather than raising.
        """
        queryset = self
        if from_m is not None:
            queryset = queryset.filter(distance_m__gte=from_m)
        if to_m is not None:
            queryset = queryset.filter(distance_m__lte=to_m)
        return queryset

    def anomalous(self) -> "ReadingQuerySet":
        return self.filter(anomaly=True)

    def pressure_stats(self) -> dict[str, float | int | None]:
        """Aggregate pressure statistics for whatever this queryset covers.

        On an empty queryset the min/max/mean come back as None rather than
        zero, which would read as a real measurement.
        """
        stats = self.aggregate(
            pressure_min=Min("pressure_bar"),
            pressure_max=Max("pressure_bar"),
            pressure_mean=Avg("pressure_bar"),
            count=Count("id"),
            anomaly_count=Count("id", filter=Q(anomaly=True)),
        )
        if stats["pressure_mean"] is not None:
            stats["pressure_mean"] = round(stats["pressure_mean"], 4)
        return stats


class RunManager(models.Manager):
    def current(self) -> "Run | None":
        """The single loaded run, or None when nothing has been uploaded yet."""
        return self.first()

    @transaction.atomic
    def replace(
        self,
        filename: str,
        parsed: Sequence[ParsedReading],
        is_sample: bool = False,
    ) -> "Run":
        """Store `parsed` as the one current run, discarding any previous one.

        Anomaly flags are computed here, once, over the complete run. Doing it
        at write time rather than per request keeps a reading's verdict
        independent of whatever distance filter the client later applies.
        """
        self.all().delete()
        run = self.create(filename=filename, is_sample=is_sample)

        verdicts = anomaly.evaluate([reading.pressure_bar for reading in parsed])
        Reading.objects.bulk_create(
            (
                Reading(
                    run=run,
                    distance_m=reading.distance_m,
                    pressure_bar=reading.pressure_bar,
                    temperature_c=reading.temperature_c,
                    anomaly=verdict.anomaly,
                    baseline_mean=verdict.baseline_mean,
                    baseline_std=verdict.baseline_std,
                )
                for reading, verdict in zip(parsed, verdicts)
            ),
            batch_size=BULK_BATCH_SIZE,
        )
        return run


class Run(models.Model):
    """One inspection run.

    The app holds exactly one run at a time: an upload replaces whatever was
    loaded before, as the assignment specifies.
    """

    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_sample = models.BooleanField(default=False)

    objects = RunManager()

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self) -> str:
        return self.filename


class Reading(models.Model):
    """A single pressure/temperature sample at one position along the pipeline."""

    run = models.ForeignKey(Run, related_name="readings", on_delete=models.CASCADE)
    distance_m = models.IntegerField(db_index=True)
    pressure_bar = models.FloatField()
    temperature_c = models.FloatField()

    anomaly = models.BooleanField(default=False)
    # Null for the first readings of a run: the window is too short for a
    # standard deviation.
    baseline_mean = models.FloatField(null=True, blank=True)
    baseline_std = models.FloatField(null=True, blank=True)

    objects = ReadingQuerySet.as_manager()

    class Meta:
        ordering = ["distance_m"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "distance_m"], name="unique_distance_per_run"
            )
        ]

    def __str__(self) -> str:
        return f"{self.distance_m} m: {self.pressure_bar} bar"

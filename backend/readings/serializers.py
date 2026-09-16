from django.db.models import Max, Min
from rest_framework import serializers

from .anomaly import THRESHOLD_SIGMAS, WINDOW_SIZE
from .models import Reading, Run


class OptionalFloatField(serializers.FloatField):
    """A float that treats an omitted or blank query parameter as "no bound".

    `?from_m=` is what a cleared input sends, and it means the same as leaving
    the parameter out entirely.
    """

    def validate_empty_values(self, data):
        if data == "":
            return True, None
        return super().validate_empty_values(data)


class DistanceRangeSerializer(serializers.Serializer):
    """Validates the optional `from_m` / `to_m` query parameters."""

    from_m = OptionalFloatField(
        required=False,
        allow_null=True,
        default=None,
        error_messages={"invalid": "must be a number."},
    )
    to_m = OptionalFloatField(
        required=False,
        allow_null=True,
        default=None,
        error_messages={"invalid": "must be a number."},
    )


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = [
            "distance_m",
            "pressure_bar",
            "temperature_c",
            "anomaly",
            "baseline_mean",
            "baseline_std",
        ]


class RunSerializer(serializers.ModelSerializer):
    reading_count = serializers.IntegerField(source="readings.count", read_only=True)
    anomaly_rule = serializers.SerializerMethodField()
    distance_range = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = [
            "filename",
            "uploaded_at",
            "is_sample",
            "reading_count",
            "distance_range",
            "anomaly_rule",
        ]

    def get_anomaly_rule(self, obj: Run) -> dict:
        """Expose the detector's parameters so the UI can label the chart."""
        return {"window_size": WINDOW_SIZE, "threshold_sigmas": THRESHOLD_SIGMAS}

    def get_distance_range(self, obj: Run) -> dict:
        """Full extent of the run, independent of any filter.

        The UI needs it to offer range presets and input hints for an
        arbitrary uploaded file, which it cannot infer from filtered readings.
        """
        return obj.readings.aggregate(
            from_m=Min("distance_m"), to_m=Max("distance_m")
        )

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import DatabaseError, IntegrityError

from readings.sample import load_sample_fixture


class Command(BaseCommand):
    help = "Load the bundled sample fixture as the current run, replacing any existing one."

    def handle(self, *args, **options):
        try:
            load_sample_fixture()
        except (DatabaseError, IntegrityError, CommandError) as exc:
            raise CommandError(str(exc)) from exc

        from readings.models import Run

        run = Run.objects.current()
        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {run.filename}: {run.readings.count()} readings, "
                f"{run.readings.filter(anomaly=True).count()} anomalies."
            )
        )

from django.core.management.base import BaseCommand, CommandError

from readings.csv_import import CsvValidationError
from readings.sample import load_sample


class Command(BaseCommand):
    help = "Load the bundled sample CSV as the current run, replacing any existing one."

    def handle(self, *args, **options):
        try:
            run = load_sample()
        except (CsvValidationError, OSError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {run.filename}: {run.readings.count()} readings, "
                f"{run.readings.filter(anomaly=True).count()} anomalies."
            )
        )

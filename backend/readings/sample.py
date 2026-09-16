"""Loading of the sample run, so the app can open with data.

No CSV is committed to the repository. If one is present at
``settings.SAMPLE_CSV_PATH`` it is loaded on startup as a convenience; if not,
the app simply starts empty and waits for an upload.
"""

from __future__ import annotations

import logging

from django.conf import settings

from .csv_import import CsvValidationError, parse_readings
from .models import Run

logger = logging.getLogger(__name__)


def load_sample() -> Run:
    """Load the sample CSV as the current run, replacing anything present."""
    path = settings.SAMPLE_CSV_PATH
    readings = parse_readings(path.read_bytes())
    run = Run.objects.replace(path.name, readings, is_sample=True)
    logger.info("Loaded sample run %s (%d readings)", path.name, len(readings))
    return run


def load_sample_if_empty() -> Run | None:
    """Seed the sample run on startup, unless a run is already loaded.

    Startup must not fail because the sample file is missing or unreadable, so
    problems here are logged and the app comes up with no run loaded.
    """
    if Run.objects.exists():
        return None

    path = settings.SAMPLE_CSV_PATH
    if not path.is_file():
        logger.warning(
            "Sample CSV not found at %s; starting with no run loaded.", path
        )
        return None

    try:
        return load_sample()
    except (CsvValidationError, OSError) as exc:
        logger.warning("Could not load sample CSV %s: %s", path, exc)
        return None

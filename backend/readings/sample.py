"""Load the bundled sample fixture in development."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import DatabaseError, IntegrityError

from .models import Run

logger = logging.getLogger(__name__)

SAMPLE_FIXTURE = "sample_run"


def load_sample_fixture() -> None:
    """Replace whatever is loaded with the bundled sample run."""
    Run.objects.all().delete()
    call_command("loaddata", SAMPLE_FIXTURE, verbosity=0)


def load_sample_fixture_if_empty() -> bool:
    """Load the sample fixture when the database has no run yet.

    Used on process start in development. Production leaves the database
    empty until something is uploaded. Missing tables (unmigrated) are
    logged rather than crashing startup.
    """
    if not getattr(settings, "LOAD_SAMPLE_FIXTURE", False):
        return False
    try:
        if Run.objects.exists():
            return False
        call_command("loaddata", SAMPLE_FIXTURE, verbosity=0)
    except (DatabaseError, IntegrityError, CommandError) as exc:
        logger.warning("Could not load sample fixture: %s", exc)
        return False
    logger.info("Loaded sample fixture %s", SAMPLE_FIXTURE)
    return True

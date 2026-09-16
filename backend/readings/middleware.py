"""Startup seeding of a sample run, when a sample CSV is available."""

from __future__ import annotations

import logging
import threading

from django.conf import settings
from django.db.utils import DatabaseError

logger = logging.getLogger(__name__)


class SampleRunMiddleware:
    """Load the sample run once, when the first request reaches the process.

    The assignment asks for the sample to be loaded on startup. Doing that in
    ``AppConfig.ready()`` would mean querying the database during app
    initialisation, which Django warns against, so it happens on the first
    request instead: by the time anyone can see the app, the data is there.

    A missing sample CSV is not an error; the app then starts with no run.
    """

    _lock = threading.Lock()
    _loaded = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._ensure_loaded()
        return self.get_response(request)

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._loaded or not settings.LOAD_SAMPLE_ON_FIRST_REQUEST:
            return

        with cls._lock:
            if cls._loaded:
                return

            from .sample import load_sample_if_empty

            try:
                load_sample_if_empty()
            except DatabaseError:
                # Usually an unmigrated database. Leave the flag unset so the
                # next request tries again once `migrate` has been run.
                logger.warning(
                    "Could not seed the sample run: database not ready. "
                    "Run `python manage.py migrate`."
                )
                return

            cls._loaded = True

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pipeline.settings")

application = get_wsgi_application()

from readings.sample import load_sample_fixture_if_empty  # noqa: E402

load_sample_fixture_if_empty()

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pipeline.settings")

application = get_asgi_application()

from readings.sample import load_sample_fixture_if_empty  # noqa: E402

load_sample_fixture_if_empty()

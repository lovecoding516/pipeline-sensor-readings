"""Domain exceptions and the handler that gives every error one shape.

DRF already renders an ``APIException`` as ``{"detail": "..."}``, so views raise
these instead of assembling error responses by hand. The handler below extends
that to field-level validation errors, which DRF would otherwise render as
``{"from_m": ["..."]}`` and give the frontend a second shape to parse.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class InvalidReadingsFile(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The uploaded file is not a valid readings CSV."
    default_code = "invalid_readings_file"


class NoRunLoaded(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "No run is loaded. Upload a readings CSV to POST /upload."
    default_code = "no_run_loaded"


def _flatten(data: object) -> str:
    """Reduce a DRF error payload to a single readable sentence."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return " ".join(_flatten(item) for item in data) if data else "Invalid request."
    if isinstance(data, dict):
        parts = []
        for field, value in data.items():
            message = _flatten(value)
            # Field errors read better prefixed; a bare "detail" is already a
            # complete sentence.
            parts.append(message if field == "detail" else f"{field}: {message}")
        return " ".join(parts)
    return str(data)


def api_exception_handler(exc: Exception, context: dict):
    """Normalise every handled error to ``{"detail": "<message>"}``."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if not (
        isinstance(response.data, dict)
        and isinstance(response.data.get("detail"), str)
    ):
        response.data = {"detail": _flatten(response.data)}
    return response

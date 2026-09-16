"""The three endpoints the assignment asks for.

The views stay thin on purpose: query logic lives on `ReadingQuerySet`, writes
on `RunManager`, parsing in `csv_import`, and error rendering in `exceptions`.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .csv_import import CsvValidationError, parse_readings
from .exceptions import InvalidReadingsFile, NoRunLoaded
from .models import ReadingQuerySet, Run
from .serializers import DistanceRangeSerializer, ReadingSerializer, RunSerializer


class IndexView(APIView):
    """Endpoint listing, so the API root is not a 404 when opened in a browser."""

    def get(self, _request: Request) -> Response:
        return Response(
            {
                "endpoints": {
                    "POST /upload": "Replace the current run with an uploaded CSV "
                                    "(multipart/form-data, field name 'file').",
                    "GET /readings": "Readings of the current run; optional "
                                     "?from_m=&to_m= distance filter.",
                    "GET /summary": "Pressure statistics for the (optionally "
                                    "filtered) range.",
                }
            }
        )


class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request) -> Response:
        uploaded = request.FILES.get("file")
        if uploaded is None:
            raise InvalidReadingsFile(
                "No file was uploaded. Send the CSV as multipart/form-data "
                "under the field name 'file'."
            )

        try:
            readings = parse_readings(uploaded.read())
        except CsvValidationError as exc:
            # Nothing has been written yet, so the previously loaded run survives.
            raise InvalidReadingsFile(str(exc)) from exc
        except OSError as exc:
            raise InvalidReadingsFile(
                "The uploaded file could not be read. Please try again."
            ) from exc

        run = Run.objects.replace(uploaded.name or "upload.csv", readings)
        return Response(
            {"run": RunSerializer(run).data}, status=status.HTTP_201_CREATED
        )


class CurrentRunView(APIView):
    """Shared plumbing for the two read endpoints."""

    def get_run(self) -> Run:
        run = Run.objects.current()
        if run is None:
            raise NoRunLoaded()
        return run

    def get_distance_range(self, request: Request) -> dict[str, float | None]:
        serializer = DistanceRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def get_readings(
        self, request: Request
    ) -> tuple[Run, dict[str, float | None], ReadingQuerySet]:
        run = self.get_run()
        distance_range = self.get_distance_range(request)
        return run, distance_range, run.readings.in_distance_range(**distance_range)


class ReadingsView(CurrentRunView):
    def get(self, request: Request) -> Response:
        run, distance_range, readings = self.get_readings(request)
        return Response(
            {
                "run": RunSerializer(run).data,
                "filter": distance_range,
                "count": readings.count(),
                "readings": ReadingSerializer(readings, many=True).data,
            }
        )


class SummaryView(CurrentRunView):
    def get(self, request: Request) -> Response:
        run, distance_range, readings = self.get_readings(request)
        return Response(
            {
                "run": RunSerializer(run).data,
                "filter": distance_range,
                **readings.pressure_stats(),
            }
        )

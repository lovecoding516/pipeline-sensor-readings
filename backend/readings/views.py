"""The three endpoints the assignment asks for.

Upload, list and summary are DRF generic views bound to `Run` / `Reading`.
Query logic stays on `ReadingQuerySet`, writes on `RunManager`.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import NoRunLoaded
from .filters import ReadingFilter
from .models import Reading, Run
from .serializers import (
    ErrorSerializer,
    IndexSerializer,
    ReadingsResponseSerializer,
    ReadingSerializer,
    RunSerializer,
    SummaryResponseSerializer,
    UploadResponseSerializer,
    UploadSerializer,
)

DISTANCE_PARAMETERS = [
    OpenApiParameter(
        name="from_m",
        type=float,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Inclusive start of the distance window, in metres.",
    ),
    OpenApiParameter(
        name="to_m",
        type=float,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Inclusive end of the distance window, in metres.",
    ),
]


class IndexView(APIView):
    """Endpoint listing, so the API root is not a 404 when opened in a browser."""

    @extend_schema(responses=IndexSerializer)
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
                    "GET /docs": "Swagger UI for this API.",
                    "GET /schema": "OpenAPI 3 schema.",
                }
            }
        )


class UploadView(generics.CreateAPIView):
    serializer_class = UploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=UploadSerializer,
        responses={
            201: UploadResponseSerializer,
            400: ErrorSerializer,
        },
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save()
        return Response(
            {"run": RunSerializer(run).data}, status=status.HTTP_201_CREATED
        )


class CurrentRunMixin:
    """Shared queryset for the two read endpoints: the current run's readings."""

    filterset_class = ReadingFilter

    def get_run(self) -> Run:
        run = getattr(self, "_run", None)
        if run is None:
            run = Run.objects.current()
            if run is None:
                raise NoRunLoaded()
            self._run = run
        return run

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Reading.objects.none()
        return self.get_run().readings.all()

    def filter_queryset(self, queryset):
        filterset = self.filterset_class(
            data=self.request.query_params,
            queryset=queryset,
            request=self.request,
        )
        if not filterset.is_valid():
            raise ValidationError(filterset.errors)
        self.distance_range = filterset.applied_range()
        return filterset.qs


class ReadingsView(CurrentRunMixin, generics.ListAPIView):
    serializer_class = ReadingSerializer

    @extend_schema(
        parameters=DISTANCE_PARAMETERS,
        responses={
            200: ReadingsResponseSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        },
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        readings = self.filter_queryset(self.get_queryset())
        return Response(
            {
                "run": RunSerializer(self.get_run()).data,
                "filter": self.distance_range,
                "count": readings.count(),
                "readings": self.get_serializer(readings, many=True).data,
            }
        )


class SummaryView(CurrentRunMixin, generics.GenericAPIView):
    serializer_class = ReadingSerializer
    @extend_schema(
        parameters=DISTANCE_PARAMETERS,
        responses={
            200: SummaryResponseSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        },
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        readings = self.filter_queryset(self.get_queryset())
        return Response(
            {
                "run": RunSerializer(self.get_run()).data,
                "filter": self.distance_range,
                **readings.pressure_stats(),
            }
        )

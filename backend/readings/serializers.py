from django.db.models import Max, Min
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .anomaly import THRESHOLD_SIGMAS, WINDOW_SIZE
from .csv_import import CsvValidationError, parse_readings
from .exceptions import InvalidReadingsFile
from .models import Reading, Run


class DistanceRangeSerializer(serializers.Serializer):
    from_m = serializers.FloatField(allow_null=True)
    to_m = serializers.FloatField(allow_null=True)


class AnomalyRuleSerializer(serializers.Serializer):
    window_size = serializers.IntegerField()
    threshold_sigmas = serializers.FloatField()


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = [
            "distance_m",
            "pressure_bar",
            "temperature_c",
            "anomaly",
            "baseline_mean",
            "baseline_std",
        ]


class RunSerializer(serializers.ModelSerializer):
    reading_count = serializers.IntegerField(source="readings.count", read_only=True)
    anomaly_rule = serializers.SerializerMethodField()
    distance_range = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = [
            "filename",
            "uploaded_at",
            "is_sample",
            "reading_count",
            "distance_range",
            "anomaly_rule",
        ]

    @extend_schema_field(AnomalyRuleSerializer)
    def get_anomaly_rule(self, obj: Run) -> dict:
        return {"window_size": WINDOW_SIZE, "threshold_sigmas": THRESHOLD_SIGMAS}

    @extend_schema_field(DistanceRangeSerializer)
    def get_distance_range(self, obj: Run) -> dict:
        return obj.readings.aggregate(
            from_m=Min("distance_m"), to_m=Max("distance_m")
        )


class ReadingsResponseSerializer(serializers.Serializer):
    run = RunSerializer()
    filter = DistanceRangeSerializer()
    count = serializers.IntegerField()
    readings = ReadingSerializer(many=True)


class SummaryResponseSerializer(serializers.Serializer):
    run = RunSerializer()
    filter = DistanceRangeSerializer()
    count = serializers.IntegerField()
    anomaly_count = serializers.IntegerField()
    pressure_min = serializers.FloatField(allow_null=True)
    pressure_max = serializers.FloatField(allow_null=True)
    pressure_mean = serializers.FloatField(allow_null=True)


class UploadResponseSerializer(serializers.Serializer):
    run = RunSerializer()


class IndexSerializer(serializers.Serializer):
    endpoints = serializers.DictField(child=serializers.CharField())


class UploadSerializer(serializers.Serializer):
    """Accepts the uploaded CSV and creates the current run."""

    file = serializers.FileField()

    def to_internal_value(self, data):
        if not data or not data.get("file"):
            raise InvalidReadingsFile(
                "No file was uploaded. Send the CSV as multipart/form-data "
                "under the field name 'file'."
            )
        return super().to_internal_value(data)

    def validate_file(self, uploaded):
        try:
            self._parsed = parse_readings(uploaded.read())
        except CsvValidationError as exc:
            raise InvalidReadingsFile(str(exc)) from exc
        except OSError as exc:
            raise InvalidReadingsFile(
                "The uploaded file could not be read. Please try again."
            ) from exc
        return uploaded

    def create(self, validated_data) -> Run:
        uploaded = validated_data["file"]
        return Run.objects.replace(uploaded.name or "upload.csv", self._parsed)

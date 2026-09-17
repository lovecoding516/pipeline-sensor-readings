from django import forms
from django_filters import rest_framework as filters

from .models import Reading


class FloatFilter(filters.Filter):
    field_class = forms.FloatField


class ReadingFilter(filters.FilterSet):
    """Inclusive distance window: `?from_m=` and `?to_m=`, independently."""

    from_m = FloatFilter(
        field_name="distance_m",
        method="filter_from_m",
        error_messages={"invalid": "must be a number."},
    )
    to_m = FloatFilter(
        field_name="distance_m",
        method="filter_to_m",
        error_messages={"invalid": "must be a number."},
    )

    class Meta:
        model = Reading
        fields = ["from_m", "to_m"]

    def filter_from_m(self, queryset, _name, value):
        return queryset.in_distance_range(from_m=value)

    def filter_to_m(self, queryset, _name, value):
        return queryset.in_distance_range(to_m=value)

    def applied_range(self) -> dict[str, float | None]:
        cleaned = self.form.cleaned_data
        return {
            "from_m": cleaned.get("from_m"),
            "to_m": cleaned.get("to_m"),
        }

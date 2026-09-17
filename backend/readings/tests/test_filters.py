from django.test import TestCase

from readings.csv_import import ParsedReading
from readings.filters import ReadingFilter
from readings.models import Run


def parsed(*pairs: tuple[int, float]) -> list[ParsedReading]:
    return [
        ParsedReading(distance_m=distance, pressure_bar=pressure, temperature_c=18.0)
        for distance, pressure in pairs
    ]


class ReadingFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.loaded = Run.objects.replace(
            "range.csv",
            parsed((0, 40.0), (5, 41.0), (10, 42.0), (15, 43.0)),
        )

    def filterset(self, **params) -> ReadingFilter:
        return ReadingFilter(params, queryset=self.loaded.readings.all())

    def test_window_is_inclusive(self):
        distances = [row.distance_m for row in self.filterset(from_m="5", to_m="10").qs]
        self.assertEqual(distances, [5, 10])

    def test_single_bound(self):
        self.assertEqual(self.filterset(from_m="10").qs.count(), 2)
        self.assertEqual(self.filterset(to_m="5").qs.count(), 2)

    def test_blank_bounds_are_ignored(self):
        self.assertEqual(self.filterset(from_m="", to_m="").qs.count(), 4)

    def test_non_numeric_bound_is_invalid(self):
        filterset = self.filterset(from_m="abc")
        self.assertFalse(filterset.is_valid())
        self.assertIn("must be a number", filterset.errors["from_m"][0])

    def test_applied_range(self):
        filterset = self.filterset(from_m="50", to_m="100")
        self.assertTrue(filterset.is_valid())
        self.assertEqual(
            filterset.applied_range(), {"from_m": 50.0, "to_m": 100.0}
        )

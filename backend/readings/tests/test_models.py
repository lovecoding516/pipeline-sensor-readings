from django.test import TestCase

from readings.csv_import import ParsedReading
from readings.models import Reading, Run


def parsed(*pairs: tuple[int, float]) -> list[ParsedReading]:
    return [
        ParsedReading(distance_m=distance, pressure_bar=pressure, temperature_c=18.0)
        for distance, pressure in pairs
    ]


def calm_then_spike() -> list[ParsedReading]:
    """Twenty quiet readings followed by a spike that must be flagged."""
    return parsed(*[(i * 5, 40.0 + (i % 2) * 0.1) for i in range(20)], (100, 55.0))


class RunManagerTests(TestCase):
    def test_current_is_none_when_nothing_loaded(self):
        self.assertIsNone(Run.objects.current())

    def test_replace_discards_the_previous_run(self):
        Run.objects.replace("first.csv", parsed((0, 40.0), (5, 40.1)))
        Run.objects.replace("second.csv", parsed((0, 41.0)))

        self.assertEqual(Run.objects.count(), 1)
        self.assertEqual(Reading.objects.count(), 1)
        self.assertEqual(Run.objects.current().filename, "second.csv")

    def test_replace_stores_anomaly_verdicts(self):
        loaded = Run.objects.replace("spike.csv", calm_then_spike())

        spike = loaded.readings.get(distance_m=100)
        self.assertTrue(spike.anomaly)
        self.assertAlmostEqual(spike.baseline_mean, 40.05, places=2)
        self.assertGreater(spike.baseline_std, 0)

    def test_replace_leaves_no_baseline_on_the_first_readings(self):
        loaded = Run.objects.replace("short.csv", parsed((0, 40.0), (5, 40.1), (10, 40.2)))

        first = loaded.readings.get(distance_m=0)
        self.assertIsNone(first.baseline_mean)
        self.assertIsNone(first.baseline_std)
        self.assertFalse(first.anomaly)

    def test_is_sample_flag(self):
        self.assertTrue(
            Run.objects.replace("s.csv", parsed((0, 40.0)), is_sample=True).is_sample
        )
        self.assertFalse(Run.objects.replace("u.csv", parsed((0, 40.0))).is_sample)


class ReadingQuerySetTests(TestCase):
    # Not `cls.run`: that would shadow TestCase.run() and break the runner.
    @classmethod
    def setUpTestData(cls):
        cls.loaded = Run.objects.replace(
            "run.csv", parsed((0, 40.0), (5, 41.0), (10, 42.0), (15, 43.0))
        )

    def test_in_distance_range_is_inclusive(self):
        readings = self.loaded.readings.in_distance_range(5, 10)
        self.assertEqual([r.distance_m for r in readings], [5, 10])

    def test_in_distance_range_without_bounds_returns_everything(self):
        self.assertEqual(self.loaded.readings.in_distance_range().count(), 4)

    def test_in_distance_range_accepts_a_single_bound(self):
        self.assertEqual(self.loaded.readings.in_distance_range(from_m=10).count(), 2)
        self.assertEqual(self.loaded.readings.in_distance_range(to_m=5).count(), 2)

    def test_inverted_range_is_empty(self):
        self.assertEqual(self.loaded.readings.in_distance_range(15, 0).count(), 0)

    def test_pressure_stats(self):
        stats = self.loaded.readings.pressure_stats()

        self.assertEqual(stats["count"], 4)
        # The 1 bar/reading ramp trips the rule once, at the third reading: a
        # two-sample window gives sigma=0.71, so 2 sigma is only 1.41 bar wide.
        self.assertEqual(stats["anomaly_count"], 1)
        self.assertAlmostEqual(stats["pressure_min"], 40.0)
        self.assertAlmostEqual(stats["pressure_max"], 43.0)
        self.assertAlmostEqual(stats["pressure_mean"], 41.5)

    def test_pressure_stats_on_an_empty_range_reports_nulls(self):
        stats = self.loaded.readings.in_distance_range(from_m=9000).pressure_stats()

        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["anomaly_count"], 0)
        self.assertIsNone(stats["pressure_min"])
        self.assertIsNone(stats["pressure_max"])
        self.assertIsNone(stats["pressure_mean"])

    def test_pressure_stats_rounds_the_mean(self):
        loaded = Run.objects.replace("thirds.csv", parsed((0, 1.0), (5, 1.0), (10, 2.0)))
        self.assertEqual(loaded.readings.pressure_stats()["pressure_mean"], 1.3333)

    def test_anomalous_narrows_to_flagged_readings(self):
        loaded = Run.objects.replace("spike.csv", calm_then_spike())
        self.assertEqual([r.distance_m for r in loaded.readings.anomalous()], [100])

    def test_readings_are_ordered_by_distance(self):
        loaded = Run.objects.replace("any.csv", parsed((10, 42.0), (0, 40.0), (5, 41.0)))
        self.assertEqual([r.distance_m for r in loaded.readings.all()], [0, 5, 10])

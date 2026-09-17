from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from readings.csv_import import parse_readings
from readings.models import Reading, Run
from readings.sample import load_sample_fixture_if_empty

HEADER = "distance_m,pressure_bar,temperature_c"


def upload_file(*lines: str, name: str = "run.csv", header: str = HEADER) -> SimpleUploadedFile:
    body = "\n".join([header, *lines]).encode("utf-8")
    return SimpleUploadedFile(name, body, content_type="text/csv")


def calm_lines(count: int = 30, start: int = 0) -> list[str]:
    """A run with no anomalies: pressure alternates between two nearby values.

    A strict alternation holds every deviation at exactly half the band while
    sigma stays near half the band too, so nothing crosses 2 sigma - not even
    in the very short windows at the start of a run, where the band is
    tightest. `test_fixture_has_no_anomalies` guards that property.
    """
    return [f"{start + i * 5},{40.0 + (i % 2) * 0.1:.2f},18.0" for i in range(count)]


class NoRunLoadedTests(TestCase):
    def test_readings_reports_no_run(self):
        response = self.client.get("/readings")
        self.assertEqual(response.status_code, 404)
        self.assertIn("No run is loaded", response.json()["detail"])

    def test_summary_reports_no_run(self):
        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_index_lists_endpoints(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("GET /readings", response.json()["endpoints"])
        self.assertIn("GET /docs", response.json()["endpoints"])


class UploadTests(TestCase):
    def test_upload_creates_run(self):
        response = self.client.post("/upload", {"file": upload_file(*calm_lines())})

        self.assertEqual(response.status_code, 201)
        run = response.json()["run"]
        self.assertEqual(run["filename"], "run.csv")
        self.assertEqual(run["reading_count"], 30)
        self.assertFalse(run["is_sample"])
        self.assertEqual(Run.objects.count(), 1)

    def test_upload_replaces_previous_run(self):
        self.client.post("/upload", {"file": upload_file(*calm_lines(), name="first.csv")})
        self.client.post(
            "/upload", {"file": upload_file(*calm_lines(10), name="second.csv")}
        )

        self.assertEqual(Run.objects.count(), 1)
        self.assertEqual(Reading.objects.count(), 10)
        self.assertEqual(Run.objects.current().filename, "second.csv")

    def test_rejected_upload_keeps_existing_run(self):
        """A bad file must not destroy the run the engineer was looking at."""
        self.client.post("/upload", {"file": upload_file(*calm_lines(), name="good.csv")})

        response = self.client.post("/upload", {"file": upload_file("0,oops,18.0")})

        self.assertEqual(response.status_code, 400)
        self.assertIn("non-numeric", response.json()["detail"])
        self.assertEqual(Run.objects.current().filename, "good.csv")
        self.assertEqual(Reading.objects.count(), 30)

    def test_upload_without_file_is_rejected(self):
        response = self.client.post("/upload", {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file was uploaded", response.json()["detail"])

    def test_upload_rejects_malformed_file_with_message(self):
        response = self.client.post(
            "/upload", {"file": upload_file("0,40.0", header="distance_m,pressure_bar")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("temperature_c", response.json()["detail"])

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/upload").status_code, 405)


class ReadingsFilterTests(TestCase):
    def setUp(self):
        self.client.post("/upload", {"file": upload_file(*calm_lines(40))})  # 0..195 m

    def test_returns_all_readings_unfiltered(self):
        body = self.client.get("/readings").json()
        self.assertEqual(body["count"], 40)
        self.assertEqual(len(body["readings"]), 40)
        self.assertIsNone(body["filter"]["from_m"])

    def test_filter_bounds_are_inclusive(self):
        body = self.client.get("/readings?from_m=50&to_m=100").json()
        self.assertEqual(
            [r["distance_m"] for r in body["readings"]], [50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
        )
        self.assertEqual(body["filter"], {"from_m": 50.0, "to_m": 100.0})

    def test_single_bound(self):
        self.assertEqual(self.client.get("/readings?from_m=180").json()["count"], 4)
        self.assertEqual(self.client.get("/readings?to_m=10").json()["count"], 3)

    def test_out_of_range_filter_is_empty_not_an_error(self):
        body = self.client.get("/readings?from_m=9000&to_m=9500").json()
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["readings"], [])

    def test_inverted_range_is_empty_not_an_error(self):
        self.assertEqual(self.client.get("/readings?from_m=100&to_m=50").json()["count"], 0)

    def test_blank_parameters_are_ignored(self):
        self.assertEqual(self.client.get("/readings?from_m=&to_m=").json()["count"], 40)

    def test_non_numeric_parameter_is_rejected(self):
        for url in ("/readings?from_m=abc", "/summary?to_m=xyz"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 400)
                self.assertIn("must be a number", response.json()["detail"])

    def test_readings_are_ordered_by_distance(self):
        distances = [r["distance_m"] for r in self.client.get("/readings").json()["readings"]]
        self.assertEqual(distances, sorted(distances))


class AnomalyIndependenceTests(TestCase):
    """Flags describe the reading, so a distance filter must not change them."""

    def setUp(self):
        # A calm stretch, then a sharp spike at 100 m.
        lines = calm_lines(20) + ["100,55.0,18.0"] + calm_lines(5, start=105)
        self.client.post("/upload", {"file": upload_file(*lines)})

    def test_spike_is_flagged(self):
        flagged = [
            r["distance_m"]
            for r in self.client.get("/readings").json()["readings"]
            if r["anomaly"]
        ]
        self.assertIn(100, flagged)

    def test_flag_survives_a_filter_that_hides_the_baseline(self):
        """Filtering to just the spike must not recompute it as normal."""
        body = self.client.get("/readings?from_m=100&to_m=100").json()
        self.assertEqual(body["count"], 1)
        self.assertTrue(body["readings"][0]["anomaly"])

    def test_baseline_is_reported(self):
        spike = next(
            r
            for r in self.client.get("/readings").json()["readings"]
            if r["distance_m"] == 100
        )
        self.assertAlmostEqual(spike["baseline_mean"], 40.05, places=2)
        self.assertGreater(spike["baseline_std"], 0)


class SummaryTests(TestCase):
    def setUp(self):
        lines = calm_lines(20) + ["100,55.0,18.0"]
        self.client.post("/upload", {"file": upload_file(*lines)})

    def test_summary_of_full_run(self):
        body = self.client.get("/summary").json()
        self.assertEqual(body["count"], 21)
        self.assertEqual(body["anomaly_count"], 1)
        self.assertAlmostEqual(body["pressure_max"], 55.0)
        self.assertAlmostEqual(body["pressure_min"], 40.0)
        self.assertIsNotNone(body["pressure_mean"])

    def test_summary_follows_the_filter(self):
        body = self.client.get("/summary?from_m=0&to_m=50").json()
        self.assertEqual(body["count"], 11)
        self.assertEqual(body["anomaly_count"], 0)
        self.assertAlmostEqual(body["pressure_max"], 40.1)

    def test_empty_range_returns_nulls_not_zeros(self):
        body = self.client.get("/summary?from_m=9000").json()
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["anomaly_count"], 0)
        self.assertIsNone(body["pressure_min"])
        self.assertIsNone(body["pressure_max"])
        self.assertIsNone(body["pressure_mean"])

    def test_fixture_has_no_anomalies(self):
        """Guards the helper: the calm baseline must contribute no flags itself."""
        self.client.post("/upload", {"file": upload_file(*calm_lines(40))})
        self.assertEqual(self.client.get("/summary").json()["anomaly_count"], 0)

    def test_summary_reports_the_rule_parameters(self):
        rule = self.client.get("/summary").json()["run"]["anomaly_rule"]
        self.assertEqual(rule, {"window_size": 20, "threshold_sigmas": 2.0})

    def test_run_reports_its_full_distance_extent(self):
        """The extent must describe the run, not the filtered slice."""
        body = self.client.get("/summary?from_m=50&to_m=60").json()
        self.assertEqual(body["run"]["distance_range"], {"from_m": 0, "to_m": 100})


@override_settings(LOAD_SAMPLE_FIXTURE=True)
class SampleSeedingTests(TestCase):
    def test_loads_the_sample_when_empty(self):
        self.assertTrue(load_sample_fixture_if_empty())
        body = self.client.get("/readings").json()
        self.assertEqual(body["run"]["filename"], "sensor_readings.csv")
        self.assertTrue(body["run"]["is_sample"])
        self.assertEqual(body["count"], 400)

    def test_does_not_overwrite_an_uploaded_run(self):
        Run.objects.replace("mine.csv", parse_readings(b"\n".join(
            [HEADER.encode()] + [line.encode() for line in calm_lines(5)]
        )))
        self.assertFalse(load_sample_fixture_if_empty())
        self.assertEqual(self.client.get("/readings").json()["run"]["filename"], "mine.csv")

    def test_production_does_not_load_the_fixture(self):
        with override_settings(LOAD_SAMPLE_FIXTURE=False):
            self.assertFalse(load_sample_fixture_if_empty())
        self.assertEqual(Run.objects.count(), 0)


class SampleDataTests(TestCase):
    """Regression tests against the bundled sample run.

    These pin down what the assignment's rule actually does on the provided
    data, including where it under-reports: see the README for the discussion.
    """

    fixtures = ["sample_run"]

    def test_sample_shape(self):
        body = self.client.get("/summary").json()
        self.assertEqual(body["count"], 400)
        self.assertEqual(body["anomaly_count"], 39)

    def test_leak_like_drop_is_fully_flagged(self):
        """Pressure drops ~4.5 bar over 480-500 m and every reading is caught."""
        body = self.client.get("/readings?from_m=480&to_m=500").json()
        self.assertEqual(body["count"], 5)
        self.assertTrue(all(r["anomaly"] for r in body["readings"]))

    def test_sustained_jump_is_only_flagged_at_its_onset(self):
        """The trailing window absorbs the 1200 m jump, masking its tail.

        Readings from 1225 m on are still ~5 bar above the pre-jump level but
        are no longer outliers relative to the (now inflated) local baseline.
        """
        flagged = {
            r["distance_m"]: r["anomaly"]
            for r in self.client.get("/readings?from_m=1200&to_m=1240").json()["readings"]
        }
        self.assertTrue(flagged[1200])
        self.assertTrue(flagged[1220])
        self.assertFalse(flagged[1225])
        self.assertFalse(flagged[1240])


class SchemaTests(TestCase):
    def test_openapi_schema_lists_the_endpoints(self):
        response = self.client.get("/schema/")
        self.assertEqual(response.status_code, 200)
        schema = response.content.decode()
        self.assertIn("openapi", schema)
        self.assertIn("/readings", schema)
        self.assertIn("/upload", schema)
        self.assertIn("/summary", schema)

    def test_swagger_ui_is_served(self):
        self.assertEqual(self.client.get("/docs/").status_code, 200)

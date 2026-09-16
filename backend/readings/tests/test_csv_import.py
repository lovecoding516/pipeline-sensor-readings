from django.test import SimpleTestCase

from readings.csv_import import (
    MAX_UPLOAD_BYTES,
    CsvValidationError,
    parse_readings,
)

HEADER = "distance_m,pressure_bar,temperature_c"


def csv_bytes(*lines: str, header: str = HEADER) -> bytes:
    return ("\n".join([header, *lines])).encode("utf-8")


class ParseReadingsTests(SimpleTestCase):
    def test_parses_valid_file(self):
        readings = parse_readings(csv_bytes("0,41.95,17.9", "5,42.01,18.3"))

        self.assertEqual(len(readings), 2)
        self.assertEqual(readings[0].distance_m, 0)
        self.assertAlmostEqual(readings[0].pressure_bar, 41.95)
        self.assertAlmostEqual(readings[1].temperature_c, 18.3)

    def test_sorts_by_distance(self):
        readings = parse_readings(csv_bytes("10,40.2,18.2", "0,40.0,18.0", "5,40.1,18.1"))
        self.assertEqual([r.distance_m for r in readings], [0, 5, 10])

    def test_ignores_unknown_columns(self):
        readings = parse_readings(
            csv_bytes("0,40.0,18.0,12.5", header=HEADER + ",flow_rate")
        )
        self.assertEqual(len(readings), 1)

    def test_accepts_bom_and_crlf(self):
        raw = b"\xef\xbb\xbf" + csv_bytes("0,40.0,18.0").replace(b"\n", b"\r\n")
        self.assertEqual(len(parse_readings(raw)), 1)

    def test_accepts_integral_float_distance(self):
        self.assertEqual(parse_readings(csv_bytes("10.0,40.0,18.0"))[0].distance_m, 10)

    def test_skips_blank_lines(self):
        readings = parse_readings(csv_bytes("0,40.0,18.0", "", "5,40.1,18.1"))
        self.assertEqual(len(readings), 2)

    def test_negative_pressure_is_allowed(self):
        """Physically odd but numerically valid; validation should not editorialise."""
        self.assertAlmostEqual(
            parse_readings(csv_bytes("0,-1.5,18.0"))[0].pressure_bar, -1.5
        )

    def _assert_rejects(self, raw: bytes, *expected_fragments: str):
        with self.assertRaises(CsvValidationError) as ctx:
            parse_readings(raw)
        message = str(ctx.exception)
        for fragment in expected_fragments:
            self.assertIn(fragment, message)
        return message

    def test_rejects_empty_file(self):
        self._assert_rejects(b"", "empty")
        self._assert_rejects(b"   \n  \n", "empty")

    def test_rejects_header_only(self):
        self._assert_rejects(csv_bytes(), "no data rows")

    def test_rejects_missing_column(self):
        self._assert_rejects(
            csv_bytes("0,40.0", header="distance_m,pressure_bar"),
            "Missing required column",
            "temperature_c",
        )

    def test_rejects_non_numeric_value(self):
        self._assert_rejects(
            csv_bytes("0,40.0,18.0", "5,abc,18.1"), "Line 3", "pressure_bar", "abc"
        )

    def test_rejects_empty_cell(self):
        self._assert_rejects(csv_bytes("0,40.0,18.0", "5,,18.1"), "Line 3", "is empty")

    def test_rejects_short_row(self):
        self._assert_rejects(csv_bytes("0,40.0,18.0", "5,40.1"), "fewer columns")

    def test_rejects_non_finite_values(self):
        self._assert_rejects(csv_bytes("0,NaN,18.0"), "finite")
        self._assert_rejects(csv_bytes("0,inf,18.0"), "finite")

    def test_rejects_fractional_distance(self):
        self._assert_rejects(csv_bytes("2.5,40.0,18.0"), "whole number")

    def test_rejects_duplicate_distance(self):
        self._assert_rejects(
            csv_bytes("0,40.0,18.0", "0,41.0,18.1"), "already appears", "unique"
        )

    def test_rejects_non_utf8_binary(self):
        self._assert_rejects(b"\x89PNG\r\n\x1a\n\xff\xfe\xfd", "UTF-8")

    def test_rejects_oversized_file(self):
        self._assert_rejects(b"x" * (MAX_UPLOAD_BYTES + 1), "too large")

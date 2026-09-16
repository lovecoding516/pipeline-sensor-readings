"""Parsing and validation of an uploaded readings CSV.

Every rejection path raises `CsvValidationError` carrying a message meant to be
shown to the engineer who picked the wrong file, so the API can turn it into a
400 instead of a traceback.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass

REQUIRED_COLUMNS = ("distance_m", "pressure_bar", "temperature_c")

# A 2 km run is ~400 rows; this is a generous ceiling that still refuses a file
# picked by accident, before we try to hold it in memory.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ROWS = 200_000


class CsvValidationError(Exception):
    """An uploaded file could not be read as a readings CSV."""


@dataclass(frozen=True)
class ParsedReading:
    distance_m: int
    pressure_bar: float
    temperature_c: float


def _decode(raw: bytes) -> str:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise CsvValidationError(
            f"File is too large ({len(raw) / 1_048_576:.1f} MB). "
            f"The limit is {MAX_UPLOAD_BYTES // 1_048_576} MB."
        )
    try:
        # utf-8-sig transparently strips the BOM that Excel exports add.
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CsvValidationError(
            "File is not valid UTF-8 text. Expected a plain CSV file, "
            "not a spreadsheet or binary file."
        ) from None


def _parse_number(value: str, column: str, line_number: int) -> float:
    if value is None or value.strip() == "":
        raise CsvValidationError(
            f"Line {line_number}: column '{column}' is empty."
        )
    try:
        number = float(value.strip())
    except ValueError:
        raise CsvValidationError(
            f"Line {line_number}: column '{column}' has the non-numeric "
            f"value '{value.strip()}'."
        ) from None
    if not math.isfinite(number):
        raise CsvValidationError(
            f"Line {line_number}: column '{column}' must be a finite number, "
            f"got '{value.strip()}'."
        )
    return number


def parse_readings(raw: bytes) -> list[ParsedReading]:
    """Turn raw upload bytes into readings sorted by distance.

    Unknown extra columns are ignored so that richer robot exports still load.
    """
    text = _decode(raw)
    if not text.strip():
        raise CsvValidationError("File is empty.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CsvValidationError("File is empty.")

    header = [(name or "").strip() for name in reader.fieldnames]
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise CsvValidationError(
            "Missing required column(s): {}. Expected a CSV with the header {}.".format(
                ", ".join(missing), ", ".join(REQUIRED_COLUMNS)
            )
        )
    reader.fieldnames = header

    readings: list[ParsedReading] = []
    seen_distances: dict[int, int] = {}

    for row in reader:
        # csv gives line 1 to the header, so data rows start at line 2.
        line_number = reader.line_num

        if any(value is None for value in (row.get(c) for c in REQUIRED_COLUMNS)):
            raise CsvValidationError(
                f"Line {line_number}: row has fewer columns than the header."
            )
        if all((row.get(c) or "").strip() == "" for c in REQUIRED_COLUMNS):
            continue  # tolerate blank separator lines

        if len(readings) >= MAX_ROWS:
            raise CsvValidationError(
                f"File has more than {MAX_ROWS:,} rows, which exceeds what this "
                "viewer is designed for."
            )

        distance = _parse_number(row["distance_m"], "distance_m", line_number)
        if not float(distance).is_integer():
            raise CsvValidationError(
                f"Line {line_number}: column 'distance_m' must be a whole "
                f"number of metres, got '{row['distance_m'].strip()}'."
            )
        distance = int(distance)
        if distance in seen_distances:
            raise CsvValidationError(
                f"Line {line_number}: distance {distance} m already appears on "
                f"line {seen_distances[distance]}. Each position must be unique."
            )
        seen_distances[distance] = line_number

        readings.append(
            ParsedReading(
                distance_m=distance,
                pressure_bar=_parse_number(row["pressure_bar"], "pressure_bar", line_number),
                temperature_c=_parse_number(row["temperature_c"], "temperature_c", line_number),
            )
        )

    if not readings:
        raise CsvValidationError("File contains a header but no data rows.")

    # The anomaly rule walks the pipeline in order, so normalise the ordering
    # instead of trusting the robot to have written the rows sorted.
    readings.sort(key=lambda reading: reading.distance_m)
    return readings

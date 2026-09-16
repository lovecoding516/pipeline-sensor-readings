"""Trailing-window anomaly detection for pipeline pressure readings.

A reading is anomalous when its pressure deviates from the local trend by more
than `threshold` standard deviations:

    anomaly(i)  <=>  |p(i) - mu(i)| > threshold * sigma(i)

where mu(i) and sigma(i) are the mean and standard deviation of the pressure
over the `window_size` readings *preceding* i. The window is shorter near the
start of the run, as the assignment specifies.

Implemented with the standard library only: 400 readings per run do not justify
a numpy/pandas dependency, and the loop maps one-to-one onto the formula above.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, stdev
from typing import Sequence

WINDOW_SIZE = 20
THRESHOLD_SIGMAS = 2.0

# stdev() is the Bessel-corrected sample standard deviation and needs at least
# two data points, so the first two readings of a run get no verdict.
MIN_WINDOW = 2


@dataclass(frozen=True)
class Verdict:
    """Outcome for a single reading, including the baseline it was judged against."""

    anomaly: bool
    baseline_mean: float | None
    baseline_std: float | None


def evaluate(
    pressures: Sequence[float],
    window_size: int = WINDOW_SIZE,
    threshold: float = THRESHOLD_SIGMAS,
) -> list[Verdict]:
    """Classify every pressure in `pressures`, which must be ordered by distance.

    Readings whose preceding window is too short to estimate a standard
    deviation are reported as non-anomalous with a null baseline, rather than
    being guessed at or raising.
    """
    if window_size < MIN_WINDOW:
        raise ValueError(f"window_size must be at least {MIN_WINDOW}")
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    verdicts: list[Verdict] = []
    for i, pressure in enumerate(pressures):
        window = pressures[max(0, i - window_size):i]
        if len(window) < MIN_WINDOW:
            verdicts.append(Verdict(False, None, None))
            continue

        mean = fmean(window)
        std = stdev(window)
        # With a zero-variance window the comparison degenerates to p != mean.
        # That is the literal reading of the rule and cannot divide by zero.
        verdicts.append(
            Verdict(abs(pressure - mean) > threshold * std, mean, std)
        )
    return verdicts

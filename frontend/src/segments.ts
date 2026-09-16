import type { Reading } from './api'

export type SegmentDirection = 'drop' | 'jump' | 'mixed'

export interface AnomalySegment {
  fromM: number
  toM: number
  readingCount: number
  direction: SegmentDirection
  peak: Reading
  peakSigmas: number | null
}

export function deviationInSigmas(reading: Reading): number | null {
  const { baseline_mean: mean, baseline_std: std } = reading
  if (mean === null || std === null || std === 0) {
    return null
  }
  return (reading.pressure_bar - mean) / std
}

function signedDeviation(reading: Reading): number {
  if (reading.baseline_mean === null) return 0
  return reading.pressure_bar - reading.baseline_mean
}

function directionOf(readings: Reading[]): SegmentDirection {
  const deviations = readings.map(signedDeviation)
  if (deviations.every((value) => value > 0)) return 'jump'
  if (deviations.every((value) => value < 0)) return 'drop'
  return 'mixed'
}

function toSegment(members: Reading[]): AnomalySegment {
  const peak = members.reduce((worst, reading) =>
    Math.abs(signedDeviation(reading)) > Math.abs(signedDeviation(worst))
      ? reading
      : worst,
  )
  return {
    fromM: members[0].distance_m,
    toM: members[members.length - 1].distance_m,
    readingCount: members.length,
    direction: directionOf(members),
    peak,
    peakSigmas: deviationInSigmas(peak),
  }
}

/** `readings` must be ordered by distance: adjacency is positional. */
export function groupAnomalySegments(readings: Reading[]): AnomalySegment[] {
  const segments: AnomalySegment[] = []
  let current: Reading[] = []

  for (const reading of readings) {
    if (reading.anomaly) {
      current.push(reading)
      continue
    }
    if (current.length > 0) {
      segments.push(toSegment(current))
      current = []
    }
  }
  if (current.length > 0) {
    segments.push(toSegment(current))
  }
  return segments
}

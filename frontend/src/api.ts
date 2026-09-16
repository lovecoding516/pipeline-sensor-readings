import axios, { type AxiosInstance } from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000').replace(
  /\/+$/,
  '',
)

export interface Reading {
  distance_m: number
  pressure_bar: number
  temperature_c: number
  anomaly: boolean
  baseline_mean: number | null
  baseline_std: number | null
}

export interface AnomalyRule {
  window_size: number
  threshold_sigmas: number
}

export interface DistanceRange {
  from_m: number | null
  to_m: number | null
}

export interface RunInfo {
  filename: string
  uploaded_at: string
  is_sample: boolean
  reading_count: number
  distance_range: DistanceRange
  anomaly_rule: AnomalyRule
}

export interface ReadingsResponse {
  run: RunInfo
  filter: DistanceRange
  count: number
  readings: Reading[]
}

export interface SummaryResponse {
  run: RunInfo
  filter: DistanceRange
  count: number
  anomaly_count: number
  pressure_min: number | null
  pressure_max: number | null
  pressure_mean: number | null
}

export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the server. */
  readonly status: number

  constructor(message: string, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }

  get isNoRunLoaded(): boolean {
    return this.status === 404
  }
}

function detailFrom(data: unknown): string | null {
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch {
      return null
    }
  }
  if (data && typeof data === 'object' && 'detail' in data) {
    const { detail } = data as { detail: unknown }
    if (typeof detail === 'string') return detail
  }
  return null
}

function toApiError(error: unknown): ApiError {
  if (!axios.isAxiosError(error)) {
    return new ApiError('Something went wrong while talking to the API.')
  }

  const { response } = error
  if (!response) {
    return new ApiError(
      `Cannot reach the API at ${API_BASE}. Is the Django server running?`,
    )
  }

  return new ApiError(
    detailFrom(response.data) ??
      `Request failed with status ${response.status} ${response.statusText}.`,
    response.status,
  )
}

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  // Long enough for a 10 MB upload, short enough that a dead server is not an
  // endless spinner.
  timeout: 30_000,
})

client.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(toApiError(error)),
)

function rangeParams(range: DistanceRange): Record<string, number> {
  const params: Record<string, number> = {}
  if (range.from_m !== null) params.from_m = range.from_m
  if (range.to_m !== null) params.to_m = range.to_m
  return params
}

export async function fetchReadings(range: DistanceRange): Promise<ReadingsResponse> {
  const { data } = await client.get<ReadingsResponse>('/readings', {
    params: rangeParams(range),
  })
  return data
}

export async function fetchSummary(range: DistanceRange): Promise<SummaryResponse> {
  const { data } = await client.get<SummaryResponse>('/summary', {
    params: rangeParams(range),
  })
  return data
}

export async function uploadReadings(file: File): Promise<{ run: RunInfo }> {
  const body = new FormData()
  body.append('file', file)
  // axios sets the multipart boundary itself; setting Content-Type by hand breaks it.
  const { data } = await client.post<{ run: RunInfo }>('/upload', body)
  return data
}

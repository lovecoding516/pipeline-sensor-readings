import { computed, ref } from 'vue'

import {
  ApiError,
  fetchReadings,
  fetchSummary,
  uploadReadings,
  type DistanceRange,
  type Reading,
  type RunInfo,
  type SummaryResponse,
} from '../api'
import { groupAnomalySegments } from '../segments'

const WHOLE_RUN: DistanceRange = { from_m: null, to_m: null }

export function useRun() {
  const run = ref<RunInfo | null>(null)
  const readings = ref<Reading[]>([])
  const summary = ref<SummaryResponse | null>(null)
  const appliedRange = ref<DistanceRange>({ ...WHOLE_RUN })

  const loading = ref(false)
  const uploading = ref(false)
  const errorMessage = ref<string | null>(null)
  const noRunLoaded = ref(false)

  const busy = computed(() => loading.value || uploading.value)
  const segments = computed(() => groupAnomalySegments(readings.value))
  const extent = computed<DistanceRange>(() => run.value?.distance_range ?? WHOLE_RUN)

  function forget() {
    run.value = null
    readings.value = []
    summary.value = null
  }

  async function load(range: DistanceRange = WHOLE_RUN) {
    loading.value = true
    errorMessage.value = null
    try {
      const [readingsResponse, summaryResponse] = await Promise.all([
        fetchReadings(range),
        fetchSummary(range),
      ])
      run.value = readingsResponse.run
      readings.value = readingsResponse.readings
      summary.value = summaryResponse
      // The server's echo of the filter, not what we asked for.
      appliedRange.value = readingsResponse.filter
      noRunLoaded.value = false
    } catch (error) {
      if (error instanceof ApiError && error.isNoRunLoaded) {
        noRunLoaded.value = true
        forget()
      } else {
        errorMessage.value =
          error instanceof ApiError ? error.message : 'Could not load the run.'
      }
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    uploading.value = true
    errorMessage.value = null
    try {
      await uploadReadings(file)
      await load()
    } catch (error) {
      errorMessage.value =
        error instanceof ApiError ? error.message : 'The upload failed.'
    } finally {
      uploading.value = false
    }
  }

  return {
    run,
    readings,
    summary,
    appliedRange,
    extent,
    segments,
    busy,
    errorMessage,
    noRunLoaded,
    load,
    upload,
  }
}

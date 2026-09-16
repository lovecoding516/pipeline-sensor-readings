<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AnomalySegments from './components/AnomalySegments.vue'
import DistanceFilter from './components/DistanceFilter.vue'
import PressureChart from './components/PressureChart.vue'
import ReadingsTable from './components/ReadingsTable.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import UploadControl from './components/UploadControl.vue'
import {
  Alert,
  Badge,
  Button,
  Card,
  Modal,
  Switch,
  Tabs,
  type TabDefinition,
} from './components/ui'
import { useRun } from './composables/useRun'

const TABS: TabDefinition[] = [
  { key: 'segments', label: 'Anomalous segments' },
  { key: 'readings', label: 'All readings' },
]

const {
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
} = useRun()

const showBaseline = ref(false)
const explainerOpen = ref(false)

const uploadedAt = computed(() =>
  run.value ? new Date(run.value.uploaded_at).toLocaleString() : '',
)

onMounted(() => load())
</script>

<template>
  <div class="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-8 pb-16">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">Pipeline Readings Viewer</h1>
        <p class="mt-1 max-w-prose text-sm text-slate-500">
          Pressure along one inspection run, with readings that deviate from the local
          trend flagged for review.
        </p>
      </div>
      <Button v-if="run" variant="secondary" size="sm" @click="explainerOpen = true">
        How detection works
      </Button>
    </header>

    <Card>
      <div class="flex flex-wrap items-end justify-between gap-4">
        <UploadControl :busy="busy" @select="upload" />
        <DistanceFilter
          v-if="run"
          :busy="busy"
          :applied="appliedRange"
          :extent="extent"
          @apply="load"
        />
      </div>
    </Card>

    <Alert v-if="errorMessage" tone="error">{{ errorMessage }}</Alert>

    <Card v-if="noRunLoaded">
      <div class="flex flex-col items-center gap-3 py-8 text-center">
        <h2 class="text-base font-semibold text-slate-900">No run loaded</h2>
        <p class="max-w-md text-sm text-slate-500">
          Upload a readings CSV to see the pressure profile and the segments that deviate
          from it. Any file with these three columns works; extra columns are ignored and
          rows may be in any order.
        </p>
        <pre
          class="rounded-md bg-slate-50 px-4 py-3 text-left text-xs text-slate-600 ring-1 ring-slate-200"
        >
distance_m,pressure_bar,temperature_c
0,52.1,18.2
5,52.0,18.2</pre>
      </div>
    </Card>

    <template v-if="run">
      <p class="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-slate-500">
        <strong class="text-slate-700">{{ run.filename }}</strong>
        <Badge v-if="run.is_sample" tone="indigo">sample</Badge>
        <span>· {{ run.reading_count }} readings</span>
        <span>· {{ extent.from_m }}–{{ extent.to_m }} m</span>
        <span>· loaded {{ uploadedAt }}</span>
      </p>

      <SummaryPanel :summary="summary" />

      <Card title="Pressure profile">
        <template #actions>
          <Switch v-model="showBaseline" label="Show local baseline" />
        </template>
        <PressureChart
          v-if="readings.length > 0"
          :readings="readings"
          :show-baseline="showBaseline"
        />
        <p v-else class="text-sm text-slate-500">
          No readings in this distance range. Widen the filter or pick "Whole run".
        </p>
      </Card>

      <Card>
        <Tabs :tabs="TABS">
          <template #panel-segments>
            <AnomalySegments :segments="segments" />
          </template>
          <template #panel-readings>
            <ReadingsTable :readings="readings" />
          </template>
        </Tabs>
      </Card>

      <Modal
        :open="explainerOpen"
        title="How anomalies are detected"
        @close="explainerOpen = false"
      >
        <p>
          A reading is flagged when its pressure sits more than
          <strong>{{ run.anomaly_rule.threshold_sigmas }} standard deviations</strong>
          away from the mean of the
          <strong>{{ run.anomaly_rule.window_size }} readings before it</strong>. The
          window is shorter at the start of a run, and the first two readings get no
          verdict because a standard deviation needs at least two samples.
        </p>
        <p>
          The baseline is computed on the server over the whole run, so a reading keeps
          its verdict no matter which distance range you filter to.
        </p>
        <p>
          Two limits worth knowing. Because the window trails the reading, a
          <em>sustained</em> shift masks its own tail: the window absorbs the new level
          within a few readings, so only the onset is flagged. And at two standard
          deviations roughly one reading in twenty is flagged by ordinary scatter, which
          is why adjacent flags are grouped into segments — a multi-reading segment is
          usually a real event, a lone flag usually is not.
        </p>
        <template #actions>
          <Button variant="secondary" size="sm" @click="explainerOpen = false">
            Close
          </Button>
        </template>
      </Modal>
    </template>
  </div>
</template>

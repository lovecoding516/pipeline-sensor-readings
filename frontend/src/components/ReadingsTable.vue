<script setup lang="ts">
import { computed } from 'vue'

import type { Reading } from '../api'
import { deviationInSigmas } from '../segments'
import { Badge, Table, type TableColumn } from './ui'

const props = defineProps<{ readings: Reading[] }>()

const COLUMNS: TableColumn[] = [
  { key: 'distance', label: 'Distance', align: 'right' },
  { key: 'pressure', label: 'Pressure', align: 'right' },
  { key: 'temperature', label: 'Temperature', align: 'right' },
  { key: 'baseline', label: 'Local baseline', align: 'right' },
  { key: 'deviation', label: 'Deviation', align: 'right' },
  { key: 'status', label: 'Status' },
]

const rows = computed(() =>
  props.readings.map((reading) => {
    const sigmas = deviationInSigmas(reading)
    return {
      id: reading.distance_m,
      distance: `${reading.distance_m} m`,
      pressure: reading.pressure_bar.toFixed(2),
      temperature: reading.temperature_c.toFixed(1),
      baseline: reading.baseline_mean === null ? '—' : reading.baseline_mean.toFixed(2),
      deviation: sigmas === null ? '—' : `${sigmas >= 0 ? '+' : ''}${sigmas.toFixed(1)}σ`,
      anomaly: reading.anomaly,
    }
  }),
)
</script>

<template>
  <Table
    :columns="COLUMNS"
    :rows="rows"
    row-key="id"
    empty-message="No readings in this range."
    max-height-class="max-h-[28rem]"
  >
    <template #cell-status="{ row }">
      <Badge v-if="row.anomaly" tone="red">Anomaly</Badge>
      <span v-else class="text-slate-400">—</span>
    </template>
  </Table>
</template>

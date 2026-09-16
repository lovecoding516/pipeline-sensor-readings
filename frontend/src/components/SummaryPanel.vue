<script setup lang="ts">
import type { SummaryResponse } from '../api'
import { Stat } from './ui'

defineProps<{ summary: SummaryResponse | null }>()

function bar(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)} bar`
}

function anomalyShare(summary: SummaryResponse): string {
  if (summary.count === 0) return ''
  return `${((summary.anomaly_count / summary.count) * 100).toFixed(1)}% of range`
}
</script>

<template>
  <div v-if="summary" class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
    <Stat label="Readings" :value="summary.count" />
    <Stat
      label="Anomalies"
      :value="summary.anomaly_count"
      :hint="anomalyShare(summary)"
      :highlight="summary.anomaly_count > 0"
    />
    <Stat label="Min pressure" :value="bar(summary.pressure_min)" />
    <Stat label="Mean pressure" :value="bar(summary.pressure_mean)" />
    <Stat label="Max pressure" :value="bar(summary.pressure_max)" />
  </div>
</template>

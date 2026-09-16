<script setup lang="ts">
import { computed } from 'vue'

import type { AnomalySegment, SegmentDirection } from '../segments'
import { Badge, Table, type TableColumn } from './ui'

const props = defineProps<{ segments: AnomalySegment[] }>()

const COLUMNS: TableColumn[] = [
  { key: 'extent', label: 'Segment' },
  { key: 'direction', label: 'Type' },
  { key: 'readingCount', label: 'Readings', align: 'right' },
  { key: 'peakPressure', label: 'Peak pressure', align: 'right' },
  { key: 'peakSigmas', label: 'Peak deviation', align: 'right' },
]

const LABELS: Record<SegmentDirection, string> = {
  drop: 'Pressure drop',
  jump: 'Pressure jump',
  mixed: 'Unstable',
}

const TONES: Record<SegmentDirection, 'red' | 'amber' | 'slate'> = {
  drop: 'red',
  jump: 'amber',
  mixed: 'slate',
}

const rows = computed(() =>
  props.segments.map((segment) => ({
    id: `${segment.fromM}-${segment.toM}`,
    extent:
      segment.fromM === segment.toM
        ? `${segment.fromM} m`
        : `${segment.fromM}–${segment.toM} m`,
    direction: segment.direction,
    readingCount: segment.readingCount,
    peakPressure: `${segment.peak.pressure_bar.toFixed(2)} bar`,
    peakSigmas:
      segment.peakSigmas === null
        ? '—'
        : `${segment.peakSigmas >= 0 ? '+' : ''}${segment.peakSigmas.toFixed(1)}σ`,
  })),
)
</script>

<template>
  <Table
    :columns="COLUMNS"
    :rows="rows"
    row-key="id"
    empty-message="No anomalies in this range."
    max-height-class="max-h-96"
  >
    <template #cell-extent="{ row }">
      <span class="tabular font-semibold">{{ row.extent }}</span>
    </template>
    <template #cell-direction="{ row }">
      <Badge :tone="TONES[row.direction as SegmentDirection]">
        {{ LABELS[row.direction as SegmentDirection] }}
      </Badge>
    </template>
  </Table>
</template>

<script setup lang="ts">
import Chart from 'chart.js/auto'
import type { ChartDataset, Point } from 'chart.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Reading } from '../api'
import { deviationInSigmas } from '../segments'

type LineDataset = ChartDataset<'line', Point[]>

const props = defineProps<{
  readings: Reading[]
  showBaseline: boolean
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart<'line', Point[]> | null = null

let byDistance = new Map<number, Reading>()

function buildDatasets() {
  const profile = props.readings.map((r) => ({ x: r.distance_m, y: r.pressure_bar }))
  const anomalies = props.readings
    .filter((r) => r.anomaly)
    .map((r) => ({ x: r.distance_m, y: r.pressure_bar }))

  const datasets: LineDataset[] = [
    {
      label: 'Pressure',
      data: profile,
      borderColor: '#2563eb',
      backgroundColor: '#2563eb',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0,
      order: 3,
    },
    {
      label: `Anomaly (${anomalies.length})`,
      data: anomalies,
      showLine: false,
      pointBackgroundColor: '#dc2626',
      pointBorderColor: '#ffffff',
      pointBorderWidth: 1,
      pointRadius: 5,
      pointHoverRadius: 7,
      order: 1,
    },
  ]

  if (props.showBaseline) {
    datasets.push({
      label: 'Local baseline (mean of previous 20)',
      data: props.readings
        .filter((r) => r.baseline_mean !== null)
        .map((r) => ({ x: r.distance_m, y: r.baseline_mean as number })),
      borderColor: '#94a3b8',
      borderWidth: 1,
      borderDash: [5, 4],
      pointRadius: 0,
      tension: 0,
      order: 2,
    })
  }
  return datasets
}

function render() {
  byDistance = new Map(props.readings.map((r) => [r.distance_m, r]))

  if (chart) {
    // Replacing datasets rather than the chart keeps zoom/axis state stable.
    chart.data.datasets = buildDatasets()
    chart.update()
    return
  }
  if (!canvas.value) return

  chart = new Chart<'line', Point[]>(canvas.value, {
    type: 'line',
    data: { datasets: buildDatasets() },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      normalized: true,
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
      scales: {
        x: {
          type: 'linear',
          title: { display: true, text: 'Distance along pipeline (m)' },
          ticks: { maxTicksLimit: 12 },
        },
        y: {
          title: { display: true, text: 'Pressure (bar)' },
        },
      },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, boxHeight: 8 } },
        tooltip: {
          callbacks: {
            title: (items) => `${items[0]?.parsed.x ?? '?'} m`,
            label: (item) => {
              const distance = item.parsed.x
              const reading = distance === null ? undefined : byDistance.get(distance)
              if (!reading) return `${item.formattedValue} bar`

              const lines = [
                `Pressure: ${reading.pressure_bar.toFixed(2)} bar`,
                `Temperature: ${reading.temperature_c.toFixed(1)} °C`,
              ]
              const sigmas = deviationInSigmas(reading)
              if (sigmas !== null) {
                lines.push(
                  `Deviation: ${sigmas >= 0 ? '+' : ''}${sigmas.toFixed(1)}σ from local trend`,
                )
              }
              if (reading.anomaly) {
                lines.push('Flagged as anomalous')
              }
              return lines
            },
          },
        },
      },
    },
  })
}

onMounted(render)
watch([() => props.readings, () => props.showBaseline], render)
onBeforeUnmount(() => {
  chart?.destroy()
  chart = null
})
</script>

<template>
  <div class="relative h-[420px]">
    <canvas ref="canvas" />
  </div>
</template>

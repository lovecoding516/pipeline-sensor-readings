<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { DistanceRange } from '../api'
import { Button, Input, Select, type SelectOption } from './ui'

const CUSTOM = 'custom'
const WHOLE_RUN = 'all'
const PRESET_COUNT = 4

const props = defineProps<{
  busy: boolean
  applied: DistanceRange
  extent: DistanceRange
}>()

const emit = defineEmits<{ apply: [range: DistanceRange] }>()

const fromText = ref('')
const toText = ref('')

watch(
  () => props.applied,
  (range) => {
    fromText.value = range.from_m === null ? '' : String(range.from_m)
    toText.value = range.to_m === null ? '' : String(range.to_m)
  },
  { immediate: true },
)

function parse(text: string): number | null | 'invalid' {
  const trimmed = text.trim()
  if (trimmed === '') return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : 'invalid'
}

const from = computed(() => parse(fromText.value))
const to = computed(() => parse(toText.value))
const hasInvalidInput = computed(() => from.value === 'invalid' || to.value === 'invalid')

const problem = computed(() => {
  if (hasInvalidInput.value) return 'Distances must be numbers.'
  if (from.value !== null && to.value !== null && from.value > to.value) {
    return 'Start is beyond the end, so this range is empty.'
  }
  return null
})

const presets = computed<SelectOption<string>[]>(() => {
  const options: SelectOption<string>[] = [{ value: WHOLE_RUN, label: 'Whole run' }]
  const { from_m: start, to_m: end } = props.extent
  if (start === null || end === null || end <= start) return options

  const step = (end - start) / PRESET_COUNT
  for (let slice = 0; slice < PRESET_COUNT; slice += 1) {
    const lower = Math.round(start + slice * step)
    const upper =
      slice === PRESET_COUNT - 1 ? end : Math.round(start + (slice + 1) * step)
    options.push({ value: `${lower}:${upper}`, label: `${lower}–${upper} m` })
  }
  return options
})

const selected = computed<string>({
  get() {
    const { from_m, to_m } = props.applied
    if (from_m === null && to_m === null) return WHOLE_RUN
    const key = `${from_m}:${to_m}`
    return presets.value.some((preset) => preset.value === key) ? key : CUSTOM
  },
  set(value) {
    if (value === CUSTOM) return
    if (value === WHOLE_RUN) {
      emit('apply', { from_m: null, to_m: null })
      return
    }
    const [lower, upper] = value.split(':').map(Number)
    emit('apply', { from_m: lower, to_m: upper })
  },
})

const presetOptions = computed(() =>
  selected.value === CUSTOM
    ? [{ value: CUSTOM, label: 'Custom range' }, ...presets.value]
    : presets.value,
)

function apply() {
  if (hasInvalidInput.value) return
  emit('apply', { from_m: from.value as number | null, to_m: to.value as number | null })
}
</script>

<template>
  <form class="flex flex-wrap items-end gap-3" @submit.prevent="apply">
    <Select v-model="selected" :options="presetOptions" label="Quick range" />
    <Input
      id="from_m"
      v-model="fromText"
      label="From (m)"
      inputmode="decimal"
      :placeholder="extent.from_m === null ? 'start' : String(extent.from_m)"
    />
    <Input
      id="to_m"
      v-model="toText"
      label="To (m)"
      inputmode="decimal"
      :placeholder="extent.to_m === null ? 'end' : String(extent.to_m)"
    />
    <Button type="submit" :disabled="busy || hasInvalidInput">Apply</Button>

    <p v-if="problem" class="basis-full text-xs text-amber-700">{{ problem }}</p>
  </form>
</template>

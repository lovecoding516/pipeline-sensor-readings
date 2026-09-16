<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    hint?: string
    highlight?: boolean
  }>(),
  { hint: '', highlight: false },
)
</script>

<template>
  <div
    class="flex flex-col gap-0.5 rounded-lg border px-3.5 py-3"
    :class="highlight ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-white'"
  >
    <span class="text-xs font-medium tracking-wide text-slate-500 uppercase">
      {{ label }}
    </span>
    <span class="tabular text-2xl font-semibold text-slate-900">{{ value }}</span>
    <span v-if="hint" class="text-xs text-slate-500">{{ hint }}</span>
  </div>
</template>

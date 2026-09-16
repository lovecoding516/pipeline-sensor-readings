<script setup lang="ts">
type Tone = 'red' | 'amber' | 'slate' | 'indigo' | 'blue'

withDefaults(defineProps<{ tone?: Tone }>(), { tone: 'slate' })

const TONES: Record<Tone, string> = {
  red: 'bg-red-100 text-red-800',
  amber: 'bg-amber-100 text-amber-800',
  slate: 'bg-slate-100 text-slate-700',
  indigo: 'bg-indigo-100 text-indigo-800',
  blue: 'bg-blue-100 text-blue-800',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
    :class="TONES[tone]"
  >
    <slot />
  </span>
</template>

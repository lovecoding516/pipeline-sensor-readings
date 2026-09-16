<script setup lang="ts">
type Tone = 'error' | 'info'

withDefaults(defineProps<{ tone?: Tone }>(), { tone: 'info' })

const TONES: Record<Tone, string> = {
  error: 'border-red-300 bg-red-50 text-red-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
}
</script>

<template>
  <p
    class="rounded-lg border px-3 py-2.5 text-sm"
    :class="TONES[tone]"
    :role="tone === 'error' ? 'alert' : 'status'"
  >
    <slot />
  </p>
</template>

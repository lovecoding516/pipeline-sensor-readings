<script setup lang="ts">
// Aliased: an unaliased import would collide with this file's own name.
import { Switch as HeadlessSwitch } from '@headlessui/vue'

const model = defineModel<boolean>({ required: true })

defineProps<{ label: string }>()
</script>

<template>
  <div class="flex items-center gap-2">
    <HeadlessSwitch
      v-model="model"
      class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      :class="model ? 'bg-blue-600' : 'bg-slate-300'"
    >
      <span class="sr-only">{{ label }}</span>
      <span
        class="pointer-events-none mt-0.5 inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform"
        :class="model ? 'translate-x-4' : 'translate-x-0.5'"
      />
    </HeadlessSwitch>
    <span class="text-sm text-slate-600">{{ label }}</span>
  </div>
</template>

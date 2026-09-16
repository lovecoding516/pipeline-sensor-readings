<script setup lang="ts">
import { ref } from 'vue'

import { Button } from './ui'

defineProps<{ busy: boolean }>()
const emit = defineEmits<{ select: [file: File] }>()

const input = ref<HTMLInputElement | null>(null)
const selectedName = ref<string | null>(null)

function onChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  selectedName.value = file.name
  emit('select', file)

  if (input.value) input.value.value = ''
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <Button as="label" :disabled="busy" class="relative overflow-hidden">
      <input
        ref="input"
        type="file"
        accept=".csv,text/csv"
        :disabled="busy"
        class="absolute inset-0 w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
        @change="onChange"
      />
      {{ busy ? 'Uploading…' : 'Upload readings CSV' }}
    </Button>
    <span v-if="selectedName" class="text-xs text-slate-500">{{ selectedName }}</span>
  </div>
</template>

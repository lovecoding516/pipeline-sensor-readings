<script setup lang="ts">
const model = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    id: string
    label: string
    placeholder?: string
    inputmode?: 'text' | 'decimal' | 'numeric'
  }>(),
  { placeholder: '', inputmode: 'text' },
)
</script>

<template>
  <div class="flex flex-col gap-1">
    <label :for="id" class="text-xs font-medium tracking-wide text-slate-500 uppercase">
      {{ label }}
    </label>
    <input
      :id="id"
      v-model="model"
      :placeholder="placeholder"
      :inputmode="inputmode"
      class="tabular w-28 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-2 focus:outline-offset-1 focus:outline-blue-500"
    />
  </div>
</template>

<script setup lang="ts" generic="T extends string | number">
import {
  Listbox,
  ListboxButton,
  ListboxLabel,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { computed } from 'vue'

import type { SelectOption } from './types'

const model = defineModel<T>({ required: true })

const props = defineProps<{
  options: SelectOption<T>[]
  label: string
}>()

const selectedLabel = computed(
  () => props.options.find((option) => option.value === model.value)?.label ?? '',
)
</script>

<template>
  <Listbox v-model="model" as="div" class="relative flex flex-col gap-1">
    <ListboxLabel class="text-xs font-medium tracking-wide text-slate-500 uppercase">
      {{ label }}
    </ListboxLabel>

    <ListboxButton
      class="flex w-48 cursor-pointer items-center justify-between rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-left text-sm hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-500"
    >
      <span class="truncate">{{ selectedLabel }}</span>
      <span aria-hidden="true" class="ml-2 text-slate-400">▾</span>
    </ListboxButton>

    <ListboxOptions
      class="absolute top-full left-0 z-10 mt-1 max-h-60 w-48 overflow-auto rounded-md border border-slate-200 bg-white py-1 text-sm shadow-lg focus:outline-none"
    >
      <ListboxOption
        v-for="option in options"
        v-slot="{ active, selected }"
        :key="String(option.value)"
        :value="option.value"
        as="template"
      >
        <li
          class="cursor-pointer px-2.5 py-1.5"
          :class="[
            active ? 'bg-blue-50 text-blue-900' : 'text-slate-700',
            selected ? 'font-semibold' : '',
          ]"
        >
          {{ option.label }}
        </li>
      </ListboxOption>
    </ListboxOptions>
  </Listbox>
</template>

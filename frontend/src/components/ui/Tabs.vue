<script setup lang="ts">
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/vue'

import type { TabDefinition } from './types'

defineProps<{ tabs: TabDefinition[] }>()
</script>

<template>
  <TabGroup>
    <TabList class="flex gap-1 border-b border-slate-200">
      <Tab v-for="tab in tabs" v-slot="{ selected }" :key="tab.key" as="template">
        <button
          class="-mb-px cursor-pointer border-b-2 px-3 py-2 text-sm font-medium focus:outline-none"
          :class="
            selected
              ? 'border-blue-600 text-blue-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          "
        >
          {{ tab.label }}
        </button>
      </Tab>
    </TabList>

    <TabPanels class="pt-4">
      <TabPanel v-for="tab in tabs" :key="tab.key" :unmount="false">
        <slot :name="`panel-${tab.key}`" />
      </TabPanel>
    </TabPanels>
  </TabGroup>
</template>

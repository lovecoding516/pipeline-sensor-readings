<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'

defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <TransitionRoot :show="open" as="template">
    <Dialog class="relative z-50" @close="emit('close')">
      <TransitionChild
        as="template"
        enter="duration-150 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-100 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-slate-900/40" aria-hidden="true" />
      </TransitionChild>

      <div class="fixed inset-0 flex items-center justify-center p-4">
        <TransitionChild
          as="template"
          enter="duration-150 ease-out"
          enter-from="opacity-0 scale-95"
          enter-to="opacity-100 scale-100"
          leave="duration-100 ease-in"
          leave-from="opacity-100 scale-100"
          leave-to="opacity-0 scale-95"
        >
          <DialogPanel
            class="max-h-[85vh] w-full max-w-lg overflow-auto rounded-xl bg-white p-5 shadow-xl"
          >
            <DialogTitle class="text-base font-semibold text-slate-900">
              {{ title }}
            </DialogTitle>
            <div class="mt-3 space-y-3 text-sm text-slate-600">
              <slot />
            </div>
            <div class="mt-5 flex justify-end">
              <slot name="actions" />
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title?: string }>(), { title: '' })
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
    <header
      v-if="title || $slots.title || $slots.actions"
      class="mb-3 flex flex-wrap items-baseline justify-between gap-3"
    >
      <h2 class="text-base font-semibold text-slate-900">
        <slot name="title">{{ title }}</slot>
      </h2>
      <div class="flex items-center gap-3">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>

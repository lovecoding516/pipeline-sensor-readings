<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'primary' | 'secondary' | 'ghost'
type Size = 'sm' | 'md'

const props = withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    as?: 'button' | 'label' | 'span'
    type?: 'button' | 'submit'
    disabled?: boolean
  }>(),
  { variant: 'primary', size: 'md', as: 'button', type: 'button', disabled: false },
)

const VARIANTS: Record<Variant, string> = {
  primary: 'border-blue-600 bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  ghost: 'border-transparent bg-transparent text-blue-700 hover:bg-blue-50',
}

const SIZES: Record<Size, string> = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3.5 py-2 text-sm',
}

const classes = computed(() => [
  'inline-flex items-center justify-center gap-1.5 rounded-md border font-medium',
  'transition-colors focus-visible:outline-2 focus-visible:outline-offset-2',
  'focus-visible:outline-blue-600',
  VARIANTS[props.variant],
  SIZES[props.size],
  props.disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
])
</script>

<template>
  <component
    :is="as"
    :class="classes"
    :type="as === 'button' ? type : undefined"
    :disabled="as === 'button' ? disabled : undefined"
    :aria-disabled="as === 'button' ? undefined : disabled"
  >
    <slot />
  </component>
</template>

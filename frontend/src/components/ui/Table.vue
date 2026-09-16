<script setup lang="ts" generic="Row extends Record<string, unknown>">
import type { TableColumn } from './types'

const props = withDefaults(
  defineProps<{
    columns: TableColumn[]
    rows: Row[]
    rowKey?: string
    emptyMessage?: string
    maxHeightClass?: string
  }>(),
  { rowKey: '', emptyMessage: 'Nothing to show.', maxHeightClass: '' },
)

function keyFor(row: Row, index: number): string | number {
  const value = props.rowKey ? row[props.rowKey] : undefined
  return typeof value === 'string' || typeof value === 'number' ? value : index
}

function alignClass(column: TableColumn): string {
  return column.align === 'right' ? 'text-right' : 'text-left'
}
</script>

<template>
  <p v-if="rows.length === 0" class="text-sm text-slate-500">
    {{ emptyMessage }}
  </p>

  <div v-else class="overflow-auto" :class="maxHeightClass">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            scope="col"
            class="sticky top-0 border-b border-slate-200 bg-white px-2.5 py-2 text-xs font-semibold tracking-wide text-slate-500 uppercase"
            :class="alignClass(column)"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in rows"
          :key="keyFor(row, index)"
          class="hover:bg-slate-50"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="border-b border-slate-100 px-2.5 py-1.5"
            :class="[alignClass(column), column.align === 'right' ? 'tabular' : '']"
          >
            <slot :name="`cell-${column.key}`" :row="row">{{ row[column.key] }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

export type Align = 'left' | 'right'

export interface TableColumn {
  /** Matches a key on the row object, and names the `cell-<key>` slot. */
  key: string
  label: string
  align?: Align
}

export interface SelectOption<T = string> {
  value: T
  label: string
}

export interface TabDefinition {
  /** Names the panel slot: `<template #panel-overview>`. */
  key: string
  label: string
}

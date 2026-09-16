import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import { globalIgnores } from 'eslint/config'
import pluginVue from 'eslint-plugin-vue'

export default defineConfigWithVueTs(
  { name: 'app/files-to-lint', files: ['**/*.{ts,mts,vue}'] },
  globalIgnores(['dist/**', 'node_modules/**']),

  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,

  // Last, so Prettier owns formatting and ESLint owns correctness.
  skipFormatting,

  {
    name: 'app/rules',
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },

  {
    // The UI kit uses single-word names (`Button`, `Table`). The multi-word
    // rule guards against clashing with real HTML elements, which cannot
    // happen here: these are imported explicitly, never globally registered.
    name: 'app/ui-kit-single-word-names',
    files: ['src/components/ui/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  },
)

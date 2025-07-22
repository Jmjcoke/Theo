// @ts-check
import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  // Global ignores first
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '.next/**',
      '**/*.config.js',
      '**/*.config.ts',
      'PocketFlow-main/**',
      'apps/api/venv/**',
      'apps/web/dist/**',
      'apps/web/node_modules/**',
      '**/src.archive/**',
      'apps/web/test_frontend.js',
      '.bmad-core/**',
      'web-bundles/**',
      'docs/**',
    ],
  },

  // Base JavaScript/TypeScript rules
  js.configs.recommended,
  
  // TypeScript configuration
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      '@typescript-eslint': typescript,
    },
    rules: {
      ...typescript.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-duplicate-enum-values': 'error',
      'no-undef': 'off', // TypeScript handles this
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error'
    },
  },

  // React configuration
  {
    files: ['apps/web/**/*.{ts,tsx}'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off', // Not needed in React 17+
      'react/prop-types': 'off', // Using TypeScript for prop validation
      'react/no-unknown-property': ['error', { ignore: ['cmdk-input-wrapper'] }], // Allow cmdk custom properties
      'react/no-unescaped-entities': ['error', { forbid: ['>', '}'] }], // More lenient with apostrophes
      'no-undef': 'off', // TypeScript handles this
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },

  // Disable conflicting rules (prettier integration)
  {
    rules: {
      'no-mixed-spaces-and-tabs': 'off',
      'no-unexpected-multiline': 'off',
    },
  },
];
import { createPreset } from 'fumadocs-ui/tailwind-plugin';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './content/**/*.{md,mdx}',
    './mdx-components.{ts,tsx}',
    './node_modules/fumadocs-ui/dist/**/*.js',
    './node_modules/fumadocs-openapi/dist/**/*.js',
  ],
  presets: [createPreset()],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            h1: {
              letterSpacing: '-0.025em', // This is what tracking-tight does
              fontWeight: '500', // font-medium (500) instead of bold (700)
            },
            h2: {
              letterSpacing: '-0.025em',
              fontWeight: '500',
            },
            h3: {
              letterSpacing: '-0.025em',
              fontWeight: '500',
            },
            h4: {
              letterSpacing: '-0.025em',
              fontWeight: '500',
            },
            h5: {
              letterSpacing: '-0.025em',
              fontWeight: '500',
            },
            h6: {
              letterSpacing: '-0.025em',
              fontWeight: '500',
            },
          },
        },
      },
    },
  },
};

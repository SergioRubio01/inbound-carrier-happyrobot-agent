/**
 * @file: tailwind.config.ts
 * @description: Tailwind CSS configuration file, defining theme customizations, plugins, and content sources.
 * @author HappyRobot Team
 * @created 2025-05-21
 * @lastModified 2025-05-21
 *
 * Modification History:
 * - 2025-05-21: Added Bizai brand colors and typography.
 *
 * Dependencies:
 * - tailwindcss
 * - tailwindcss-animate
 */
import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        bizai: {
          primary: '#0D253F', // Deep Navy
          'primary-dark': '#0A1D30', // Darker navy for dark mode
          'primary-darker': '#051118', // Even darker for contrast
          accent1: '#00B8D9', // Vibrant Teal/Cyan
          accent2: '#FFAB00', // Muted Orange/Amber
          yellow: '#FFD700', // Gold Yellow for hover states
          'yellow-dark': '#FFC107', // Darker yellow for better contrast
          white: '#FFFFFF',
          lightGray: '#F4F6F8',
          darkGray: '#212529',
          mediumGray: '#495057',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Example: Inter for headings and body
        // Add Manrope or Open Sans if needed and configured
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'shimmer-once': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      animation: {
        'shimmer-once': 'shimmer-once 1s ease-in-out forwards',
        'fade-in': 'fade-in 0.5s ease-out forwards',
        'gradient-shift': 'gradient-shift 6s ease infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config;

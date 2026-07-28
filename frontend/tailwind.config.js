/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        ocean: { DEFAULT: '#1B4F72', light: '#2E86C1', dark: '#0D1B2A' },
        jungle: { DEFAULT: '#27AE60', light: '#2ECC71', dark: '#1A7A43' },
        spice: { DEFAULT: '#E67E22', light: '#F39C12', dark: '#B7600E' },
        crimson: { DEFAULT: '#C0392B', light: '#E74C3C', dark: '#922B21' },
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      animation: {
        'gradient-shift': 'gradient 4s ease infinite',
      },
    },
  },
  plugins: [],
}

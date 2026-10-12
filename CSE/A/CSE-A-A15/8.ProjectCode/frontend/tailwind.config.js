/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 950: '#0b1220', 900: '#111a2e', 800: '#1a2540', 700: '#27345a' },
        brand: { 50: '#ecfdf8', 100: '#d1faec', 500: '#14b88a', 600: '#0d9670', 700: '#0b7a5c' },
      },
      fontFamily: { mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'] },
    },
  },
  plugins: [],
}

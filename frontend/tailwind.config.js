/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        jet: {
          950: '#050505',
          900: '#0A0A0A', // Primary Jet Black
          850: '#0F0F12',
          800: '#141418',
          750: '#1A1A20',
          700: '#22222A',
          600: '#2E2E38',
          500: '#464654',
          400: '#78788C',
          300: '#A4A4B8',
          200: '#D2D2DE',
          100: '#F0F0F5',
        },
        cerulean: {
          DEFAULT: '#007BA7', // Primary Cerulean Blue
          light: '#189FD2',
          dark: '#005777',
          muted: 'rgba(0, 123, 167, 0.2)',
          subtle: 'rgba(0, 123, 167, 0.08)',
          glow: 'rgba(0, 123, 167, 0.45)',
        },
        neonrose: {
          DEFAULT: '#FF2D95', // Primary Neon Rose
          light: '#FF64AC',
          dark: '#C8156E',
          muted: 'rgba(255, 45, 149, 0.2)',
          subtle: 'rgba(255, 45, 149, 0.08)',
          glow: 'rgba(255, 45, 149, 0.45)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.4)',
        'glass-sm': '0 4px 16px 0 rgba(0, 0, 0, 0.3)',
        'glass-lg': '0 12px 48px 0 rgba(0, 0, 0, 0.55)',
        'glow-cerulean': '0 0 25px rgba(0, 123, 167, 0.35)',
        'glow-cerulean-lg': '0 0 45px rgba(0, 123, 167, 0.55)',
        'glow-rose': '0 0 25px rgba(255, 45, 149, 0.35)',
        'glow-rose-lg': '0 0 45px rgba(255, 45, 149, 0.55)',
        'inner-glow': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.08)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'subtle-grid': 'radial-gradient(circle, rgba(255, 255, 255, 0.04) 1px, transparent 1px)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
}

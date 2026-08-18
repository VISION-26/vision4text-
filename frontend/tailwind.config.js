/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fff1fb', 100: '#ffe2f8', 200: '#ffc5f1', 300: '#ff98e5', 400: '#f865d5',
          500: '#ef2cc1', 600: '#d71aaa', 700: '#b3118c', 800: '#921071', 900: '#78115e', 950: '#4c043a',
        },
        together: {
          night: '#010120', surface: '#10102d', soft: '#27273d', orange: '#fc4c02', magenta: '#ef2cc1',
          periwinkle: '#bdbbff', mint: '#c8f6f9', body: '#73737d',
        },
        darkblue: { 900: '#010120', 950: '#080812' },
      },
      fontFamily: {
        sans: ['Inter', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['SFMono-Regular', 'Consolas', 'Liberation Mono', 'monospace'],
      },
      boxShadow: {
        soft: '0 10px 30px rgba(1,1,32,0.06)',
        'soft-lg': '0 22px 70px rgba(1,1,32,0.12)',
      },
      borderRadius: { '2xl': '8px' },
    },
  },
  plugins: [],
};

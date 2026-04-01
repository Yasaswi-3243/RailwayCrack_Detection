/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rail: {
          50: '#f8f9fa',
          100: '#e9ecef',
          900: '#232526',
        },
      },
      backgroundImage: {
        'rail-gradient': 'linear-gradient(120deg, #232526 0%, #485563 40%, #00c6ff 100%)',
      },
    },
  },
  plugins: [],
}

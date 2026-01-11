/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'edms-primary': '#1e40af',
        'edms-secondary': '#64748b',
        'edms-accent': '#059669',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
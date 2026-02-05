/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.html",
    "./apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2E7D32',      // your main green
        'primary-dark': '#1B5E20',
        accent: '#4CAF50',
      },
    },
  },
  plugins: [],
}

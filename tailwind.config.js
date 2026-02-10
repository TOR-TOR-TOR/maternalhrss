/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Important: tell Tailwind where to look for classes
    "./templates/**/*.html",
    "./apps/**/*.html",
    "./apps/**/templates/**/*.html",
    // If you later add JS files with classes (Alpine.js, htmx, etc.)
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // You can define project-specific colors here
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        danger: {
          600: '#dc2626',
          700: '#b91c1c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

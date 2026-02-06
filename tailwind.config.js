/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // === IMPORTANT: Tell Tailwind where to look for class names ===
    
    // All templates in the main templates folder
    "./templates/**/*.html",
    
    // If you ever put templates inside apps (some people do)
    "./apps/**/*.html",
    
    // If you add any custom JS files later that use Tailwind classes
    "./static_src/**/*.js",
    
    // Optional: if you create partials or components folders
    "./templates/partials/**/*.html",
  ],
  
  theme: {
    extend: {
      // === Customize colors to match your existing design ===
      colors: {
        primary: {
          DEFAULT: '#2E7D32',    // main green from your old --primary-color
          50:  '#f0fdf4',
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
        secondary: '#43A047',
        danger:    '#D32F2F',
        warning:   '#F57C00',
        info:      '#1976D2',
        muted:     '#6B7280',
      },
      
      // Optional: better spacing / typography for dashboards
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  
  plugins: [
    // Optional: add these later when you need them
    // require('@tailwindcss/forms'),
    // require('@tailwindcss/typography'),
  ],
}

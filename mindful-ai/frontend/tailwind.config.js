
export default {
  content: ['./index.html', './src*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'sans-serif'],
        display: ['"Playfair Display"', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        ink: {
          50: '#f0f0f5',
          100: '#e0e0eb',
          200: '#c2c2d6',
          300: '#9999bb',
          400: '#6666a0',
          500: '#333385',
          600: '#29296b',
          700: '#1f1f51',
          800: '#141436',
          900: '#0a0a1c',
          950: '#050510',
        },
        sage: {
          50: '#f0f7f4',
          100: '#dceee7',
          200: '#b9ddd0',
          300: '#8ac4b1',
          400: '#5aa68f',
          500: '#3a8a74',
          600: '#2d6f5d',
          700: '#265a4c',
          800: '#21483e',
          900: '#1e3c34',
        },
        blush: {
          50: '#fdf2f4',
          100: '#fce7eb',
          200: '#f9d0d9',
          300: '#f4a8b9',
          400: '#ed7594',
          500: '#e24872',
          600: '#ce2d5a',
          700: '#ad2049',
          800: '#911d41',
          900: '#7c1c3c',
        },
        amber: {
          50: '#fffbeb',
          400: '#fbbf24',
          500: '#f59e0b',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}

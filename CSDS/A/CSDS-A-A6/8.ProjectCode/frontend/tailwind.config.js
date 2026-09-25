/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9eaff",
          200: "#bcdaff",
          300: "#8ec2ff",
          400: "#589eff",
          500: "#2f78f6",
          600: "#1c5aeb",
          700: "#1846c9",
          800: "#193ba3",
          900: "#193581",
        },
      },
    },
  },
  plugins: [],
};

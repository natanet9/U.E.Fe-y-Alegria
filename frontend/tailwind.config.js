/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Roboto Flex", "Roboto", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          600: "#3449eb",
          700: "#2a3bd4",
        },
      },
      boxShadow: {
        panel: "0 20px 50px rgba(17, 24, 39, 0.12)",
      },
    },
  },
  plugins: [],
};

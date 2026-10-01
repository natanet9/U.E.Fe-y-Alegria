/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Roboto Flex", "Roboto", "system-ui", "sans-serif"],
      },
      colors: {
        red: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
        },
        brand: {
          50: "#fff1f1",
          100: "#ffd6d6",
          600: "#FF2C2C",
          700: "#D92323",
        },
      },
      boxShadow: {
        panel: "0 20px 50px rgba(17, 24, 39, 0.12)",
      },
    },
  },
  plugins: [],
};

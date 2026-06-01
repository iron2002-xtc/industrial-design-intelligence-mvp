import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        graphite: "#2c2c2c",
        fog: "#f4f4f2",
        panel: "#ffffff",
        line: "#e4e4df",
        signal: "#1d7f70",
        copper: "#b66534",
        plum: "#6f5d7a",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(17, 17, 17, 0.08)",
        tight: "0 8px 24px rgba(17, 17, 17, 0.08)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;

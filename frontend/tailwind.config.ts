import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b1020",
          900: "#111827",
          700: "#334155",
          500: "#64748b",
        },
        cloud: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
        },
        brand: {
          500: "#2563eb",
          600: "#1d4ed8",
          700: "#1e40af",
        },
        mint: {
          500: "#10b981",
          600: "#059669",
        },
      },
      boxShadow: {
        soft: "0 18px 60px rgba(15, 23, 42, 0.08)",
        line: "0 1px 0 rgba(15, 23, 42, 0.08)",
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
} satisfies Config;

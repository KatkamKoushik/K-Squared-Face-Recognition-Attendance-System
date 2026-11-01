import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        institutional: {
          navy: "#1E3A5F",
          blue: "#0284C7",
          gold: "#A16207",
          bg: "#F8FAFC",
          surface: "#FFFFFF",
          border: "#CBD5E1",
          text: "#0F172A",
          muted: "#475569",
        },
        status: {
          matched: "#16A34A",
          review: "#D97706",
          recapture: "#EA580C",
          unknown: "#64748B",
          error: "#DC2626",
          committed: "#0D9488",
        },
      },
      fontFamily: {
        serif: ["var(--font-eb-garamond)", "Crimson Text", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;


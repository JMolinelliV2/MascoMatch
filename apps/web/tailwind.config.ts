import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: { colors: { background: "var(--background)", surface: "var(--surface)", ink: "var(--text-primary)", muted: "var(--text-secondary)", primary: "var(--primary)", "primary-soft": "var(--primary-soft)", information: "var(--accent-blue)", success: "var(--success)", warning: "var(--warning)", danger: "var(--danger)", line: "var(--border)" } } },
  plugins: [],
};

export default config;


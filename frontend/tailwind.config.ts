import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: "var(--forest)",
        sage: "var(--sage)",
        olive: "var(--olive)",
        cream: "var(--cream)",
        moss: "var(--moss)",
        amber: "var(--amber)",
        brick: "var(--brick)"
      },
      fontFamily: { display: ["var(--font-anton)"], sans: ["var(--font-inter)"] }
    }
  },
  plugins: []
};

export default config;

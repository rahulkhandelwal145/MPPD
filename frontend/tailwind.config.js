export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        display: ["Sora", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        indigo: { DEFAULT: "#6366F1" },
        brand: {
          50: "#eef2ff", 100: "#e0e7ff", 200: "#c7d2fe", 300: "#a5b4fc",
          400: "#818cf8", 500: "#6366f1", 600: "#4f46e5", 700: "#4338ca",
          800: "#3730a3", 900: "#312e81",
        },
      },
      boxShadow: {
        soft: "0 2px 10px -3px rgb(15 23 42 / 0.08)",
        card: "0 6px 28px -10px rgb(15 23 42 / 0.14)",
        lift: "0 24px 48px -16px rgb(79 70 229 / 0.30)",
        glow: "0 0 0 1px rgb(99 102 241 / 0.25), 0 12px 32px -12px rgb(99 102 241 / 0.45)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(120deg, #4f46e5 0%, #7c3aed 45%, #c026d3 100%)",
        "hero-glow": "radial-gradient(900px 380px at 12% -10%, rgba(124,58,237,0.18), transparent 60%), radial-gradient(700px 360px at 100% 0%, rgba(217,70,239,0.14), transparent 55%)",
      },
      borderRadius: { "4xl": "2rem" },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};

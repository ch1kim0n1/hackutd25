import {heroui} from "@heroui/theme"

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    './src/layouts/**/*.{js,ts,jsx,tsx,mdx}',
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  darkMode: "class",
  plugins: [
    heroui({
      themes: {
        light: {
          colors: {
            default: {
              50: "#fafafa",
              100: "#f2f2f3",
              200: "#ebebec",
              300: "#e3e3e6",
              400: "#dcdcdf",
              500: "#d4d4d8",
              600: "#afafb2",
              700: "#8a8a8c",
              800: "#656567",
              900: "#404041",
              foreground: "#000",
              DEFAULT: "#d4d4d8"
            },
            primary: {
              50: "#fdf8e7",
              100: "#fbeec5",
              200: "#f8e3a3",
              300: "#f5d982",
              400: "#f3cf60",
              500: "#f0c53e",
              600: "#c6a333",
              700: "#9c8028",
              800: "#725e1d",
              900: "#483b13",
              foreground: "#000",
              DEFAULT: "#f0c53e"
            },
            secondary: {
              50: "#fdede5",
              100: "#fad4c0",
              200: "#f6bb9b",
              300: "#f3a277",
              400: "#f08952",
              500: "#ed702d",
              600: "#c45c25",
              700: "#9a491d",
              800: "#713515",
              900: "#47220e",
              foreground: "#000",
              DEFAULT: "#ed702d"
            },
            success: {
              50: "#e0efe6",
              100: "#b5d7c4",
              200: "#8ac0a1",
              300: "#5ea97f",
              400: "#33925c",
              500: "#087b3a",
              600: "#076530",
              700: "#055026",
              800: "#043a1c",
              900: "#022511",
              foreground: "#fff",
              DEFAULT: "#087b3a"
            },
            warning: {
              50: "#fbf4e9",
              100: "#f5e5ca",
              200: "#f0d5aa",
              300: "#eac68b",
              400: "#e5b66c",
              500: "#dfa74d",
              600: "#b88a40",
              700: "#916d32",
              800: "#6a4f25",
              900: "#433217",
              foreground: "#000",
              DEFAULT: "#dfa74d"
            },
            danger: {
              50: "#f0e1e3",
              100: "#dab7bc",
              200: "#c48d95",
              300: "#ae636e",
              400: "#993947",
              500: "#830f20",
              600: "#6c0c1a",
              700: "#550a15",
              800: "#3e070f",
              900: "#27050a",
              foreground: "#fff",
              DEFAULT: "#830f20"
            },
            background: "#000000",
            foreground: "#000000",
            content1: {
              DEFAULT: "#ffffff",
              foreground: "#000"
            },
            content2: {
              DEFAULT: "#f4f4f5",
              foreground: "#000"
            },
            content3: {
              DEFAULT: "#e4e4e7",
              foreground: "#000"
            },
            content4: {
              DEFAULT: "#d4d4d8",
              foreground: "#000"
            },
            focus: "#f0c53e",
            overlay: "#000000"
          }
        },
        dark: {
          colors: {
            default: {
              50: "#05050c",
              100: "#090918",
              200: "#0e0e25",
              300: "#121231",
              400: "#17173d",
              500: "#454564",
              600: "#74748b",
              700: "#a2a2b1",
              800: "#d1d1d8",
              900: "#ffffff",
              foreground: "#fff",
              DEFAULT: "#17173d"
            },
            primary: {
              50: "#483b13",
              100: "#725e1d",
              200: "#9c8028",
              300: "#c6a333",
              400: "#f0c53e",
              500: "#f3cf60",
              600: "#f5d982",
              700: "#f8e3a3",
              800: "#fbeec5",
              900: "#fdf8e7",
              foreground: "#000",
              DEFAULT: "#f0c53e"
            },
            secondary: {
              50: "#47220e",
              100: "#713515",
              200: "#9a491d",
              300: "#c45c25",
              400: "#ed702d",
              500: "#f08952",
              600: "#f3a277",
              700: "#f6bb9b",
              800: "#fad4c0",
              900: "#fdede5",
              foreground: "#000",
              DEFAULT: "#ed702d"
            },
            success: {
              50: "#022511",
              100: "#043a1c",
              200: "#055026",
              300: "#076530",
              400: "#087b3a",
              500: "#33925c",
              600: "#5ea97f",
              700: "#8ac0a1",
              800: "#b5d7c4",
              900: "#e0efe6",
              foreground: "#fff",
              DEFAULT: "#087b3a"
            },
            warning: {
              50: "#433217",
              100: "#6a4f25",
              200: "#916d32",
              300: "#b88a40",
              400: "#dfa74d",
              500: "#e5b66c",
              600: "#eac68b",
              700: "#f0d5aa",
              800: "#f5e5ca",
              900: "#fbf4e9",
              foreground: "#000",
              DEFAULT: "#dfa74d"
            },
            danger: {
              50: "#27050a",
              100: "#3e070f",
              200: "#550a15",
              300: "#6c0c1a",
              400: "#830f20",
              500: "#993947",
              600: "#ae636e",
              700: "#c48d95",
              800: "#dab7bc",
              900: "#f0e1e3",
              foreground: "#fff",
              DEFAULT: "#830f20"
            },
            background: "#000000",
            foreground: "#ffffff",
            content1: {
              DEFAULT: "#111114",
              foreground: "#fff"
            },
            content2: {
              DEFAULT: "#141417",
              foreground: "#fff"
            },
            content3: {
              DEFAULT: "#3f3f46",
              foreground: "#fff"
            },
            content4: {
              DEFAULT: "#52525b",
              foreground: "#fff"
            },
            focus: "#f0c53e",
            overlay: "#ffffff"
          }
        }
      },
      layout: {
        disabledOpacity: "0.5"
      }
    })
  ],
}

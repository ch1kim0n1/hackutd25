# Electron + React (Vite) Starter

A tiny boilerplate to get you hacking with Electron + React powered by Vite.

## Quickstart

```bash
# 1) Install deps
npm i

# 2) Run in development (Vite + Electron, with HMR)
npm run dev

# 3) Package a distributable app
npm run build
```

### Notes

- The Electron main process is in `electron/main.js` and uses a secure `preload.js` bridge.
- In dev, Electron loads `http://localhost:5173`. In production, it loads the built `dist/index.html`.
- IPC example: the renderer calls `window.api.ping()` which resolves to `'pong from main'`.


 "default": {           "50": "#fafafa",           "100": "#f2f2f3",           "200": "#ebebec",           "300": "#e3e3e6",           "400": "#dcdcdf",           "500": "#d4d4d8",           "600": "#afafb2",           "700": "#8a8a8c",           "800": "#656567",           "900": "#404041",           "foreground": "#000",           "DEFAULT": "#d4d4d8"         }
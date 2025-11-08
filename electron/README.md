# Electron

This directory contains the source code for the Electron main process.

**Files:**
- `main.js`: The main entry point for the Electron application. It creates the browser window and handles system events.
- `preload.js`: A script that runs before the web page is loaded into the browser window. It has access to both DOM APIs and a limited set of Node.js APIs.

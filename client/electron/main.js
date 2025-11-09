import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// ESM doesn't provide __dirname/__filename by default. Create them
// from import.meta.url so path.join(...) works the same as in CJS.
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let win

const createWindow = () => {
  const isDev = !app.isPackaged

  win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js')
    }
  })

  if (isDev) {
    const devServerURL = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173'
    win.loadURL(devServerURL)
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    const indexPath = path.join(__dirname, '..', 'dist', 'index.html')
    win.loadFile(indexPath)
  }
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
}).catch((err) => {
  // Catch unexpected errors during startup to avoid unhandled promise rejections
  console.error('Failed during app.whenReady():', err)
})

// Graceful quit on all platforms
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

// Simple IPC example
ipcMain.handle('ping', async () => {
  return 'pong from main'
})

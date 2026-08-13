# Technical Stack – Folder Notes App

**Purpose:** Detailed breakdown of every technology choice, why it was selected, and how it works  
**Audience:** Developers and Cline (for accurate code generation)  
**Date:** 2026-08-13

---

## Table of Contents

1. [Core Stack](#core-stack)
2. [Production Dependencies](#production-dependencies)
3. [Development Dependencies](#development-dependencies)
4. [Why These Choices?](#why-these-choices)
5. [Alternative Stack Comparison](#alternative-stack-comparison)
6. [Installation & Configuration](#installation--configuration)
7. [Folder Structure & Module Resolution](#folder-structure--module-resolution)

---

## Core Stack

### Electron 30+
**What:** Native desktop application framework  
**Version:** `^30.0.0` (latest stable)  
**Purpose:** Cross-platform window management, file dialogs, app lifecycle

**Key APIs Used:**
```javascript
// Create window
const { BrowserWindow } = require('electron');
const mainWindow = new BrowserWindow({...});

// File picker
const { dialog } = require('electron');
const { filePaths } = await dialog.showOpenDialog(mainWindow, {
  properties: ['openDirectory']
});

// IPC communication
const { ipcMain } = require('electron');
ipcMain.handle('get-note', async (event, path) => {...});
```

**Why Electron?**
- Mature ecosystem (used by Discord, Slack, VSCode)
- Excellent documentation and SO support
- Large training data → AI code generation is reliable
- Native file system access + file dialogs
- Cross-platform: single codebase runs on Win/Mac/Linux
- Built-in auto-update capability (Phase 2)

---

### React 18+
**What:** UI library for building interactive components  
**Version:** `^18.2.0`  
**Purpose:** Component-based UI, state management, efficient re-renders

**Key Patterns Used:**
```javascript
// Functional component with hooks
function NoteDisplay({ folderPath }) {
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (!folderPath) return;
    setLoading(true);
    window.electronAPI.getNoteByPath(folderPath)
      .then(setNote)
      .finally(() => setLoading(false));
  }, [folderPath]);
  
  return <div>{loading ? 'Loading...' : note?.content}</div>;
}
```

**Why React?**
- Declarative UI (easier to reason about)
- Component reusability (FolderPicker, NoteDisplay, NoteForm)
- Built-in state management (`useState`, `useContext`)
- Virtual DOM (efficient updates, no manual DOM manipulation)
- Massive community and training data for AI

**React Hooks Used:**
- `useState` – Local component state
- `useEffect` – Side effects (IPC calls, subscriptions)
- `useCallback` – Memoized callbacks to prevent re-renders
- `useRef` – Direct DOM access (if needed)

---

### SQLite + better-sqlite3
**What:** Lightweight, file-based relational database  
**Version:** `sqlite3@^5.1.6`, `better-sqlite3@^9.0.0`  
**Purpose:** Persistent storage of notes

**Database Schema:**
```sql
CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  folderPath TEXT UNIQUE NOT NULL,
  content TEXT DEFAULT '',
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key CRUD Operations:**
```javascript
const Database = require('better-sqlite3');
const db = new Database(dbPath);

// Create
const stmt = db.prepare(`
  INSERT INTO notes (id, folderPath, content, createdAt, updatedAt)
  VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
`);
stmt.run(uuid(), folderPath, content);

// Read
const getStmt = db.prepare('SELECT * FROM notes WHERE folderPath = ?');
const note = getStmt.get(folderPath);

// Update
const updateStmt = db.prepare(`
  UPDATE notes SET content = ?, updatedAt = CURRENT_TIMESTAMP
  WHERE id = ?
`);
updateStmt.run(content, id);

// Delete
const deleteStmt = db.prepare('DELETE FROM notes WHERE id = ?');
deleteStmt.run(id);
```

**Why SQLite?**
- **No server needed** – File-based, embedded
- **Cross-platform** – Works identically on Win/Mac/Linux
- **Small footprint** – Database file is ~400 KB for 1,000 notes
- **ACID compliant** – Data integrity guaranteed
- **better-sqlite3** – Fastest Node.js SQLite binding (synchronous API is cleaner for Electron)
- **No learning curve** – Standard SQL syntax

**Database Path:**
```javascript
// Cross-platform user config directory
const dbPath = path.join(app.getPath('userData'), 'notes.db');
// Windows: C:\Users\Username\AppData\Roaming\Folder Notes\notes.db
// macOS: ~/Library/Application Support/Folder Notes/notes.db
// Linux: ~/.config/Folder Notes/notes.db
```

---

### Vite 5+
**What:** Fast bundler and development server  
**Version:** `^5.0.0`  
**Purpose:** Bundle React code for Electron renderer process

**Config (vite.config.js):**
```javascript
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist/renderer',
    target: 'esnext'
  }
});
```

**Why Vite?**
- **Fast HMR** – Changes reflect instantly (dev experience)
- **Zero-config for React** – Plugin handles JSX, CSS modules
- **Small production bundles** – Only necessary code included
- **ESM by default** – Modern module system
- **Great for Electron** – Works seamlessly with Electron's renderer process

**Dev Workflow:**
```bash
npm run dev  # Starts Vite dev server + launches Electron
            # Changes to React code hot-reload
```

---

## Production Dependencies

### package.json - Dependencies Section

```json
{
  "dependencies": {
    "electron": "^30.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "better-sqlite3": "^9.0.0",
    "uuid": "^9.0.0"
  }
}
```

### uuid
**What:** Generate unique identifiers  
**Version:** `^9.0.0`  
**Usage:** Generate note IDs

```javascript
const { v4: uuidv4 } = require('uuid');
const noteId = uuidv4();  // "550e8400-e29b-41d4-a716-446655440000"
```

**Why?**
- Unique IDs are needed for note records
- UUID v4 is collision-resistant and non-sequential
- Lightweight library (~5 KB)

---

## Development Dependencies

### package.json - DevDependencies Section

```json
{
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "electron-builder": "^24.6.0",
    "eslint": "^8.50.0",
    "prettier": "^3.0.0"
  }
}
```

### @vitejs/plugin-react
**Purpose:** Vite plugin for React support (JSX, Fast Refresh)

### electron-builder
**Purpose:** Package Electron app for distribution (`.exe`, `.dmg`, `.AppImage`)

**Config (electron-builder.yml):**
```yaml
appId: "com.foldernotesapp"
productName: "Folder Notes"
directories:
  buildResources: "assets"
  output: "dist/builder"
files:
  - "dist/**/*"
  - "node_modules/**/*"
```

### ESLint + Prettier
**Purpose:** Code quality and formatting

**Config (.eslintrc.json):**
```json
{
  "env": { "browser": true, "node": true, "es2021": true },
  "extends": ["eslint:recommended", "react-app"],
  "rules": { "no-unused-vars": "warn" }
}
```

---

## Why These Choices?

### Electron vs. Tauri vs. NW.js

| Feature | Electron | Tauri | NW.js |
|---------|----------|-------|-------|
| **Size** | ~150 MB | ~50 MB | ~200 MB |
| **Memory** | ~100 MB baseline | ~50 MB | ~150 MB |
| **Maturity** | Very mature | Growing | Mature |
| **Documentation** | Excellent | Good | Good |
| **AI Training Data** | Massive | Growing | Limited |
| **Native APIs** | Full | Full | Full |
| **Best For** | Production apps | Lightweight apps | Legacy |
| **Complexity** | Moderate | Moderate | Higher |

**Electron chosen because:**
- Massive training data → Cline generates better code
- Mature ecosystem → fewer bugs/gotchas
- Excellent documentation → easier debugging
- Large community → SO support abundant
- App size acceptable for this use case

---

### React vs. Vue vs. Svelte

| Feature | React | Vue | Svelte |
|---------|-------|-----|--------|
| **Learning Curve** | Moderate | Easy | Easy |
| **State Management** | Built-in (hooks) | Built-in | Built-in |
| **Ecosystem** | Massive | Good | Growing |
| **AI Training Data** | Excellent | Good | Limited |
| **Electron Integration** | Excellent | Good | Limited |
| **Best For** | Large apps, teams | Quick projects | Small apps |

**React chosen because:**
- Largest training data → Cline reliability
- Hooks are sufficient for MVP (no Redux needed)
- Unmatched ecosystem
- Electron + React is industry standard (Slack, VSCode, Discord use it)

---

### SQLite vs. PostgreSQL vs. Firebase

| Feature | SQLite | PostgreSQL | Firebase |
|---------|--------|------------|----------|
| **Setup** | File-based, zero setup | Server needed | Cloud API |
| **Learning** | Easy | Moderate | Moderate |
| **Scalability** | Single machine | Scalable | Scalable |
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Cost** | Free | Free | Paid (after free tier) |
| **Best For** | Local apps | Server-based apps | Cloud apps |

**SQLite chosen because:**
- This is a local-first app (no cloud required)
- Zero setup (no server to manage)
- Fast for <10K records
- Suitable for offline-first workflow
- better-sqlite3 is fastest Node.js binding

---

### Vite vs. Webpack vs. Parcel

| Feature | Vite | Webpack | Parcel |
|---------|------|---------|--------|
| **Dev Speed** | ⚡ Fast | Slow | Fast |
| **Config** | Minimal | Complex | Minimal |
| **Customization** | Good | Excellent | Limited |
| **Build Size** | Small | Medium | Medium |
| **Best For** | Fast dev experience | Complex apps | Quick projects |

**Vite chosen because:**
- Instant HMR (changes reflect immediately)
- Zero-config for React
- Production builds are optimized
- Fast development workflow

---

## Alternative Stack Comparison

If you wanted to use **different technologies**, here's how they'd compare:

### Alternative 1: Electron + Vue + SQLite
```json
{
  "dependencies": {
    "electron": "^30.0.0",
    "vue": "^3.3.0",
    "better-sqlite3": "^9.0.0"
  }
}
```
**Pros:** Simpler Vue syntax, easier learning curve  
**Cons:** Smaller ecosystem, less Cline training data

### Alternative 2: Tauri + React + SQLite
```json
{
  "dependencies": {
    "@tauri-apps/api": "^1.5.0",
    "react": "^18.2.0",
    "@tauri-apps/plugin-sql": "^1.0.0"
  }
}
```
**Pros:** Smaller app size (~50 MB vs 150 MB)  
**Cons:** Newer technology, fewer resources, harder debugging

### Alternative 3: NW.js + Vue + MongoDB
```json
{
  "dependencies": {
    "nw": "^0.78.0",
    "vue": "^3.3.0",
    "mongoose": "^7.0.0"
  }
}
```
**Pros:** None significant for this project  
**Cons:** Outdated, steep learning curve, overkill database

### Alternative 4: Electron + Preact + IndexedDB
```json
{
  "dependencies": {
    "electron": "^30.0.0",
    "preact": "^10.18.0",
    "dexie": "^3.2.0"
  }
}
```
**Pros:** Lightweight (Preact ~3 KB vs React ~40 KB)  
**Cons:** Less Cline training data for Preact, IndexedDB has size limits

---

**Recommendation:** Stick with Electron + React + SQLite. It's the sweet spot for this project.

---

## Installation & Configuration

### Step 1: Initialize Node Project

```bash
npm init -y
npm install electron@^30.0.0 react@^18.2.0 react-dom@^18.2.0 better-sqlite3@^9.0.0 uuid@^9.0.0
npm install --save-dev vite@^5.0.0 @vitejs/plugin-react@^4.2.0 electron-builder@^24.6.0
```

### Step 2: Create Folder Structure

```bash
mkdir -p src/main src/renderer src/renderer/components public
touch src/main/main.js src/renderer/App.jsx src/renderer/index.jsx vite.config.js electron-builder.yml
```

### Step 3: package.json Scripts

```json
{
  "scripts": {
    "dev": "vite & wait $! && electron .",
    "build": "vite build && electron-builder",
    "build:win": "vite build && electron-builder --win",
    "build:mac": "vite build && electron-builder --mac",
    "build:linux": "vite build && electron-builder --linux"
  },
  "main": "dist/main/main.js",
  "homepage": "./"
}
```

### Step 4: Vite Config

```javascript
// vite.config.js
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist/renderer',
    target: 'esnext'
  },
  server: {
    port: 5173,
    middlewareMode: false
  }
});
```

### Step 5: Electron Main Process

```javascript
// src/main/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

app.on('ready', () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  const isDev = process.env.NODE_ENV === 'development';
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webDevTools.openDevTools();
  } else {
    mainWindow.loadFile('dist/renderer/index.html');
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
```

---

## Folder Structure & Module Resolution

### Directory Tree

```
folder-notes-app/
│
├── src/
│   ├── main/                          # Electron main process
│   │   ├── main.js                    # App entry point
│   │   ├── database.js                # SQLite CRUD
│   │   └── preload.js                 # IPC bridge (security)
│   │
│   ├── renderer/                      # React / UI
│   │   ├── index.jsx                  # React entry
│   │   ├── App.jsx                    # Root component
│   │   ├── App.css
│   │   └── components/
│   │       ├── FolderPicker.jsx
│   │       ├── NoteDisplay.jsx
│   │       ├── NoteForm.jsx
│   │       └── components.css
│   │
│   └── shared/                        # Shared utilities
│       └── constants.js               # Shared config
│
├── dist/                              # Build output
│   ├── main/                          # Bundled main process
│   └── renderer/                      # Bundled React app
│
├── public/                            # Static assets
│   └── icon.png                       # App icon
│
├── node_modules/                      # Installed packages
├── package.json                       # Dependencies + scripts
├── vite.config.js                     # Vite configuration
├── electron-builder.yml               # Build config
├── .gitignore
└── README.md
```

### Module Resolution

**From React component to main process:**
```javascript
// src/renderer/App.jsx
const note = await window.electronAPI.getNoteByPath(folderPath);
// ↓ IPC call bridges to main process
// src/main/main.js (ipcMain.handle)
```

**From main process to database:**
```javascript
// src/main/database.js
const note = db.prepare('SELECT * FROM notes WHERE folderPath = ?').get(folderPath);
// ↓ Query database file
// ~/.config/Folder Notes/notes.db
```

---

## Performance Considerations

### Memory Usage

- **Electron base:** ~50–100 MB
- **React app:** ~20–30 MB
- **SQLite in memory:** <5 MB (unless loading entire DB into RAM)
- **Total baseline:** ~100–150 MB (acceptable for desktop app)

### Startup Time

- **Cold start:** ~2–3 seconds (Electron + React + SQLite init)
- **Warm start:** <1 second (cached)
- **Note display:** <200ms (SQLite query)
- **Note save:** <100ms (SQLite insert/update)

### Database Performance

- **Read (getNoteByPath):** ~1ms (indexed query)
- **Write (createNote):** ~2ms (insert + transaction)
- **Delete:** ~1ms
- **Scan all notes:** ~5–10ms for 1,000+ notes

---

## Security Considerations

### IPC Isolation

Use `preload.js` to expose only safe APIs:

```javascript
// src/main/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getNoteByPath: (path) => ipcRenderer.invoke('get-note-by-path', path),
  createNote: (path, content) => ipcRenderer.invoke('create-note', path, content),
  // Only expose safe functions
});
```

**Why?** Prevents malicious code injection from compromised renderer process.

### Database Validation

Always validate user input before database operations:

```javascript
function createNote(folderPath, content) {
  if (!folderPath || typeof folderPath !== 'string') {
    throw new Error('Invalid folder path');
  }
  if (typeof content !== 'string') {
    throw new Error('Invalid content');
  }
  // Safe to use in query
}
```

---

## Dependency Update Strategy

### Critical Updates (Update Immediately)
- Security patches (Electron, Node.js)
- Bug fixes in better-sqlite3 or React

### Minor Updates (Update Monthly)
- New features in Vite, electron-builder
- Performance improvements

### Major Updates (Update with Caution)
- React major version
- Electron major version
- Better-sqlite3 major version
- Test thoroughly before updating

**Command to check for updates:**
```bash
npm outdated  # Shows available updates
npm update    # Updates minor/patch versions
npm install electron@latest  # Major version update (manual)
```

---

## Troubleshooting Dependencies

### Issue: better-sqlite3 Build Fails

**Symptom:** `npm install` fails with "binding.gyp" error

**Solution:**
```bash
npm install --build-from-source better-sqlite3
# Or use pre-built binary:
npm install better-sqlite3@9.0.0
```

### Issue: Vite Dev Server Not Starting

**Symptom:** `npm run dev` hangs

**Solution:**
```bash
rm -rf node_modules/.vite
npm run dev -- --force
```

### Issue: Electron Can't Find Preload Script

**Symptom:** "ReferenceError: electronAPI is not defined"

**Solution:**
- Verify `preload.js` path in `BrowserWindow` config
- Check preload.js exports using `contextBridge.exposeInMainWorld`
- Restart dev server

---

## Further Reading

- Electron Docs: https://www.electronjs.org/docs
- React Documentation: https://react.dev
- Vite Guide: https://vitejs.dev/guide/
- SQLite Best Practices: https://www.sqlite.org/bestprac.html
- better-sqlite3 Docs: https://github.com/WiseLibs/better-sqlite3

---

**End of Tech Stack Document**

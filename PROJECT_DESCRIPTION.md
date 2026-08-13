# Folder Notes – Project Description

**For:** Project creation, team documentation, GitHub README, or personal reference  
**Last Updated:** 2026-08-13  
**Status:** Pre-Development (Planning Phase)

---

## One-Liner

A lightweight, always-accessible desktop app that displays a persistent note in the bottom-right corner, uniquely associated with each folder you navigate to.

---

## What Are You Trying to Achieve?

### Problem

Users often switch between multiple folders while working (project folders, downloads, documents, media libraries, etc.). Each folder has its own context:
- "Projects/WebApp" might need: "TODO: Fix login bug, run tests before commit"
- "Downloads/Films" might need: "Watch: Oppenheimer, The Matrix, Inception"
- "Music/Playlists" might need: "Create: Synthwave mix, add Carpenter Brut, Perturbator"

Managing these context-specific notes across multiple applications (Notes.app, Obsidian, Notion, etc.) is friction-heavy. There's no single place to see "what do I need to do/remember for this folder?"

### Solution

**Folder Notes** is a persistent desktop widget that:
- Ties a single note to each folder
- Displays that note automatically when you navigate to the folder
- Never mixes notes from different folders
- Allows quick create, read, update, delete (CRUD) operations
- Works offline with local storage

Result: Context-aware note access with zero friction.

---

## Key Features (MVP)

### Core
1. **Folder Selection**
   - User clicks "Select Folder" button
   - Native file picker dialog opens
   - User selects a folder
   - App remembers the selection

2. **Note Display**
   - Note tied to selected folder displays in bottom-right corner
   - Fixed, persistent widget (doesn't move or disappear)
   - If no note exists, shows "No note for this folder"
   - Scrollable if note content is long

3. **Note CRUD**
   - **Create:** Click "New Note" button → modal form opens → type note → save
   - **Read:** Note displays automatically in widget
   - **Update:** Click "Edit" button → modal opens with existing content → edit → save
   - **Delete:** Click "Delete" button → confirmation → note removed

4. **No Note Mixing**
   - "Films" folder's note never displays when viewing "Music" folder
   - Each folder has its own isolated note
   - Switching folders switches notes instantly

5. **Persistence**
   - Notes saved to local SQLite database
   - Last-selected folder remembered across app restarts
   - No cloud, no sync, no account needed

---

## Target User

- **Who:** Desktop users who work with multiple folders and need context-specific notes
- **Platforms:** Windows, macOS, Linux
- **Use Case:** Developers, researchers, creatives, anyone juggling multiple project directories
- **Skill Level:** Any (no special technical knowledge required)

---

## Technical Specs (Under the Hood)

### Stack
- **Frontend:** React 18+ (UI components)
- **Desktop Framework:** Electron (cross-platform native desktop app)
- **Backend:** Node.js (Electron main process)
- **Database:** SQLite with `better-sqlite3` (local, lightweight)
- **Bundler:** Vite (fast development, optimized builds)
- **Styling:** Vanilla CSS (no framework bloat)

### Architecture
- **Presentation Layer:** React components (FolderPicker, NoteDisplay, NoteForm)
- **Application Layer:** Electron main process (IPC bridge, file dialogs, app lifecycle)
- **Data Layer:** SQLite CRUD operations (createNote, getNote, updateNote, deleteNote)
- **Storage:** SQLite database file (~/.config/folder-notes/notes.db)

### Data Model
```sql
CREATE TABLE notes (
  id TEXT PRIMARY KEY,              -- Unique ID (UUID)
  folderPath TEXT UNIQUE NOT NULL,  -- Absolute path to folder
  content TEXT DEFAULT '',          -- Note content (plain text)
  createdAt DATETIME,               -- Creation timestamp
  updatedAt DATETIME                -- Last updated timestamp
);
```

### IPC Communication
- **Renderer → Main:** `window.electronAPI.getNoteByPath(folderPath)`
- **Main → Renderer:** Returns note object or null
- **Main Process:** Handles file dialogs, database queries, app lifecycle

---

## Workflow Example

**User Scenario:**

1. User opens Folder Notes app
2. App opens blank (no folder selected yet)
3. User clicks "Select Folder" button
4. Native file picker opens → user navigates to `/Users/jane/Projects/WebApp` → clicks "Open"
5. App displays: "Current folder: /Users/jane/Projects/WebApp"
6. Widget shows: "No note for this folder"
7. User clicks "New Note" button
8. Modal form opens (empty textarea)
9. User types: "TODO: Fix login bug, run tests before commit, update dependencies"
10. User clicks "Save"
11. Note saves to SQLite
12. Widget displays the note
13. Later, user navigates to `/Users/jane/Downloads/Films`
14. User clicks "Select Folder" and picks the Films folder
15. App displays: "Current folder: /Users/jane/Downloads/Films"
16. Widget displays: "Watch: Oppenheimer, The Matrix, Inception"
17. When user returns to WebApp, the WebApp note reappears

---

## Non-Features (Out of Scope for MVP)

- ❌ **Cloud sync** – All data is local
- ❌ **Rich text editing** – Plain text only
- ❌ **Tags or categories** – 1 note per folder only
- ❌ **Multi-device sync** – Single-machine only
- ❌ **Markdown rendering** – Plain text display
- ❌ **Collaborative editing** – Single-user only
- ❌ **File watcher** – Manual folder selection only (no passive monitoring)

---

## Success Criteria

The project is successful when:

1. ✅ User can select a folder via native file picker
2. ✅ User can create a note for that folder
3. ✅ Note persists in SQLite (survives app restart)
4. ✅ Note displays in bottom-right corner of app window
5. ✅ User can edit the note
6. ✅ User can delete the note
7. ✅ Switching to a different folder displays that folder's note
8. ✅ No notes mix (Films note never appears in Music folder context)
9. ✅ App runs without crashes on Windows, macOS, and Linux
10. ✅ UI is clean, minimal, and non-intrusive

---

## Project Phases

### Phase 1: MVP (Estimated 4–6 hours of AI prompting)

**Goal:** Fully functional, single-folder note management

**Deliverables:**
- [ ] Electron + React + Vite project initialized
- [ ] SQLite database layer with CRUD
- [ ] Folder picker component
- [ ] Note display widget (bottom-right)
- [ ] Note form (create/edit/delete)
- [ ] End-to-end integration (folder selection → note display)
- [ ] App packaging for one platform (test on Windows/macOS/Linux)

**Definition of Done:**
- User can follow the workflow example above without errors
- No note mixing observed
- Notes persist across restarts
- No console errors

### Phase 2: Polish (Estimated 2–3 hours)

**Goal:** Professional UI, improved UX

**Deliverables:**
- [ ] Keyboard shortcuts (Ctrl+Shift+N for new note, Ctrl+Shift+F for folder picker)
- [ ] UI refinements (dark/light theme toggle, timestamps, note truncation)
- [ ] Export/import functionality (JSON backup of all notes)
- [ ] Search/filter (find notes by folder name or content)
- [ ] Recently used folders dropdown

**Definition of Done:**
- Keyboard shortcuts work reliably
- Export/import tested and working
- UI looks professional and polished

### Phase 3: Advanced (Estimated 5+ hours, optional)

**Goal:** Extended functionality and multi-device support (if needed)

**Deliverables:**
- [ ] Rich text editing (markdown support or WYSIWYG)
- [ ] Note templates (pre-made formats)
- [ ] Tags/labels for notes
- [ ] Cloud sync option (Dropbox, OneDrive, etc.)
- [ ] Multi-window support
- [ ] Note sharing/export to different formats

**Definition of Done:**
- All Phase 3 features tested and working
- No regressions from MVP

---

## Development Approach

### AI-Assisted Development Using Cline

**Why Cline?**
- Generates 500+ lines of code per turn
- Understands your project context
- Executes terminal commands (npm install, build, run)
- Learns from feedback and iterates

**Workflow:**
1. **Plan** – Ask Cline to design the feature
2. **Review** – Verify the plan makes sense
3. **Implement** – Cline writes the code
4. **Test** – Manual testing or automated checks
5. **Iterate** – Request refinements until it works

**No manual coding required.** Akhilesh reviews and prompts only.

### Session Structure

Each development session follows:
1. **Setup** (5 min) – Verify Cline API key, model selection
2. **Prompt** (2–5 min) – Write specific, detailed prompt
3. **Generation** (2–5 min) – Cline writes code, runs commands
4. **Review** (5–10 min) – Read output, check for errors
5. **Test** (10–15 min) – Run locally, verify behavior
6. **Iterate** (5–20 min) – Ask for refinements if needed

**Typical session duration:** 30 min – 2 hours

---

## Estimated Timeline

- **Phase 1 MVP:** 4–6 hours of prompting over 3–4 sessions
- **Phase 2 Polish:** 2–3 hours over 1–2 sessions
- **Phase 3 Advanced:** 5+ hours over 3–5 sessions (optional)

**Total (full app):** ~11–14 hours of Cline interaction

---

## File Structure (Final)

```
folder-notes-app/
├── public/
│   └── icon.png (512x512 app icon)
├── src/
│   ├── main/
│   │   ├── main.js (Electron entry point)
│   │   ├── database.js (SQLite CRUD)
│   │   └── preload.js (secure IPC bridge)
│   ├── renderer/
│   │   ├── App.jsx (React root, state management)
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── FolderPicker.jsx
│   │   │   ├── NoteDisplay.jsx
│   │   │   ├── NoteForm.jsx
│   │   │   └── components.css
│   │   └── index.jsx (React entry point)
│   └── shared/
│       └── constants.js (shared config)
├── .gitignore
├── package.json
├── vite.config.js
├── electron-builder.yml
├── README.md
└── docs/
    ├── ARCHITECTURE.md
    ├── SETUP.md
    └── ROADMAP.md
```

---

## Key Technologies Explained

### Electron
- Desktop framework used by Slack, Discord, VSCode
- Write code once, run on Windows/macOS/Linux
- Access to native file dialogs, window management, etc.

### React
- UI library for building interactive components
- Component-based architecture (FolderPicker, NoteDisplay, etc.)
- State management (useState, useContext)

### SQLite
- Lightweight, file-based database (no server needed)
- Perfect for local-only data
- ~400 KB database file for thousands of notes

### Vite
- Fast bundler and dev server
- Hot module replacement (code changes reflect instantly)
- Optimized production builds

---

## Assumptions & Constraints

### Assumptions
- User has Node.js 18+ installed
- User can use a code editor (VS Code, Cursor, JetBrains)
- User has an API key for AI prompting (OpenRouter, Claude API, etc.)
- Single user, single machine (no multi-user sync)

### Constraints
- **No cloud storage initially** (Phase 3 only)
- **No rich text initially** (Phase 3 only)
- **Single folder at a time** (app displays one folder's note)
- **Plain text only** (MVP)
- **No real-time sync** (manual app restart required if DB is edited externally)

---

## Known Limitations (Phase 1)

1. **Manual folder selection only** – App doesn't monitor file system passively
2. **Single-window app** – No multi-window support
3. **No search** – Can only view notes by folder selection
4. **No export initially** – All data stored in SQLite only
5. **Basic UI** – Minimal styling, no animations

---

## Success Metrics

### Functional
- 100% of MVP features working without crashes
- 0 note mixing errors
- Notes persist across restarts

### Performance
- App launches in <2 seconds
- Folder selection and note display <500ms
- No memory leaks (app doesn't consume >100MB RAM)

### User Experience
- New users can figure out the UI without documentation
- No confusing error messages
- Workflow from folder selection to note display is intuitive

---

## Next Steps

1. **Read FOLDER_NOTES_ARCHITECTURE.md** – Understand the technical design
2. **Read CLINE_SETUP.md** – Set up Cline with the right API provider
3. **Initialize project** – Run first Cline prompt to scaffold the app
4. **Build Phase 1** – Follow the prompting strategy to implement MVP
5. **Test thoroughly** – Manual testing after each component
6. **Ship** – Package the app for distribution (Phase 2+)

---

## Support & Resources

- **Electron Docs:** https://www.electronjs.org/docs
- **React Docs:** https://react.dev
- **SQLite Docs:** https://www.sqlite.org/docs.html
- **Vite Docs:** https://vitejs.dev
- **Cline Docs:** https://github.com/cline/cline

---

## License

[TBD – Choose one: MIT, Apache 2.0, GPL, Proprietary]

---

**End of Project Description**

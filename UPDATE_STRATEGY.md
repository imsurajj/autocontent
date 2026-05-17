# AutoContent Pro | Update & Distribution Strategy

This document outlines the architecture for "Over-The-Air" (OTA) updates for AutoContent Pro while maintaining a **Private GitHub Repository** and a friction-free user experience.

---

## 🟢 Approach 1: The "Wizard" (Major Updates)
*Best for: Major Python engine changes, new libraries, or security patches.*

### 1. Infrastructure
- **Server**: `imsuraj.pythonanywhere.com/api/v1/update`
- **Storage**: Direct Download Link (Dropbox, Google Drive, or Private Server).
- **Format**: `.exe` Installer (Wizard).

### 2. Workflow
1. **App Startup**: `app.py` sends a request to your server: `GET /version`.
2. **Detection**: Server returns `{ "version": "2.1.0", "url": "https://download.link/wizard.exe" }`.
3. **UI Trigger**: If local version < remote, a Geist-styled **"UPDATE READY"** button appears in the sidebar.
4. **The Wizard**: User clicks update -> App opens the browser to the direct download -> User runs the Installer.
5. **Auto-Overwrite**: The installer (Wizard) automatically replaces the old files.

---

## 🚀 Approach 2: The "Stealth Patch" (Recommended / Ultra-Lightweight)
*Best for: UI fixes, layout adjustments (alignments), and JS logic improvements.*

This is the "Air Update" you requested—it's faster, invisible, and doesn't require a re-install.

### 1. Architecture
Instead of bundling the `index.html` inside the `.exe`, we use a **Local Cache with Remote Sync**.

### 2. The Workflow
1. **Check**: `app.py` checks a small `patch_hash.txt` on your server.
2. **Download**: If the hash differs, the app silently downloads a new `index.html` (only ~30KB) to the user's `AppData` folder.
3. **Load**: The app always loads the latest patched file from `AppData`.
4. **Result**: You fix a CSS alignment on your server, and **instantly** all your users have the fix without downloading a new `.exe`.

---

## 🛠️ Implementation Roadmap

### Phase 1: The Version Gate (PythonAnywhere)
Create a simple endpoint that returns the current version. This allows you to control all users from one dashboard.

### Phase 2: Sidebar Integration
Add a dynamic update card to the `index.html` footer that only renders when `update_available == true`.

### Phase 3: The Download Bridge
Implement `webbrowser.open(download_url)` in `app.py` to bridge the gap between the desktop app and your private download source.

---

> [!TIP]
> **Why this is better:** By using your PythonAnywhere server as the middle-man, you never have to make your GitHub repo public. You have 100% control over who gets the update and when.

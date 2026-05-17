# 📦 Professional Distribution Guide

Follow these steps to generate, package, and distribute your compiled standalone desktop application with a professional installation wizard.

---

## 🔨 Step 1: Build the Standalone Engine (.exe)

First, compile your Python codebase into a clean, standalone background executable. Run this command inside your local terminal in the `d:\autocontent` directory:

```bash
pyinstaller --noconfirm --onefile --windowed --add-data "index.html;." app.py
```

### Why these flags?
*   `--onefile`: Compiles all code and libraries into a single file (`dist/app.exe`).
*   `--windowed`: Hides the default black terminal cmd window, launching only your high-end GUI workspace.
*   `--add-data "index.html;."`: Embeds your default HTML interface directly inside the executable, ensuring instant boots even when offline!

---

## 🎨 Step 2: Build the Professional Install Wizard (Inno Setup)

To package your app into a branded Windows Installation Wizard that handles desktop shortcuts, license keys, and standard software directories:

1.  **Open Inno Setup** on your computer.
2.  **Load the Script**: Open the custom script **`installer_script.iss`** located in your workspace.
3.  **Compile**: Click the **Build ──> Compile** button (or press `Ctrl + F9`).
4.  **The Result**: Your final setup wizard file **`AutoContent_Pro_v2.0.0_Setup.exe`** will be generated inside the `Output/` folder!

### ✨ Feature Spotlight: Wizard-Level Pre-Activation
*   During installation, the wizard displays a **"License Activation"** screen.
*   It prompts the user to enter their **Activation Key** (which you created in your `/admin` web dashboard!).
*   The wizard verifies that a key is entered (verifying format length >= 8) and **automatically writes the key** into the user's local `license.key` settings file during installation.
*   **Zero Friction**: When your customer clicks the desktop shortcut to launch the app for the very first time, it is **already fully pre-activated** and instantly queries your cloud server to log in!

---

## 🚀 Live Updates are 100% Automated!

Once your customer has used your Inno Setup wizard to install the app once, **you never need to build or compile installation wizards to deliver updates!** The running app handles everything over-the-air:

### 1. UI & Visual Layout Patches (Stealth Mode)
*   **What to do**: Edit your local `index.html` file and upload it to your PythonAnywhere `mysite/` directory.
*   **User Action**: **None**. Their running desktop application silently detects the new design hash, downloads the ~30KB patch on startup, and updates the layout immediately.

### 2. Major Native Code Upgrades (In-App Updater)
*   **What to do**:
    1. Compile a new executable locally using the **PyInstaller** command in Step 1.
    2. Upload the new `app.exe` to PythonAnywhere inside the `mysite/` folder as `autocontent_pro.exe`.
    3. Increase the target version inside your `license_server.py` to `2.1.0` (or higher).
*   **User Action**: An elegant **"Update Engine"** banner automatically appears in their sidebar. They click it once; the app silently downloads your new binary, terminates, overwrites itself on their computer in 2 seconds, and restarts fully updated!

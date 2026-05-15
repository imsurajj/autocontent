# 📦 Professional Distribution Guide

Follow these steps to create a **Professional Install Wizard** using your official branding.

## 1. Build the Engine (.exe)
Run this command to build the app with your official icon and bundle the logo image:

```bash
pyinstaller --noconsole --onefile --icon="image/logo.ico" --add-data "image/logo.png;image" --name "AutoContent_Ultimate" app.py
```

### Why these flags?
*   `--icon="image/logo.ico"`: Attaches your icon to the `.exe` file.
*   `--add-data "image/logo.png;image"`: Embeds your logo image inside the `.exe` so the app can display it.

## 2. Create the Professional Installer (Wizard)
1.  **Open Inno Setup.**
2.  **Open the Script:** Load `installer_script.iss`.
3.  **Compile:** Click the **Compile** button.
4.  **The Result:** Your final installer `AutoContent_Pro_Setup.exe` will be in the `Output/` folder.

## 🐙 Sharing on GitHub
Upload **ONLY** the `AutoContent_Pro_Setup.exe` to your GitHub Releases. 

---
**Note:** If you change your logo or icon in the `image/` folder, just rerun these two steps to update your installer.

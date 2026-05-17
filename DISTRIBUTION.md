# AutoContent Pro — Distribution, Installer & OTA Updates

This document is the authoritative distribution guide for AutoContent Pro. It covers packaging a one-time installer, a secure Over-The-Air (OTA) update strategy, signing, CI/CD automation, and testing steps so your users get a single, reliable install and seamless updates thereafter.

Contents
- Packaging the one-time installer
- Updater / launcher architecture (OTA)
- Manifest format and signing
- CI/CD release flow (build → sign → upload)
- Testing, rollback, and monitoring

---

## 1) One-time Installable EXE (Recommended UX)

Goal: ship a single installer that users run once to install the app. After that, an embedded launcher/updater keeps the app patched automatically.

Steps
- Build the distributable app binary (PyInstaller recommended for Python):
  - `pip install pyinstaller`
  - `pyinstaller --noconsole --onefile --icon=image/icon.ico app.py`
  - Take the produced `dist/app.exe` as the application binary.
- Create a professional installer with Inno Setup (recommended):
  - Use `installer.iss` to produce `AutoContent_Pro_Setup_vX.Y.exe`.
  - Installer should place a versioned folder (e.g., `C:\Program Files\AutoContent Pro\v1.0.0`) and write a small launcher/updater executable to a stable path.
  - Installer should register Start Menu / desktop shortcuts and an uninstall entry.

Important choices
- Install location: per-user (AppData) avoids UAC for updates; per-machine (Program Files) requires elevation for updates.
- Launcher vs. Service: prefer a launcher that runs at app start and checks updates. Use a service only if you need privileged background installs.

---

## 2) Updater / Launcher Architecture (OTA)

Purpose: allow the installed app to receive secure patches and notifications without re-running the full installer.

Design
- Launcher (small exe) starts first and does:
  1. Check signed manifest on server (HTTPS) for latest version.
  2. If update available, download artifact (full or delta) to a temp folder.
  3. Verify artifact checksum and signature.
  4. Apply update atomically (deploy to new version folder then switch symlink/shortcut or rename), keeping previous version for rollback.
  5. Launch the real app binary.
- Updater details:
  - Use delta patches (bsdiff/xdelta or Squirrel-style diffs) to minimize download sizes, or ship full replacements for simplicity.
  - Ensure updater can replace running files (use a two-step swap or a helper process that runs after app exits).

UX options
- Check-on-launch: simple — launcher checks and updates before starting app.
- Background updater: silently updates while app is closed; notifies user on next start.
- In-app prompt: notify and let user choose Install Now or Later.

---

## 3) Manifest Format & Signing (Security)

Keep a signed JSON manifest that the launcher validates before downloading or applying updates.

Minimal manifest example
```json
{
  "version": "1.2.3",
  "released": "2026-05-18T12:00:00Z",
  "notes": "Minor fixes and license flow improvements.",
  "files": [
    {"name":"app-v1.2.3.zip","url":"https://cdn.example.com/app-v1.2.3.zip","sha256":"...","size": 12345678}
  ],
  "signature": "(PKCS7 or detached signature)"
}
```

Signing rules
- Sign the manifest (PKCS7 or similar). Embed the public verification key in the launcher.
- Verify the manifest signature before trusting any URLs.
- Verify per-file SHA256 after download.

---

## 4) CI/CD — Build → Sign → Publish (recommended pipeline)

Pipeline outline
1. CI build job (Windows runner):
   - Run tests, static checks.
   - Build `app.exe` with PyInstaller.
2. Packaging job:
   - Create versioned artifact (zip or installer).
   - Optionally create delta patches vs previous releases.
3. Signing job:
   - Code-sign EXE/installer with Authenticode.
   - Sign manifest with your private key.
4. Publish job:
   - Upload artifacts and manifest to CDN or Appwrite Storage.
   - Update release metadata (GitHub Releases or internal tracker).

Notes
- Protect signing keys in secure vault (HashiCorp, Azure Key Vault, GitHub Secrets with restricted access).
- Automate changelog and release notes generation from commits or PRs.

---

## 5) Backwards Compatibility & Migration

- Keep old version folders until new version is verified (allow rollback).
- Updater should keep a small number of previous versions (1–2) to limit disk usage.
- If the update requires migrations, run migration steps in the updater with careful error handling.

---

## 6) Testing & Rollback

Critical tests
- Manifest validation: tampered manifest is rejected.
- Checksum validation: corrupted download fails.
- Delta patch test: apply patch on multiple older versions.
- Rollback test: simulate failed deploy and ensure previous version restores.
Perform these in CI with dedicated test VMs.

---

## 7) Windows-specific Notes

- Per-user install (AppData) avoids UAC elevation for updates — easiest UX.
- Per-machine install (Program Files) requires a privileged updater (service or elevation prompt) to update.
- Code-signing is essential to reduce false positives from AV and for user trust.

---

## 8) Minimal Quick-Start Choices (fastest to production)

If you need a minimal, production-ready approach quickly:
1. Package app with PyInstaller.
2. Create Inno Setup installer that installs:
   - `launcher.exe` (small updater/launcher), and
   - `app-vX.Y.Z\app.exe` (versioned folder).
3. Use Squirrel.Windows or a small custom updater in the launcher to apply updates.
4. Sign installer and launcher.
5. Host manifest + artifacts on CDN/Appwrite Storage.

---

## 9) Example checklist for a release
- Build and test locally ✅
- Create signed artifacts and manifest ✅
- Upload artifacts to CDN ✅
- Create release notes and publish ✅
- Monitor adoption and errors (telemetry) ✅

---

If you want, I can now:
- Produce an `updater` sequence diagram and minimal pseudo-code for the launcher, or
- Generate a CI job example (GitHub Actions) that builds, signs, and publishes the manifest and artifacts.

Which would you like next? (No code changes performed unless you ask.)

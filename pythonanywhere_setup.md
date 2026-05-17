# PythonAnywhere Setup Guide for AutoContent Pro Licensing

This guide walks you through deploying your licensing server to PythonAnywhere so your desktop application can verify keys, track hardware IDs, and prevent license sharing.

## Step 1: Create a PythonAnywhere Account
1. Go to [PythonAnywhere.com](https://www.pythonanywhere.com/) and click **Sign Up**.
2. Choose the **Create a Beginner account** (the free tier).
3. Fill in your details. Your username will become part of your server URL (e.g., `https://yourusername.pythonanywhere.com`).

## Step 2: Create a Flask Web App
1. Once logged in, go to the **Web** tab at the top right.
2. Click the large blue button: **Add a new web app**.
3. A prompt will appear asking for a domain. Click **Next** (it will default to `yourusername.pythonanywhere.com`).
4. Select the **Flask** web framework.
5. Select the latest available **Python 3.x** version (e.g., Python 3.10).
6. It will show a path for a new file like `/home/yourusername/mysite/flask_app.py`. Click **Next**.
7. Your web app is now created and running a "Hello World" page!

## Step 3: Upload Your Licensing Server Code
1. Go to the **Files** tab at the top right.
2. Under "Directories", click on the folder named **`mysite`**.
3. You will see the default `flask_app.py` file that was just created. **Delete it** (click the trash can icon next to it).
4. Click the **Upload a file** button.
5. Select the `license_server.py` file that is currently on your computer (inside your project folder).
6. Once uploaded, **rename the file** from `license_server.py` to `flask_app.py`. (PythonAnywhere specifically looks for a file named `flask_app.py` to run your site).

## Step 4: Restart the Server
1. Go back to the **Web** tab.
2. Click the big green **Reload yourusername.pythonanywhere.com** button at the top.
3. Your licensing server is now live!

## Step 5: Update Your Desktop App
1. Open your `app.py` file on your computer.
2. Go to approximately line 138.
3. Change the API URL to match your new PythonAnywhere account:
   ```python
   # Replace "yourusername" with your actual PythonAnywhere username!
   LICENSE_API_URL = "https://yourusername.pythonanywhere.com"
   ```

---

## How to Manage Your Licenses

You can now easily manage all your licenses directly from your web browser using these 4 URLs. **Make sure to replace `TEAM-A-1234` with the actual key you are managing!**

### 1. Add a New Key
Generate a new key for a user and track their name and license duration. You can add `?name=...` and `?duration=...` (in days) to the end of the URL.
`https://imsuraj.pythonanywhere.com/admin/add_key/TEAM-A-1234?name=John+Doe&duration=60`
*(Use a `+` instead of spaces for the name. You will see a message saying "Key added successfully". You can now give this key to your team member.)*

### 2. See All Keys & Statuses
Check who is active, who is revoked, and see their Hardware IDs:
`https://imsuraj.pythonanywhere.com/admin/list`
*(This will show you a nice JSON list of every key in your system).*

### 3. Revoke a Key (Block Access)
Instantly block a user from using the software:
`https://imsuraj.pythonanywhere.com/admin/revoke/TEAM-A-1234`
*(Changes status to Revoked. The user's app will immediately kick them out on their next startup).*

### 4. Re-Activate a Key
If you accidentally revoked someone, you can restore their access:
`https://imsuraj.pythonanywhere.com/admin/activate/TEAM-A-1234`

---

## 🚀 How to Publish UI/Frontend Updates (Stealth Patches)

The **Stealth Patch Engine** allows you to update your app's layout, styles, colors, and frontend features instantly without forcing users to download a new `.exe`.

### Step 1: Upload your index.html to PythonAnywhere
1. Make your UI changes in the local `index.html` file on your computer.
2. Log in to **PythonAnywhere** and go to the **Files** tab.
3. Open the `mysite` folder (where your `flask_app.py` is located).
4. Upload your updated `index.html` to this directory.

### Step 2: You're Done!
*   Unlike server-side code changes, **you do not need to reload your server** when updating `index.html`!
*   The Flask server dynamically calculates the SHA-256 checksum of `index.html` on every query.
*   On next startup, all user apps will detect the new checksum, silently download the updated layout (~30KB), and load the new interface immediately!

> **Security Note:** These endpoints are currently open for your convenience. Since this URL is private to you, it's generally safe, but keep your PythonAnywhere URL secret!

---

## 🛠️ Developer Release Checklist & Deployment Architecture

Use this checklist and architectural guide whenever you want to publish UI changes, update server features, or distribute new app engines.

> [!IMPORTANT]
> **Understanding File Target Deployments:**
> 1. **`index.html` (Frontend / UI)**: Uploaded to **PythonAnywhere**. Updates silently and directly in the user's app *without* any dialog (Stealth Patch).
> 2. **`license_server.py` (Backend Server)**: Uploaded to **PythonAnywhere** (renamed to `flask_app.py`). Runs the licensing API.
> 3. **`app.py` (Desktop Client Engine)**: **DO NOT** upload this to PythonAnywhere! PythonAnywhere does not run `app.py`. Since users run compiled `.exe` files locally on their PCs, any changes to `app.py` (like PDF rendering or local window rules) require compiling a new `.exe` locally and distributing the installer to users.

### 📂 Step 1: Push Changes to GitHub
Commit your local workspace and push it to your private repository (this saves your code and automates the PythonAnywhere sync):
```bash
git add .
git commit -m "feat: updated styles and silent update configurations"
git push origin main
```

### 🌐 Step 2: Sync to PythonAnywhere

Choose one of these two professional sync methods:

#### Option A: Fully Automated GitHub Webhook (Recommended - CI/CD)
This sets up a 100% automated pipeline. Every time you push to the `main` branch, GitHub automatically tells your server to run `git pull`, overwrite `flask_app.py`, and **instantly hot-reload your web application** without you ever needing to touch PythonAnywhere!

1. Go to your **GitHub Repository Settings** on your web browser.
2. Click on **Webhooks** in the left sidebar ──> click the **Add webhook** button.
3. Configure the following settings exactly:
   * **Payload URL**: `https://imsuraj.pythonanywhere.com/webhook/sync`
   * **Content type**: `application/json`
   * **Secret**: *(Leave blank)*
   * **Trigger events**: Select **"Just the push event"**.
4. Click **Add webhook** to save.
5. **You're Done!** Now, simply push your code locally (`git push origin main`). Your licensing server automatically synchronizes and updates all users' apps instantly!

#### Option B: Manual Upload
1. Go to the **Files** tab on PythonAnywhere and enter the `mysite/` folder.
2. Upload the updated `license_server.py` (rename/overwrite your main web file, e.g., `flask_app.py`).
3. Upload `index.html` to the exact same `mysite/` folder.
4. Upload `admin_dashboard.html` to the exact same `mysite/` folder (so your license management dashboard is active!).
5. Go to the **Web** tab in PythonAnywhere and click **Reload**.

### 🔨 Step 3: Compile the New EXE File
Generate a standalone compiled executable for your users:
1. Open your terminal/command line locally in `d:\autocontent`.
2. Run the compiler command:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --add-data "index.html;." app.py
   ```
3. Your brand-new self-updating executable is now fully compiled and sitting inside the `dist/` folder ready for distribution!

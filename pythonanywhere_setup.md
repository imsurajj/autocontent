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
Generate a new key for a user:
`https://imsuraj.pythonanywhere.com/admin/add_key/TEAM-A-1234`
*(You will see a message saying "Key added successfully". You can now give this key to your team member.)*

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

> **Security Note:** These endpoints are currently open for your convenience. Since this URL is private to you, it's generally safe, but keep your PythonAnywhere URL secret!

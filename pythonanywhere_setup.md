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

Your server has a simple built-in way to generate new keys. 

### Generating a New Key
To create a new key (e.g., "TEAM-A-1234"), simply open your web browser and go to:
`https://yourusername.pythonanywhere.com/admin/add_key/TEAM-A-1234`

You should see a message saying "Key added successfully". You can now give this key to your team member.

### Revoking a Key
1. In PythonAnywhere, go to the **Files** tab and open your `mysite` folder.
2. You will see a file named `licenses.db`. 
3. To change a key's status, you can either download this file and open it locally using a tool like [DB Browser for SQLite](https://sqlitebrowser.org/), or run an SQLite console directly in PythonAnywhere to run a quick SQL command:
   ```sql
   UPDATE licenses SET status = 'Revoked' WHERE key = 'TEAM-A-1234';
   ```
4. Once marked as "Revoked", the user's desktop app will immediately block them from using the software.

> **Security Note:** The `/admin/add_key/` endpoint is currently open for ease of setup. Once you are comfortable, you should add a simple password check to this route in `flask_app.py` so random people cannot generate their own keys!

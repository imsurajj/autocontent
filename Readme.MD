# PDF Batch Generator

A simple, fast tool to generate multiple PDFs from a single Markdown content file using a list of titles. 
Perfect for creating high-quality, formatted documents in bulk.

---

## Features

- **Batch Generation:** Generate 10, 50, or 100+ PDFs in seconds.
- **Markdown Support:** Write your content in simple Markdown; get beautifully formatted PDFs.
- **Dynamic Titles:** Each PDF gets a unique title from your list.
- **Sequential Naming:** Files are automatically named (e.g., `doc01.pdf`, `doc02.pdf`).
- **Desktop UI:** Easy-to-use interface with Light/Dark mode support.

---

## Project Structure

```
autocontent/
├── app.py           ← The main Desktop application
├── .env             ← Configuration settings
├── requirements.txt ← Required Python packages
├── content.md       ← Your base body content
└── titles.md        ← Your list of titles (one per line)
```

---

### Step 2 — Create the Database & Licenses Table

#### Via the Appwrite Console (UI)

*Note: Appwrite recently updated their terminology. "Collections" are now called "Tables", and "Attributes" are now "Columns".*

| Step | Action |
|------|--------|
| 1 | **Database → + New Database** → Name: `autocontent`, ID: `autocontent` |
| 2 | Inside the DB → **+ Create Table** → Name: `licenses`, ID: `licenses` |
| 3 | Add columns (see table below) |
| 4 | Copy the **Database ID** and **Table ID** (Collection ID) |

**Required Columns for the `licenses` table:**

| Column Key     | Type     | Required | Notes                         |
|----------------|----------|----------|-------------------------------|
| `userId`       | String   | ✅       | Appwrite user ID or email     |
| `licenseKey`   | String   | ✅       | The unique license key        |
| `hardwareId`   | String   | ❌       | Locked machine fingerprint    |
| `expiresAt`    | DateTime | ❌       | Expiry date (null = lifetime) |
| `isActive`     | Boolean  | ✅       | Whether the license is valid  |

---

## Configuration (.env)

| Setting | Description |
|---|---|
| `FILE_PREFIX` | Filename prefix (e.g., `doc` -> `doc01.pdf`) |
| `START_NUMBER` | Where to start numbering files |
| `OUTPUT_FOLDER` | Where the generated PDFs will be saved |

---

## Developer Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. To build the `.exe`:
   ```bash
   pyinstaller --noconsole --onefile app.py
   ```

---

## 📚 Documentation

For advanced setup and distribution, see the following guides included in this repository:

- [☁️ Appwrite Cloud Setup Guide](appwrite.md) — How to provision the backend, secure license verification, and set up database tables.
- [📦 Testing & Distribution Guide](distribution.md) — How to test locally, compile with PyInstaller, and build a Windows installer using Inno Setup.

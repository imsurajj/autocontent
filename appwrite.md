## ☁️ Appwrite Cloud Backend Setup

AutoContent Pro uses **Appwrite Cloud** as its serverless backend for license verification, hardware locking, and OTA updates. Follow the steps below to provision everything from scratch.

---

### Step 1 — Create an Appwrite Project

1. Go to [https://cloud.appwrite.io](https://cloud.appwrite.io) and sign in.
2. Click **Projects → Create Project**.
3. Name it (e.g. `AutoContent-Pro`) and confirm.
4. From the project dashboard, copy:
   - **Project ID** (e.g. `autocontent`)
   - **API Key** → Settings → API Keys → **Create API Key** with full `databases` + `functions` scopes.

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

| Column Key    | Type     | Size | Required | Notes |
|---------------|----------|------|----------|-------|
| `licenseKey`  | String   | 64   | ✅       | The license key (e.g. `TESTLICENSE1234`) |
| `userId`      | String   | 100  | ✅       | User's display name or email |
| `hardwareId`  | String   | 128  | ❌       | HWID — auto-filled by the function on first use, leave empty |
| `expiresAt`   | DateTime | —    | ❌       | Expiry date — leave empty for lifetime license |
| `isActive`    | Boolean  | —    | ✅       | Set to `true` to activate the license |

> ℹ️ **System fields** (`$id`, `$createdAt`, `$updatedAt`) are added automatically by Appwrite — do not delete them, they are fine.

> ✅ **The Document ID can be left auto-generated.** The function now searches by the `licenseKey` field, so you don't need to set the document ID manually anymore.

**Example row to add for testing:**

| Field | Value |
|-------|-------|
| `licenseKey` | `TESTLICENSE1234` |
| `userId` | `Test User` |
| `hardwareId` | *(leave empty)* |
| `expiresAt` | *(leave empty for lifetime, or pick a future date)* |
| `isActive` | `true` |

#### Via the Appwrite CLI

```bash
# Configure CLI (run once)
appwrite config set endpoint https://cloud.appwrite.io/v1
appwrite config set project autocontent
appwrite config set key YOUR_SERVER_API_KEY

# Create database
appwrite databases createDatabase \
    --databaseId autocontent \
    --name "AutoContent"

# Create collection
appwrite databases createCollection \
    --databaseId autocontent \
    --collectionId licenses \
    --name "Licenses"

# Add attributes
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key userId     --size 36  --required true
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key licenseKey --size 64  --required true
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key hardwareId --size 128 --required false
appwrite databases createDateTimeAttribute --databaseId autocontent --collectionId licenses --key expiresAt            --required false
appwrite databases createBooleanAttribute  --databaseId autocontent --collectionId licenses --key isActive             --required true
```

---

### Step 3 — Deploy the License-Verification Function

1. In the Appwrite Console go to **Functions → + Create Function**.
2. Set:
   - **Runtime:** Python 3.11
   - **Function ID:** `verify-license`
   - **Entry point:** `main`
3. Upload your function source (zip the function folder or link a GitHub repo).
4. **Add Environment Variables** inside the function settings (⚠️ **never** put these in `.env` committed to Git):

| Variable Name         | Value                              |
|-----------------------|------------------------------------|
| `APPWRITE_ENDPOINT`   | `https://cloud.appwrite.io/v1`     |
| `APPWRITE_PROJECT_ID` | Your Project ID                    |
| `APPWRITE_API_KEY`    | Your server-side API Key           |
| `DATABASE_ID`         | `autocontent`                      |
| `COLLECTION_ID`       | `licenses`                         |

5. Click **Deploy** and wait for the status to show ✅ **Active**.

---

### Step 4 — Configure Your Local `.env`

Copy `.env.example` → `.env` and fill in only the **public** values:

```dotenv
# ==========================================
# APPWRITE CLOUD CONFIGURATION
# ==========================================
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=autocontent          # ← your Project ID
APPWRITE_FUNCTION_ID=verify-license      # ← function ID from Step 3
```

> ⚠️ **Security Rule:** `APPWRITE_API_KEY` must **NEVER** be placed in `.env` or committed to Git.  
> It belongs exclusively in the Appwrite Function's environment variable settings.

---

### Step 5 — How the Client Calls the Function

The desktop app never talks to the database directly. It only invokes the serverless function:

```python
from appwrite.client import Client
from appwrite.services.functions import Functions
import os, json

client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT")) \
      .set_project(os.getenv("APPWRITE_PROJECT_ID"))
# ← No API key on the client side!

functions = Functions(client)

result = functions.create_execution(
    function_id=os.getenv("APPWRITE_FUNCTION_ID"),
    data=json.dumps({
        "licenseKey": user_key,
        "hardwareId": hw_id
    })
)

response = json.loads(result["response"])
# response = { "valid": True/False, "message": "..." }
```

---

### Step 6 — Automated Setup (PowerShell)

Run `setup.ps1` once to provision everything automatically:

```powershell
# setup.ps1
$Endpoint  = "https://cloud.appwrite.io/v1"
$ProjectId = "YOUR_PROJECT_ID"
$ApiKey    = "YOUR_SERVER_API_KEY"

appwrite config set endpoint $Endpoint
appwrite config set project  $ProjectId
appwrite config set key      $ApiKey

appwrite databases createDatabase   --databaseId autocontent --name "AutoContent"
appwrite databases createCollection --databaseId autocontent --collectionId licenses --name "Licenses"

# Attributes
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key userId     --size 36  --required true
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key licenseKey --size 64  --required true
appwrite databases createStringAttribute   --databaseId autocontent --collectionId licenses --key hardwareId --size 128 --required false
appwrite databases createDateTimeAttribute --databaseId autocontent --collectionId licenses --key expiresAt            --required false
appwrite databases createBooleanAttribute  --databaseId autocontent --collectionId licenses --key isActive             --required true

Write-Host "✅ Database + Collection provisioned. Now deploy the function via the Appwrite Console."
```

---

### ✅ Final Checklist

```
[ ] Created Appwrite project → noted Project ID & API Key
[ ] Created database "autocontent" + table "licenses" with all columns
[ ] Deployed function "verify-license" (Python 3.11)
[ ] Added all 5 env vars INSIDE the Appwrite Function settings
[ ] Copied .env.example → .env, filled ENDPOINT + PROJECT_ID + FUNCTION_ID only
[ ] Confirmed APPWRITE_API_KEY is NOT in .env or any committed file
[ ] Ran the app → license verification returns valid response
[ ] .env is listed in .gitignore
```

---

### 🔒 Security Notes

- The `APPWRITE_API_KEY` grants full admin access. **Treat it like a password.**
- The client (desktop app) only holds the public Project ID — safe to ship.
- All database reads/writes happen inside the serverless function on Appwrite's servers.
- Hardware locking is enforced server-side; the client cannot bypass it.
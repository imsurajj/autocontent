# PDF Batch Generator

Generates multiple PDFs with AI-rephrased titles using the Gemini API.
You write the content once — Gemini rewrites the title differently for each PDF.
Files are saved as `exp01.pdf`, `exp02.pdf`, and so on.

---

## What You Get

```
pdf_gen/
├── main.py          ← all the logic
├── .env             ← your API key + settings
├── requirements.txt ← python packages needed
└── content.md       ← your title + body content
```

---

## Step 1 — Make Sure Python is Installed

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
python --version
```

You need **Python 3.10 or higher**. If not installed, download it from https://python.org.

---

## Step 2 — Get a Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key — you'll paste it in the next step

---

## Step 3 — Set Up the Project

Download or copy all 4 files into one folder, for example `pdf_gen/`.

Your folder should look like this:

```
pdf_gen/
├── main.py
├── .env
├── requirements.txt
└── content.md
```

---

## Step 4 — Install Dependencies

In your terminal, navigate to the project folder:

```bash
cd path/to/pdf_gen
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

---

## Step 5 — Configure `.env`

Open the `.env` file in any text editor and fill it in:

```env
GEMINI_API_KEY=paste_your_key_here
GEMINI_MODEL=gemini-1.5-flash

HOW_MANY_PDFS=5
FILE_PREFIX=exp
OUTPUT_FOLDER=output_pdfs
```

| Setting | What it does |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key from Step 2 |
| `GEMINI_MODEL` | Gemini model to use (keep as `gemini-1.5-flash`) |
| `HOW_MANY_PDFS` | How many PDFs to generate |
| `FILE_PREFIX` | Filename prefix — `exp` gives `exp01.pdf`, `exp02.pdf` ... |
| `OUTPUT_FOLDER` | Where PDFs are saved (see options below) |

### OUTPUT_FOLDER options

**Relative path** — saves inside the project folder:
```env
OUTPUT_FOLDER=output_pdfs
```

**Absolute path** — saves anywhere on your computer:
```env
# Windows
OUTPUT_FOLDER=C:/Users/YourName/Desktop/my_pdfs

# Mac / Linux
OUTPUT_FOLDER=/Users/YourName/Desktop/my_pdfs
```

The folder is created automatically if it doesn't exist.

---

## Step 6 — Write Your Content

Open `content.md` in any text editor.

**Format rules:**
- The first line must start with `#` — this is your base title
- Gemini will rephrase this title for each PDF
- Leave a blank line between paragraphs

**Example:**

```markdown
# The Impact of Artificial Intelligence on Modern Healthcare

Artificial intelligence is rapidly transforming the healthcare industry.
From diagnostics to drug discovery, AI-powered tools are enabling faster
and more personalized medical care than ever before.

Machine learning algorithms can now analyze medical images such as X-rays
and MRIs with accuracy comparable to experienced radiologists. This leads
to earlier detection of conditions like cancer.

Despite the promise, challenges remain. Data privacy, algorithmic bias,
and regulatory approval are barriers that must be addressed before AI
can be fully integrated into clinical workflows.
```

You can add as many paragraphs as you want. Just separate each one with a blank line.

---

## Step 7 — Run It

```bash
python main.py
```

You'll see output like this:

```
  Base title : The Impact of Artificial Intelligence on Modern Healthcare
  Generating : 5 PDFs  →  /your/path/output_pdfs

[1/5] Rephrasing... ✓
        → How AI is Revolutionizing the Future of Medicine
        Saved: exp01.pdf

[2/5] Rephrasing... ✓
        → Artificial Intelligence and Its Growing Role in Healthcare
        Saved: exp02.pdf

...

✅  Done! 5 PDFs saved to:
   /your/path/output_pdfs
```

---

## Common Errors

**`GEMINI_API_KEY` not set**
```
❌  Set GEMINI_API_KEY in .env
```
→ Open `.env` and paste your API key where it says `your_gemini_api_key_here`

---

**`content.md` not found**
```
❌  content.md not found.
```
→ Make sure `content.md` is in the same folder as `main.py`

---

**`ModuleNotFoundError`**
```
ModuleNotFoundError: No module named 'reportlab'
```
→ Run `pip install -r requirements.txt` again

---

**Wrong Python version**
```
SyntaxError or TypeError
```
→ Run `python --version` — you need 3.10 or above. Try `python3 main.py` on Mac/Linux.

---

## Changing Things Later

| What you want to change | Where to change it |
|---|---|
| Title or body content | `content.md` |
| Number of PDFs | `HOW_MANY_PDFS` in `.env` |
| Output folder / location | `OUTPUT_FOLDER` in `.env` |
| Filename prefix (exp → doc) | `FILE_PREFIX` in `.env` |
| Gemini model | `GEMINI_MODEL` in `.env` |
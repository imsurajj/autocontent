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

## How to Use

1. **Write Content:** Open `content.md` and write your main text.
2. **List Titles:** Open `titles.md` and add one title per line for each PDF you want to create.
3. **Run App:** Launch the application, select your settings, and hit "Generate".

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
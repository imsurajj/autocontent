"""
Generate PDF from Markdown using Chromium (Playwright).

Usage:
  pip install -r requirements.txt
  python -m playwright install
  python generate_pdf_chromium.py
"""

import os
import re
import sys
from markdown import markdown
from dotenv import load_dotenv
from pathlib import Path
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = Path(__file__).parent
PREFIX = os.getenv("FILE_PREFIX", "exp")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output_pdfs")
TITLES_FILE = BASE_DIR / "titles.md"
CONTENT_FILE = BASE_DIR / "content.md"

if not os.path.isabs(OUTPUT_FOLDER):
    OUTPUT_FOLDER = os.path.join(BASE_DIR, OUTPUT_FOLDER)


def next_file_number():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(PREFIX)}(\d+)\.pdf$", re.IGNORECASE)
    nums = []
    for f in os.listdir(OUTPUT_FOLDER):
        m = pattern.match(f)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def load_titles():
    if not TITLES_FILE.exists():
        print("titles.md not found")
        sys.exit(1)

    titles = []
    for line in TITLES_FILE.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t:
            titles.append(t)

    if not titles:
        print("No titles found in titles.md")
        sys.exit(1)

    return titles


def load_md():
    if not CONTENT_FILE.exists():
        print("content.md not found")
        sys.exit(1)
    return CONTENT_FILE.read_text(encoding="utf-8")


HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Markdown PDF</title>
  <style>
    :root {
      --title-color: #1a1a2e;
      --accent: #FF6B6B;
      --body: #000000;
    }

    html, body {
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Emoji", "Noto Color Emoji", "Apple Color Emoji", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: var(--body) !important;
      padding: 40px;
      font-size: 14px;
      line-height: 1.6;
    }

    h1 {
      color: var(--title-color) !important;
      font-size: 28px;
      margin: 0 0 8px 0;
    }

    h2 {
      color: var(--title-color) !important;
      font-size: 20px;
      margin-top: 18px;
      margin-bottom: 6px;
    }

    h3 {
      color: var(--title-color) !important;
      font-size: 16px;
      margin-top: 14px;
      margin-bottom: 4px;
    }

    p, li, div, span, strong, em, a {
      color: var(--body) !important;
    }

    hr {
      border: none;
      height: 3px;
      background: var(--accent);
      margin: 12px 0 18px;
    }

    p {
      margin: 8px 0;
    }

    ul, ol {
      margin: 8px 0 8px 22px;
    }

    li {
      margin: 4px 0;
    }

    strong {
      font-weight: 600;
    }

    em {
      font-style: italic;
    }

    a {
      text-decoration: underline;
    }

    * {
      color: var(--body);
    }
  </style>
</head>
<body>
__BODY__
</body>
</html>
"""


def md_to_html(md_text: str) -> str:
    html_body = markdown(md_text, extensions=["extra", "sane_lists"])
    return HTML_TEMPLATE.replace("__BODY__", html_body)


def generate_pdf(html: str, out_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.emulate_media(media="screen")
        page.pdf(path=out_path, format="A4", print_background=True)
        browser.close()


def inject_title(md_text: str, title: str) -> str:
    lines = md_text.splitlines()

    if lines and lines[0].strip().startswith("# "):
        lines[0] = f"# {title}"
        return "\n".join(lines)

    return f"# {title}\n\n{md_text}"


def main():
    titles = load_titles()
    md = load_md()

    n = next_file_number()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("Generating PDFs using Chromium…")
    print(" Titles:", len(titles))

    for title in titles:
        final_md = inject_title(md, title)
        html = md_to_html(final_md)

        filename = f"{PREFIX}{n:02d}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, filename)

        print(" Title:", title)
        print(" File :", out_path)

        generate_pdf(html, out_path)
        n += 1

    print("Done — all PDFs saved.")


if __name__ == "__main__":
    main()
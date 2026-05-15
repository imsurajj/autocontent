"""
Generate PDF from Markdown using Chromium (Playwright).

Usage:
  pip install -r requirements.txt
  python -m playwright install
  python generate_pdf_chromium.py

This script reads `content.md`, converts it to HTML, renders with a small CSS
that prioritizes emoji-capable fonts, and saves a numbered PDF named like `exp01.pdf`.
"""

import os
import re
import sys
from markdown import markdown
from dotenv import load_dotenv
from pathlib import Path
from playwright.sync_api import sync_playwright

load_dotenv()

PREFIX = os.getenv("FILE_PREFIX", "exp")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output_pdfs")

if not os.path.isabs(OUTPUT_FOLDER):
    OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FOLDER)


def next_file_number():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    pattern = re.compile(rf'^{re.escape(PREFIX)}(\d+)\.pdf$', re.IGNORECASE)
    nums = []
    for f in os.listdir(OUTPUT_FOLDER):
        m = pattern.match(f)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def load_md():
    path = Path(__file__).parent / 'content.md'
    if not path.exists():
        print('content.md not found')
        sys.exit(1)
    text = path.read_text(encoding='utf-8')
    return text


HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Markdown PDF</title>
  <style>
    :root{{--title-color:#1a1a2e;--accent:#FF6B6B;--body:#2d2d2d}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI Emoji","Noto Color Emoji","Apple Color Emoji","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
          color:var(--body); padding:40px; font-size:14px; line-height:1.6;}}
    h1{{color:var(--title-color); font-size:24px; margin-bottom:8px;}}
    h2{{color:var(--title-color); font-size:20px; margin-top:18px; margin-bottom:6px;}}
    h3{{color:var(--title-color); font-size:16px; margin-top:14px; margin-bottom:4px;}}
    hr{{border:none; height:3px; background:var(--accent); margin:12px 0 18px;}}
    p{{margin:8px 0;}}
    ul,ol{{margin:8px 0 8px 22px;}}
    li{{margin:4px 0;}}
    strong{{font-weight:600;}}
    em{{font-style:italic;}}
    a{{color:#0b57d0; text-decoration:underline;}}
  </style>
</head>
<body>
{body}
</body>
</html>
'''

def md_to_html(md_text: str) -> str:
    html_body = markdown(md_text, extensions=['extra', 'sane_lists'])
    return HTML_TEMPLATE.format(body=html_body)


def generate_pdf(html: str, out_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until='networkidle')
        # render to PDF with background and A4
        page.pdf(path=out_path, format='A4', print_background=True)
        browser.close()


def main():
    md = load_md()
    # Title extraction (first H1)
    title = 'Document'
    for line in md.splitlines():
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            break

    html = md_to_html(md)

    n = next_file_number()
    filename = f"{PREFIX}{n:02d}.pdf"
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    out_path = os.path.join(OUTPUT_FOLDER, filename)

    print('Generating PDF using Chromium…')
    print(' Title:', title)
    print(' File :', out_path)

    generate_pdf(html, out_path)
    print('Done — saved to', out_path)


if __name__ == '__main__':
    main()
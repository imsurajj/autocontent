"""
PDF Batch Generator
-------------------
- User pastes titles (one per line) — used exactly as given
- Content comes from content.md (full markdown supported)
- Auto-detects existing PDFs and continues numbering from there
  e.g. if exp01-exp05 exist, next batch starts at exp06

Setup:
    pip install -r requirements.txt
    → fill in .env
    → edit content.md
    → python main.py
"""

import os
import re
import sys
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    ListFlowable, ListItem
)

load_dotenv()

# ── Config from .env ──────────────────────────────────────────────────────────

PREFIX        = os.getenv("FILE_PREFIX", "exp")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output_pdfs")
TITLES_FILE   = os.getenv("TITLES_FILE", "titles.md")
START_NUMBER  = os.getenv("START_NUMBER")

if START_NUMBER:
    try:
        START_NUMBER = int(START_NUMBER)
    except ValueError:
        START_NUMBER = None

if not os.path.isabs(OUTPUT_FOLDER):
    OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FOLDER)


# ── Auto-detect next file number ──────────────────────────────────────────────

def next_file_number() -> int:
    """
    Scans OUTPUT_FOLDER for files matching PREFIX+number (e.g. exp01.pdf, exp12.pdf)
    and returns the next number to use.
    If START_NUMBER is set in .env, uses that as the starting point.
    Otherwise, returns the next number after existing files.
    """
    if START_NUMBER:
        return START_NUMBER

    if not os.path.exists(OUTPUT_FOLDER):
        return 1

    pattern = re.compile(rf'^{re.escape(PREFIX)}(\d+)\.pdf$', re.IGNORECASE)
    numbers = []

    for fname in os.listdir(OUTPUT_FOLDER):
        m = pattern.match(fname)
        if m:
            numbers.append(int(m.group(1)))

    return max(numbers) + 1 if numbers else 1


# ── Ask user for titles ───────────────────────────────────────────────────────

def get_titles_from_stdin() -> list:
    """
    Prompts the user to paste one or more titles (one per line).
    Ends input on a blank line or EOF.
    """
    print("\n  Paste your titles below (one per line).")
    print("  Press Enter twice when done:\n")

    titles = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            if titles:          # blank line after at least one title = done
                break
            else:
                continue        # ignore leading blank lines
        titles.append(line.strip())

    if not titles:
        print("❌  No titles entered. Exiting.")
        sys.exit(1)

    return titles


def load_titles() -> list:
    """
    Loads titles from a markdown file if it exists, otherwise prompts the user.
    Supports plain lines, markdown bullets, and numbered lists.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    titles_path = TITLES_FILE if os.path.isabs(TITLES_FILE) else os.path.join(base_dir, TITLES_FILE)

    if os.path.exists(titles_path):
        with open(titles_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        titles = []
        for raw in raw_lines:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("#"):
                continue
            bullet_match = re.match(r'^[\-\*\+]\s+(.*)$', s)
            if bullet_match:
                s = bullet_match.group(1).strip()
            else:
                numbered_match = re.match(r'^\d+\.\s+(.*)$', s)
                if numbered_match:
                    s = numbered_match.group(1).strip()

            if s:
                titles.append(s)

        if titles:
            print(f"\n  Loaded {len(titles)} title(s) from {TITLES_FILE}")
            return titles

        print(f"\n  {TITLES_FILE} found but no titles were parsed. Falling back to paste input.")

    print(f"\n  No titles file found at {TITLES_FILE}. Using paste input instead.")
    return get_titles_from_stdin()


# ── Load content.md ───────────────────────────────────────────────────────────

def load_content():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.md")
    if not os.path.exists(path):
        print("❌  content.md not found.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Drop the first # heading line — title comes from user input
    if lines and lines[0].startswith("#"):
        lines = lines[1:]

    return lines


# ── Parse markdown → ReportLab flowables ─────────────────────────────────────

def md_to_story(lines: list, styles) -> list:
    """
    Supported markdown:
      # H1   ## H2   ### H3
      **bold**   *italic*   `code`
      - bullet  (or * or +)
      1. numbered list
      > blockquote
      blank line = paragraph break
    """

    h1 = ParagraphStyle("mdH1", parent=styles["Heading1"],
                         fontSize=16, leading=22,
                         textColor=colors.HexColor("#1a1a2e"),
                         spaceBefore=14, spaceAfter=6)

    h2 = ParagraphStyle("mdH2", parent=styles["Heading2"],
                         fontSize=13, leading=18,
                         textColor=colors.HexColor("#2c2c54"),
                         spaceBefore=12, spaceAfter=4)

    h3 = ParagraphStyle("mdH3", parent=styles["Heading3"],
                         fontSize=11, leading=16,
                         textColor=colors.HexColor("#444"),
                         spaceBefore=10, spaceAfter=3)

    body = ParagraphStyle("mdBody", parent=styles["Normal"],
                           fontSize=11, leading=18,
                           textColor=colors.HexColor("#2d2d2d"),
                           spaceAfter=8)

    quote = ParagraphStyle("mdQuote", parent=styles["Normal"],
                            fontSize=11, leading=17,
                            textColor=colors.HexColor("#555555"),
                            leftIndent=20, spaceAfter=8)

    bullet_st = ParagraphStyle("mdBullet", parent=styles["Normal"],
                                fontSize=11, leading=17,
                                textColor=colors.HexColor("#2d2d2d"))

    def inline(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
        text = re.sub(r'`(.+?)`',       r'<font name="Courier">\1</font>', text)
        return text

    story      = []
    para_lines = []
    bullet_buf = []
    num_buf    = []

    def flush_para():
        if para_lines:
            text = " ".join(l.strip() for l in para_lines if l.strip())
            if text:
                story.append(Paragraph(inline(text), body))
            para_lines.clear()

    def flush_bullets():
        if bullet_buf:
            items = [ListItem(Paragraph(inline(b), bullet_st),
                              bulletColor=colors.HexColor("#1a1a2e"))
                     for b in bullet_buf]
            story.append(ListFlowable(items, bulletType='bullet',
                                      leftIndent=20, spaceAfter=8))
            bullet_buf.clear()

    def flush_numbers():
        if num_buf:
            items = [ListItem(Paragraph(inline(n), bullet_st),
                              bulletColor=colors.HexColor("#1a1a2e"))
                     for n in num_buf]
            story.append(ListFlowable(items, bulletType='1',
                                      leftIndent=20, spaceAfter=8))
            num_buf.clear()

    for raw in lines:
        s = raw.rstrip("\n").strip()

        if s.startswith("### "):
            flush_para(); flush_bullets(); flush_numbers()
            story.append(Paragraph(inline(s[4:]), h3))

        elif s.startswith("## "):
            flush_para(); flush_bullets(); flush_numbers()
            story.append(Paragraph(inline(s[3:]), h2))

        elif s.startswith("# "):
            flush_para(); flush_bullets(); flush_numbers()
            story.append(Paragraph(inline(s[2:]), h1))

        elif s.startswith("> "):
            flush_para(); flush_bullets(); flush_numbers()
            story.append(Paragraph(inline(s[2:]), quote))

        elif re.match(r'^[-*+] ', s):
            flush_para(); flush_numbers()
            bullet_buf.append(s[2:])

        elif re.match(r'^\d+\. ', s):
            flush_para(); flush_bullets()
            num_buf.append(re.sub(r'^\d+\. ', '', s))

        elif s == "":
            flush_para(); flush_bullets(); flush_numbers()
            story.append(Spacer(1, 4))

        else:
            flush_bullets(); flush_numbers()
            para_lines.append(s)

    flush_para(); flush_bullets(); flush_numbers()
    return story


# ── Build one PDF ─────────────────────────────────────────────────────────────

def build_pdf(filepath: str, title: str, md_lines: list):
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("MainTitle", parent=styles["Title"],
                                  fontSize=17, leading=24,
                                  textColor=colors.HexColor("#1a1a2e"),
                                  spaceAfter=6)

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=colors.HexColor("#1a1a2e"), spaceAfter=10))
    story.extend(md_to_story(md_lines, styles))
    doc.build(story)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    titles   = load_titles()
    md_lines = load_content()
    start_n  = next_file_number()

    print(f"\n  {len(titles)} title(s) received")
    print(f"  Starting from : {PREFIX}{start_n:02d}.pdf")
    print(f"  Output folder : {OUTPUT_FOLDER}\n")

    for i, title in enumerate(titles):
        n        = start_n + i
        filename = f"{PREFIX}{n:02d}.pdf"
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        print(f"[{i+1}/{len(titles)}] {filename}")
        print(f"        Title : {title}")
        build_pdf(filepath, title, md_lines)
        print(f"        Saved ✓\n")

    print(f"✅  Done! {len(titles)} PDF(s) saved to:")
    print(f"   {OUTPUT_FOLDER}\n")


if __name__ == "__main__":
    main()
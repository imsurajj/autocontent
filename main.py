"""
PDF Generator with Full Emoji Support
--------------------------------------
Creates PDF from `content.md` using `fpdf2` with Unicode TTF support.

Usage:
    pip install fpdf2 python-dotenv
    python main.py

"""

import os
import re
import sys
import platform
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()


def locate_unicode_font():
    """Return a path to a TTF font that likely supports emoji/unicode, or None."""
    candidates = []
    base = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(base, "fonts", "DejaVuSans.ttf"),
        os.path.join(base, "fonts", "NotoColorEmoji.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "DejaVuSans.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "seguiemj.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "SegoeUIEmoji.ttf"),
        "/Library/Fonts/Apple Color Emoji.ttf",
        "/System/Library/Fonts/Apple Color Emoji.ttf",
    ])

    if os.getenv("VERBOSE_CHECK", "0") == "1":
        print("Checking font candidates:")
        for p in candidates:
            print("  ", p, "->", os.path.exists(p))

    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


PREFIX = os.getenv("FILE_PREFIX", "exp")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output_pdfs")
START_NUMBER = os.getenv("START_NUMBER")
if START_NUMBER:
    try:
        START_NUMBER = int(START_NUMBER)
    except Exception:
        START_NUMBER = None

if not os.path.isabs(OUTPUT_FOLDER):
    OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FOLDER)


def next_file_number():
    if START_NUMBER:
        return START_NUMBER
    if not os.path.exists(OUTPUT_FOLDER):
        return 1
    pattern = re.compile(rf'^{re.escape(PREFIX)}(\d+)\.pdf$', re.IGNORECASE)
    nums = []
    for f in os.listdir(OUTPUT_FOLDER):
        m = pattern.match(f)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def extract_title_from_content():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.md")
    if not os.path.exists(path):
        print("❌ content.md not found")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("# "):
                return s[2:].strip()
    return "Document"


def load_content():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.md")
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    return lines


def build_pdf(filepath, title, md_lines):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = locate_unicode_font()
    font_family = None
    if font_path:
        try:
            pdf.add_font('DejaVu', '', font_path, uni=True)
            pdf.add_font('DejaVu', 'B', font_path, uni=True)
            pdf.add_font('DejaVu', 'I', font_path, uni=True)
            font_family = 'DejaVu'
        except Exception as e:
            print(f"⚠️ Could not register font {font_path}: {e}")

    if not font_family:
        print("⚠️  No Unicode TTF registered. Falling back to built-in fonts (limited emoji support).")
        font_family = 'helvetica'

    title_color = (26, 26, 46)
    body_color = (45, 45, 45)

    pdf.set_text_color(*title_color)
    pdf.set_font(font_family, 'B', 16)
    pdf.multi_cell(0, 10, title)

    pdf.set_draw_color(255, 107, 107)
    pdf.set_line_width(1.5)
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_text_color(*body_color)
    pdf.set_font(font_family, size=11)

    for raw in md_lines:
        text = raw.rstrip("\n").strip()
        if not text:
            pdf.ln(2)
            continue

        if text.startswith('# '):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, 'B', 14)
            pdf.ln(3)
            pdf.multi_cell(0, 8, text[2:].strip())
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.ln(2)
            continue

        if text.startswith('## '):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, 'B', 12)
            pdf.ln(2)
            pdf.multi_cell(0, 8, text[3:].strip())
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.ln(1)
            continue

        if text.startswith('### '):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, 'B', 11)
            pdf.ln(2)
            pdf.multi_cell(0, 8, text[4:].strip())
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.ln(1)
            continue

        if text.startswith('> '):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, 'I', 10)
            pdf.set_x(20)
            pdf.multi_cell(0, 7, text[2:].strip())
            pdf.set_font(font_family, size=11)
            pdf.ln(1)
            continue

        if re.match(r'^[-*+] ', text):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.set_x(15)
            pdf.multi_cell(0, 7, '● ' + text[2:].strip())
            pdf.ln(1)
            continue

        if re.match(r'^\d+\. ', text):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.set_x(15)
            pdf.multi_cell(0, 7, text)
            pdf.ln(1)
            continue

        pdf.set_text_color(*body_color)
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 7, text)
        pdf.ln(1)

    pdf.output(filepath)


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    title = extract_title_from_content()
    md_lines = load_content()
    file_num = next_file_number()
    filename = f"{PREFIX}{file_num:02d}.pdf"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    print(f"\nPDF Generator - Emoji Support Active ✨")
    print(f"Python : {platform.python_version()} ({platform.system()})")
    print(f"CWD    : {os.getcwd()}")
    print(f"Title  : {title}")
    print(f"File   : {filename}")
    print(f"Output : {OUTPUT_FOLDER}\n")

    try:
        build_pdf(filepath, title, md_lines)
    except Exception:
        import traceback
        print("❌ Error while generating PDF:")
        traceback.print_exc()
        return

    print("✅ PDF saved successfully!")
    print(f"📍 {filepath}")


if __name__ == '__main__':
    main()

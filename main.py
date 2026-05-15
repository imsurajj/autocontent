import os
import re
import sys
import platform
from pathlib import Path
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "content.md"
TITLES_FILE = BASE_DIR / "titles.md"
OUTPUT_FOLDER = Path(os.getenv("OUTPUT_FOLDER", BASE_DIR / "output_pdfs"))
PREFIX = os.getenv("FILE_PREFIX", "exp")
START_NUMBER = os.getenv("START_NUMBER")

if START_NUMBER:
    try:
        START_NUMBER = int(START_NUMBER)
    except Exception:
        START_NUMBER = None


def locate_unicode_font():
    candidates = [
        BASE_DIR / "fonts" / "DejaVuSans.ttf",
        BASE_DIR / "fonts" / "NotoColorEmoji.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"),
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "DejaVuSans.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "seguiemj.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "SegoeUIEmoji.ttf",
        Path("/Library/Fonts/Apple Color Emoji.ttf"),
        Path("/System/Library/Fonts/Apple Color Emoji.ttf"),
    ]

    for p in candidates:
        if p.exists():
            return str(p)
    return None


def read_titles():
    if not TITLES_FILE.exists():
        print("❌ titles.md not found")
        sys.exit(1)

    titles = []
    with TITLES_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                titles.append(s)

    if not titles:
        print("❌ No titles found in titles.md")
        sys.exit(1)

    return titles


def load_content():
    if not CONTENT_FILE.exists():
        print("❌ content.md not found")
        sys.exit(1)

    with CONTENT_FILE.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    if lines and lines[0].startswith("#"):
        lines = lines[1:]

    return lines


def next_file_number():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    if START_NUMBER is not None:
        return START_NUMBER

    pattern = re.compile(rf"^{re.escape(PREFIX)}(\d+)\.pdf$", re.IGNORECASE)
    nums = []
    for f in OUTPUT_FOLDER.iterdir():
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def build_pdf(filepath, title, md_lines, font_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_family = "helvetica"
    if font_path:
        try:
            pdf.add_font("DejaVu", "", font_path, uni=True)
            pdf.add_font("DejaVu", "B", font_path, uni=True)
            pdf.add_font("DejaVu", "I", font_path, uni=True)
            font_family = "DejaVu"
        except Exception as e:
            print(f"⚠️ Could not register font {font_path}: {e}")

    title_color = (26, 26, 46)
    body_color = (0, 0, 0)

    pdf.set_text_color(*title_color)
    pdf.set_font(font_family, "B", 16)
    pdf.multi_cell(0, 10, title)

    pdf.set_draw_color(255, 107, 107)
    pdf.set_line_width(1.5)
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for raw in md_lines:
        text = raw.rstrip("\n").strip()

        if not text:
            pdf.ln(2)
            continue

        if text.startswith("# "):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, "B", 14)
            pdf.ln(3)
            pdf.multi_cell(0, 8, text[2:].strip())
            pdf.set_font(font_family, size=11)
            pdf.set_text_color(*body_color)
            pdf.ln(2)
            continue

        if text.startswith("## "):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, "B", 12)
            pdf.ln(2)
            pdf.multi_cell(0, 8, text[3:].strip())
            pdf.set_font(font_family, size=11)
            pdf.set_text_color(*body_color)
            pdf.ln(1)
            continue

        if text.startswith("### "):
            pdf.set_text_color(*title_color)
            pdf.set_font(font_family, "B", 11)
            pdf.ln(2)
            pdf.multi_cell(0, 8, text[4:].strip())
            pdf.set_font(font_family, size=11)
            pdf.set_text_color(*body_color)
            pdf.ln(1)
            continue

        if text.startswith("> "):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, "I", 10)
            pdf.set_x(20)
            pdf.multi_cell(0, 7, text[2:].strip())
            pdf.set_font(font_family, size=11)
            pdf.set_text_color(*body_color)
            pdf.ln(1)
            continue

        if re.match(r"^[-*+] ", text):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.set_x(15)
            pdf.multi_cell(0, 7, "● " + text[2:].strip())
            pdf.set_text_color(*body_color)
            pdf.ln(1)
            continue

        if re.match(r"^\d+\. ", text):
            pdf.set_text_color(*body_color)
            pdf.set_font(font_family, size=11)
            pdf.set_x(15)
            pdf.multi_cell(0, 7, text)
            pdf.set_text_color(*body_color)
            pdf.ln(1)
            continue

        pdf.set_text_color(*body_color)
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 7, text)
        pdf.set_text_color(*body_color)
        pdf.ln(1)

    pdf.output(str(filepath))


def main():
    titles = read_titles()
    md_lines = load_content()
    font_path = locate_unicode_font()
    file_num = next_file_number()

    print(f"\nPDF Generator")
    print(f"Python : {platform.python_version()} ({platform.system()})")
    print(f"CWD    : {os.getcwd()}")
    print(f"Output : {OUTPUT_FOLDER}")
    print(f"Titles : {len(titles)}\n")

    for title in titles:
        filename = f"{PREFIX}{file_num:02d}.pdf"
        filepath = OUTPUT_FOLDER / filename

        try:
            build_pdf(filepath, title, md_lines, font_path)
            print(f"✅ Saved: {filepath}")
        except Exception:
            import traceback
            print(f"❌ Error while generating PDF for: {title}")
            traceback.print_exc()

        file_num += 1


if __name__ == "__main__":
    main()
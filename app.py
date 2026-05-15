import os
import re
import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from fpdf import FPDF
from markdown import markdown

# Initialize environment
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"

# Default fallback settings
DEFAULT_SETTINGS = {
    "output_folder": str(BASE_DIR / "output_pdfs"),
    "prefix": "doc",
    "start_num": "1",
    "appearance_mode": "Dark",
    "content": "",
    "titles": ""
}

class AutoContentPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load "Cookies" (Settings)
        self.settings = self.load_settings()

        self.title("AutoContent Pro — Ultimate Batch Engine")
        self.geometry("1100x750")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Variables
        self.output_folder = tk.StringVar(value=self.settings.get("output_folder"))
        self.prefix = tk.StringVar(value=self.settings.get("prefix"))
        self.start_num = tk.StringVar(value=self.settings.get("start_num"))
        self.appearance_mode = tk.StringVar(value=self.settings.get("appearance_mode"))

        self.setup_ui()
        self.restore_work()
        
        # Set theme
        ctk.set_appearance_mode(self.appearance_mode.get())

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except:
                return DEFAULT_SETTINGS
        return DEFAULT_SETTINGS

    def save_settings(self):
        # Gather current state
        current_data = {
            "output_folder": self.output_folder.get(),
            "prefix": self.prefix.get(),
            "start_num": self.start_num.get(),
            "appearance_mode": self.appearance_mode.get(),
            "content": self.content_text.get("1.0", "end-1c"),
            "titles": self.titles_text.get("1.0", "end-1c")
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(current_data, f, indent=4)

    def setup_ui(self):
        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="⚡ AutoContent", 
                                      font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 0))
        
        self.sub_logo = ctk.CTkLabel(self.sidebar_frame, text="PRO EDITION", 
                                    font=ctk.CTkFont(size=10, weight="bold"), text_color="#3B8ED0")
        self.sub_logo.grid(row=1, column=0, padx=20, pady=(0, 30))

        self.generate_btn = ctk.CTkButton(self.sidebar_frame, text="GENERATE NOW", 
                                         command=self.start_generation, height=50,
                                         corner_radius=10, font=ctk.CTkFont(size=15, weight="bold"),
                                         fg_color="#3B8ED0", hover_color="#2B6DA0")
        self.generate_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.status_badge = ctk.CTkLabel(self.sidebar_frame, text="● SYSTEM READY", 
                                        font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ECC71")
        self.status_badge.grid(row=3, column=0, padx=20, pady=5)

        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", anchor="w")
        self.mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                          variable=self.appearance_mode, command=self.change_appearance_mode)
        self.mode_menu.grid(row=7, column=0, padx=20, pady=(10, 20))

        # --- MAIN ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, corner_radius=15)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        
        self.tab_editor = self.tabview.add("📝 CONTENT EDITOR")
        self.tab_settings = self.tabview.add("⚙️ GLOBAL SETTINGS")
        self.tab_console = self.tabview.add("🖥️ SYSTEM CONSOLE")

        # Editor
        self.tab_editor.grid_columnconfigure(0, weight=1)
        self.tab_editor.grid_columnconfigure(1, weight=1)
        self.tab_editor.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.tab_editor, text="Body Content (Markdown)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        ctk.CTkLabel(self.tab_editor, text="Title List (One Per Line)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")

        self.content_text = ctk.CTkTextbox(self.tab_editor, corner_radius=10, undo=True)
        self.content_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.titles_text = ctk.CTkTextbox(self.tab_editor, corner_radius=10, undo=True)
        self.titles_text.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Settings
        self.tab_settings.grid_columnconfigure(0, weight=1)
        settings_card = ctk.CTkFrame(self.tab_settings, corner_radius=15)
        settings_card.pack(fill="x", padx=20, pady=20)
        
        row1 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row1, text="Filename Prefix:").pack(side="left", padx=(0, 10))
        ctk.CTkEntry(row1, textvariable=self.prefix, width=150).pack(side="left", padx=(0, 30))
        ctk.CTkLabel(row1, text="Starting Number:").pack(side="left", padx=(0, 10))
        ctk.CTkEntry(row1, textvariable=self.start_num, width=100).pack(side="left")

        row2 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(row2, text="Output Directory:").pack(anchor="w")
        path_row = ctk.CTkFrame(row2, fg_color="transparent")
        path_row.pack(fill="x")
        ctk.CTkEntry(path_row, textvariable=self.output_folder).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(path_row, text="Browse", width=80, command=self.browse_dir, 
                     fg_color="gray30", hover_color="gray40").pack(side="right")

        # Console
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(1, weight=1)
        self.progress_bar = ctk.CTkProgressBar(self.tab_console, height=12)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.progress_bar.set(0)
        self.log_text = ctk.CTkTextbox(self.tab_console, corner_radius=10, 
                                      font=ctk.CTkFont(family="Consolas", size=13),
                                      fg_color=("#F0F0F0", "#121212"))
        self.log_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_text.configure(state="disabled")

    def browse_dir(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_folder.set(dirname)
            self.save_settings()

    def change_appearance_mode(self, mode):
        ctk.set_appearance_mode(mode)
        self.save_settings()

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"> {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def restore_work(self):
        # Restore editor text from cookies
        if self.settings.get("content"):
            self.content_text.insert("1.0", self.settings.get("content"))
        elif (BASE_DIR / "content.md").exists():
            self.content_text.insert("1.0", (BASE_DIR / "content.md").read_text(encoding="utf-8"))
            
        if self.settings.get("titles"):
            self.titles_text.insert("1.0", self.settings.get("titles"))
        elif (BASE_DIR / "titles.md").exists():
            self.titles_text.insert("1.0", (BASE_DIR / "titles.md").read_text(encoding="utf-8"))

    def start_generation(self):
        # Auto-save before running
        self.save_settings()
        
        self.generate_btn.configure(state="disabled", text="RUNNING...")
        self.status_badge.configure(text="● GENERATING", text_color="#F1C40F")
        self.tabview.set("🖥️ SYSTEM CONSOLE")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
        thread = threading.Thread(target=self.run_generation)
        thread.daemon = True
        thread.start()

    def run_generation(self):
        try:
            raw_content = self.content_text.get("1.0", "end-1c")
            raw_titles = self.titles_text.get("1.0", "end-1c")
            output_dir = Path(self.output_folder.get())
            prefix = self.prefix.get()
            try:
                start_n = int(self.start_num.get())
            except:
                start_n = 1
            if not raw_content.strip():
                self.after(0, lambda: messagebox.showerror("Error", "Editor content is empty!"))
                return
            titles = [l.strip() for l in raw_titles.splitlines() if l.strip()]
            if not titles:
                self.after(0, lambda: messagebox.showerror("Error", "Title list is empty!"))
                return
            output_dir.mkdir(parents=True, exist_ok=True)
            total = len(titles)
            self.after(0, lambda: self.log(f"Initializing Engine: {total} units planned"))
            for i, title in enumerate(titles):
                file_num = start_n + i
                filename = f"{prefix}{file_num:02d}.pdf"
                filepath = output_dir / filename
                self.build_pdf(filepath, title, raw_content)
                progress = (i + 1) / total
                self.after(0, lambda p=progress, m=f"SUCCESS: {filename}": [self.progress_bar.set(p), self.log(m)])
            self.after(0, lambda: [self.status_badge.configure(text="● SYSTEM READY", text_color="#2ECC71"), 
                                  self.log("\nBatch complete. Systems stable."), 
                                  messagebox.showinfo("AutoContent Pro", f"Successfully generated {total} PDFs!")])
        except Exception as err:
            err_msg = str(err)
            self.after(0, lambda msg=err_msg: [self.status_badge.configure(text="● ENGINE ERROR", text_color="#E74C3C"), 
                                              self.log(f"CRITICAL ERROR: {msg}"), 
                                              messagebox.showerror("Error", msg)])
        finally:
            self.after(0, lambda: self.generate_btn.configure(state="normal", text="GENERATE NOW"))

    def build_pdf(self, filepath, title, raw_markdown):
        from fpdf.fonts import FontFace
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_text_color(26, 26, 46)
        pdf.set_font("helvetica", "B", 20)
        pdf.multi_cell(0, 12, title)
        pdf.set_draw_color(59, 142, 208)
        pdf.set_line_width(0.8)
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        md_clean = re.sub(r"^#\s+.*", "", raw_markdown, count=1, flags=re.MULTILINE)
        html_content = markdown(md_clean, extensions=['extra', 'sane_lists'])
        final_html = f'<font face="helvetica" size="12">{html_content}</font>'
        
        # FIXED: Using "B" and "I" style strings which are universally supported
        tag_styles = {
            "h2": FontFace(emphasis="B", size_pt=16, color=(26, 26, 46)),
            "h3": FontFace(emphasis="B", size_pt=14, color=(26, 26, 46)),
            "h4": FontFace(emphasis="B", size_pt=12, color=(0, 0, 0)),
            "p": FontFace(size_pt=12, color=(40, 40, 40)),
            "li": FontFace(size_pt=12, color=(40, 40, 40)),
            "blockquote": FontFace(emphasis="I", size_pt=11, color=(85, 85, 85)),
        }
        pdf.write_html(final_html, tag_styles=tag_styles)
        pdf.output(str(filepath))

if __name__ == "__main__":
    app = AutoContentPro()
    # Ensure save on close
    app.protocol("WM_DELETE_WINDOW", lambda: [app.save_settings(), app.destroy()])
    app.mainloop()

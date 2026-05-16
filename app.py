import os
import re
import sys
import json
import hashlib
import threading
import urllib.request
import webbrowser
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from fpdf import FPDF
from markdown import markdown

# Initialize environment
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    EXE_DIR = Path(sys.executable).parent
else:
    EXE_DIR = Path(__file__).resolve().parent

USER_DATA_DIR = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming") / "AutoContent Pro"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = USER_DATA_DIR / "settings.json"
LICENSE_FILE = USER_DATA_DIR / "license.key"
LEGACY_SETTINGS_FILE = EXE_DIR / "settings.json"
LEGACY_LICENSE_FILE = EXE_DIR / "license.key"
LOGO_PATH = get_resource_path(os.path.join("image", "logo.png"))
ICON_PATH = get_resource_path(os.path.join("image", "logo.ico"))

# App Meta
APP_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/imsurajj/autocontent/main/version.json"

# Security Config (Pro Hashing)
# The app validates the user-facing activation key by hashing it.
# The actual plain key is not stored in readable form here.
KEY_HASH = "d98d6111195555816560a714cbdd9bda62ff006f7fd4757ba188b3852cbedb27"
LICENSE_DURATION_DAYS = 30

# Placeholders
CONTENT_PLACEHOLDER = "# Main Header\n\nWrite your content here using Markdown syntax.\n\n## Sub-section\n- List Item 1\n- List Item 2"
TITLES_PLACEHOLDER = "Example Title 1\nExample Title 2\nExample Title 3"

# Default fallback settings
DEFAULT_SETTINGS = {
    "output_folder": str(USER_DATA_DIR / "output_pdfs"),
    "prefix": "doc",
    "start_num": "1",
    "appearance_mode": "Dark",
    "content": "",
    "titles": ""
}

class AutoContentPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AutoContent Pro — Ultimate Engine v{APP_VERSION}")
        self.geometry("1100x750")
        
        try:
            if os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
        except:
            pass

        self.settings = self.load_settings()
        self.appearance_mode = tk.StringVar(value=self.settings.get("appearance_mode"))
        ctk.set_appearance_mode(self.appearance_mode.get())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.is_activated = False

        self.check_license()

    def normalize_key(self, key):
        normalized = re.sub(r"[\s\-]+", "", key).upper()
        return normalized

    def get_license_path(self):
        if LICENSE_FILE.exists():
            return LICENSE_FILE
        if LEGACY_LICENSE_FILE.exists():
            return LEGACY_LICENSE_FILE
        return LICENSE_FILE

    def check_license(self):
        is_valid = False
        license_path = self.get_license_path()
        if license_path.exists():
            try:
                with open(license_path, "r") as f:
                    data = json.load(f)
                    activation_date_str = data.get("date", "")
                    license_hash = data.get("key", "")
                    if "T" in activation_date_str:
                        activation_date = datetime.fromisoformat(activation_date_str)
                    else:
                        activation_date = datetime.strptime(activation_date_str, "%Y-%m-%d")
                    
                    if license_hash == KEY_HASH and datetime.now() < activation_date + timedelta(days=LICENSE_DURATION_DAYS):
                        is_valid = True
            except Exception:
                pass
        
        self.is_activated = is_valid
        self.show_main_app()
        if self.is_activated:
            threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        try:
            with urllib.request.urlopen(VERSION_URL, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("version", APP_VERSION)
                update_url = data.get("url", "")
                if latest_version > APP_VERSION:
                    self.after(0, lambda: self.notify_update(latest_version, update_url))
        except:
            pass

    def notify_update(self, version, url):
        self.log(f"🔔 UPDATE AVAILABLE: v{version}")
        msg = f"A new version (v{version}) is available!\nWould you like to download it now?"
        if messagebox.askyesno("Update Available", msg):
            webbrowser.open(url)

    def show_activation_screen(self):
        for child in self.winfo_children():
            child.destroy()

        self.activation_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.activation_frame.grid(row=0, column=0, sticky="nsew")
        self.activation_frame.grid_columnconfigure(0, weight=1)
        self.activation_frame.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self.activation_frame, fg_color="transparent")
        container.grid(row=0, column=0)

        ctk.CTkLabel(container, text="🛡️", font=ctk.CTkFont(size=80)).pack(pady=(0, 20))
        ctk.CTkLabel(container, text="Activation Required", font=ctk.CTkFont(size=32, weight="bold")).pack(pady=5)
        ctk.CTkLabel(container, text="Your license is missing or has expired.\nEnter your key to unlock the Ultimate Engine.", 
                    font=ctk.CTkFont(size=14), text_color="gray70").pack(pady=(5, 30))
        
        self.key_entry = ctk.CTkEntry(container, placeholder_text="Enter Key...", 
                                     show="•", width=380, height=50, 
                                     font=ctk.CTkFont(family="Consolas", size=16),
                                     border_width=1, corner_radius=12)
        self.key_entry.pack(pady=10)
        self.key_entry.bind("<Return>", lambda e: self.verify_license())
        
        self.activate_btn = ctk.CTkButton(container, text="ACTIVATE NOW", command=self.verify_license, 
                                         fg_color="#3B8ED0", hover_color="#2B6DA0", 
                                         height=55, width=300, font=ctk.CTkFont(size=16, weight="bold"),
                                         corner_radius=15)
        self.activate_btn.pack(pady=(25, 0))
        ctk.CTkLabel(container, text="Enter the activation key, not the hidden hash.", 
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(pady=(10, 0))

    def verify_license(self):
        user_key = self.normalize_key(self.activation_key_entry.get())
        user_hash = hashlib.sha256(user_key.encode()).hexdigest()
        
        if user_hash == KEY_HASH:
            with open(LICENSE_FILE, "w") as f:
                json.dump({"date": datetime.now().isoformat(), "key": user_hash}, f)
            self.update_activation_state(True)
            threading.Thread(target=self.check_for_updates, daemon=True).start()
        else:
            messagebox.showerror(
                "Error",
                "Invalid License Key! Please enter the activation key exactly as provided, not the internal hash."
            )

    def show_main_app(self):
        for child in self.winfo_children():
            child.destroy()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.output_folder = tk.StringVar(value=self.settings.get("output_folder"))
        self.prefix = tk.StringVar(value=self.settings.get("prefix"))
        self.start_num = tk.StringVar(value=self.settings.get("start_num"))
        self.setup_ui()
        self.restore_work()
        self.update_activation_state(self.is_activated)

    def load_settings(self):
        for path in (SETTINGS_FILE, LEGACY_SETTINGS_FILE):
            if path.exists():
                try:
                    with open(path, "r") as f:
                        return {**DEFAULT_SETTINGS, **json.load(f)}
                except:
                    pass
        return DEFAULT_SETTINGS

    def save_settings(self):
        if not hasattr(self, 'content_text'):
            return
        content = self.content_text.get("1.0", "end-1c")
        if content == CONTENT_PLACEHOLDER:
            content = ""
        titles = self.titles_text.get("1.0", "end-1c")
        if titles == TITLES_PLACEHOLDER:
            titles = ""
        current_data = {
            "output_folder": self.output_folder.get(),
            "prefix": self.prefix.get(),
            "start_num": self.start_num.get(),
            "appearance_mode": self.appearance_mode.get(),
            "content": content,
            "titles": titles
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(current_data, f, indent=4)

    def setup_ui(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        try:
            logo_img = Image.open(LOGO_PATH)
            self.logo_image = ctk.CTkImage(logo_img, size=(70, 70))
            ctk.CTkLabel(self.sidebar_frame, image=self.logo_image, text="").grid(row=0, column=0, padx=20, pady=(30, 0))
        except:
            ctk.CTkLabel(self.sidebar_frame, text="⚡", font=ctk.CTkFont(size=40)).grid(row=0, column=0, padx=20, pady=(30, 0))
        ctk.CTkLabel(self.sidebar_frame, text="AutoContent Pro", font=ctk.CTkFont(size=20, weight="bold")).grid(row=1, column=0, padx=20, pady=(10, 0))
        ctk.CTkLabel(self.sidebar_frame, text="ULTIMATE EDITION", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3B8ED0").grid(row=2, column=0, padx=20, pady=(0, 20))
        self.generate_btn = ctk.CTkButton(self.sidebar_frame, text="GENERATE NOW", command=self.start_generation, height=50, corner_radius=10, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#3B8ED0", hover_color="#2B6DA0")
        self.generate_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.status_badge = ctk.CTkLabel(self.sidebar_frame, text="● SYSTEM READY", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ECC71")
        self.status_badge.grid(row=4, column=0, padx=20, pady=5)
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], variable=self.appearance_mode, command=self.change_appearance_mode)
        self.mode_menu.grid(row=7, column=0, padx=20, pady=(10, 20))
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0)
        self.main_container.grid_rowconfigure(1, weight=1)

        self.activation_card = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.activation_card.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=0)
        self.activation_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.activation_card, text="Activation required to enable app features.", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.activation_key_entry = ctk.CTkEntry(self.activation_card, placeholder_text="Enter Activation Key...", show="•", width=380, height=40, font=ctk.CTkFont(family="Consolas", size=14), border_width=1, corner_radius=12)
        self.activation_key_entry.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.activation_key_entry.bind("<Return>", lambda e: self.verify_license())
        self.activation_submit_btn = ctk.CTkButton(self.activation_card, text="ACTIVATE", command=self.verify_license, fg_color="#3B8ED0", hover_color="#2B6DA0", height=45, width=180, font=ctk.CTkFont(size=14, weight="bold"), corner_radius=12)
        self.activation_submit_btn.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")
        ctk.CTkLabel(self.activation_card, text="Your install activation key enables generation and settings.", font=ctk.CTkFont(size=12), text_color="gray60").grid(row=3, column=0, padx=20, pady=(0, 20), sticky="w")

        self.tabview = ctk.CTkTabview(self.main_container, corner_radius=15)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.tab_editor = self.tabview.add("📝 CONTENT EDITOR")
        self.tab_settings = self.tabview.add("⚙️ GLOBAL SETTINGS")
        self.tab_console = self.tabview.add("🖥️ SYSTEM CONSOLE")
        self.tab_editor.grid_columnconfigure(0, weight=1)
        self.tab_editor.grid_columnconfigure(1, weight=1)
        self.tab_editor.grid_rowconfigure(1, weight=1)
        self.content_text = ctk.CTkTextbox(self.tab_editor, corner_radius=10, undo=True)
        self.content_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.content_text.bind("<FocusIn>", lambda e: self.clear_placeholder(self.content_text, CONTENT_PLACEHOLDER))
        self.content_text.bind("<FocusOut>", lambda e: self.add_placeholder(self.content_text, CONTENT_PLACEHOLDER))
        self.titles_text = ctk.CTkTextbox(self.tab_editor, corner_radius=10, undo=True)
        self.titles_text.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.titles_text.bind("<FocusIn>", lambda e: self.clear_placeholder(self.titles_text, TITLES_PLACEHOLDER))
        self.titles_text.bind("<FocusOut>", lambda e: self.add_placeholder(self.titles_text, TITLES_PLACEHOLDER))
        self.tab_settings.grid_columnconfigure(0, weight=1)
        settings_card = ctk.CTkFrame(self.tab_settings, corner_radius=15)
        settings_card.pack(fill="x", padx=20, pady=20)
        row1 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=15)
        self.prefix_entry = ctk.CTkEntry(row1, textvariable=self.prefix, width=150)
        self.prefix_entry.pack(side="left", padx=(10, 30))
        self.start_num_entry = ctk.CTkEntry(row1, textvariable=self.start_num, width=100)
        self.start_num_entry.pack(side="left")
        row2 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 20))
        self.output_folder_entry = ctk.CTkEntry(row2, textvariable=self.output_folder)
        self.output_folder_entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
        self.browse_btn = ctk.CTkButton(row2, text="Browse", width=80, command=self.browse_dir)
        self.browse_btn.pack(side="right")
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(1, weight=1)
        self.progress_bar = ctk.CTkProgressBar(self.tab_console, height=12)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.log_text = ctk.CTkTextbox(self.tab_console, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=13))
        self.log_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_text.configure(state="disabled")

    def update_activation_state(self, activated):
        self.is_activated = activated
        if activated:
            self.activation_card.grid_remove()
            self.generate_btn.configure(state="normal")
            self.content_text.configure(state="normal")
            self.titles_text.configure(state="normal")
            self.prefix_entry.configure(state="normal")
            self.start_num_entry.configure(state="normal")
            self.output_folder_entry.configure(state="normal")
            self.browse_btn.configure(state="normal")
            self.activation_key_entry.delete(0, "end")
            self.status_badge.configure(text="● SYSTEM READY", text_color="#2ECC71")
        else:
            self.activation_card.grid()
            self.generate_btn.configure(state="disabled")
            self.content_text.configure(state="disabled")
            self.titles_text.configure(state="disabled")
            self.prefix_entry.configure(state="disabled")
            self.start_num_entry.configure(state="disabled")
            self.output_folder_entry.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            self.status_badge.configure(text="● ACTIVATION REQUIRED", text_color="#E74C3C")

    def add_placeholder(self, widget, placeholder):
        val = widget.get("1.0", "end-1c").strip()
        if not val or val == placeholder:
            widget.delete("1.0", "end")
            widget.insert("1.0", placeholder)
            widget.configure(text_color="gray40")

    def clear_placeholder(self, widget, placeholder):
        if widget.get("1.0", "end-1c") == placeholder:
            widget.delete("1.0", "end")
            widget.configure(text_color=ctk.ThemeManager.theme["CTkTextbox"]["text_color"])

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
        content = self.settings.get("content")
        if content:
            self.content_text.insert("1.0", content)
        else:
            self.add_placeholder(self.content_text, CONTENT_PLACEHOLDER)
        titles = self.settings.get("titles")
        if titles:
            self.titles_text.insert("1.0", titles)
        else:
            self.add_placeholder(self.titles_text, TITLES_PLACEHOLDER)

    def start_generation(self):
        self.save_settings()
        self.generate_btn.configure(state="disabled", text="RUNNING...")
        self.status_badge.configure(text="● GENERATING", text_color="#F1C40F")
        self.tabview.set("🖥️ SYSTEM CONSOLE")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        try:
            raw_content = self.content_text.get("1.0", "end-1c")
            if raw_content == CONTENT_PLACEHOLDER:
                raw_content = ""
            raw_titles = self.titles_text.get("1.0", "end-1c")
            if raw_titles == TITLES_PLACEHOLDER:
                raw_titles = ""
            output_dir = Path(self.output_folder.get())
            prefix = self.prefix.get()
            try:
                start_n = int(self.start_num.get())
            except:
                start_n = 1
            if not raw_content.strip():
                self.after(0, lambda: messagebox.showerror("Error", "Content is empty!"))
                return
            titles = [l.strip() for l in raw_titles.splitlines() if l.strip()]
            if not titles:
                self.after(0, lambda: messagebox.showerror("Error", "No titles provided!"))
                return
            output_dir.mkdir(parents=True, exist_ok=True)
            total = len(titles)
            for i, title in enumerate(titles):
                file_num = start_n + i
                filename = f"{prefix}{file_num:02d}.pdf"
                filepath = output_dir / filename
                self.build_pdf(filepath, title, raw_content)
                progress = (i + 1) / total
                self.after(0, lambda p=progress, m=f"SUCCESS: {filename}": [self.progress_bar.set(p), self.log(m)])
            self.after(0, lambda: [
                self.status_badge.configure(text="● SYSTEM READY", text_color="#2ECC71"),
                messagebox.showinfo("AutoContent Pro", "Batch complete!")
            ])
        except Exception as err:
            m = str(err)
            self.after(0, lambda m=m: [
                self.status_badge.configure(text="● ENGINE ERROR", text_color="#E74C3C"),
                self.log(f"CRITICAL ERROR: {m}"),
                messagebox.showerror("Error", m)
            ])
        finally:
            self.after(0, lambda: self.generate_btn.configure(state="normal", text="GENERATE NOW"))

    def build_pdf(self, filepath, title, raw_markdown):
        from fpdf.fonts import FontFace
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("helvetica", "B", 20)
        pdf.multi_cell(0, 12, title)
        pdf.set_draw_color(59, 142, 208)
        pdf.set_line_width(0.8)
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        md_clean = re.sub(r"^#\s+.*", "", raw_markdown, count=1, flags=re.MULTILINE)
        html_content = markdown(md_clean, extensions=['extra', 'sane_lists'])
        tag_styles = {
            "h2": FontFace(emphasis="B", size_pt=16, color=(26, 26, 46)),
            "h3": FontFace(emphasis="B", size_pt=14, color=(26, 26, 46)),
            "p": FontFace(size_pt=12, color=(40, 40, 40)),
            "li": FontFace(size_pt=12, color=(40, 40, 40)),
            "blockquote": FontFace(emphasis="I", size_pt=11, color=(85, 85, 85))
        }
        pdf.write_html(f'<font face="helvetica" size="12">{html_content}</font>', tag_styles=tag_styles)
        pdf.output(str(filepath))

    def on_closing(self):
        try:
            self.save_settings()
        except:
            pass
        self.quit()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = AutoContentPro()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

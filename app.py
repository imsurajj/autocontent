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

# Unicode font support for PDF export
def get_unicode_font_path(font_map=None, requested_font=None):
    if requested_font and requested_font != "Auto" and font_map:
        requested_path = font_map.get(requested_font)
        if requested_path and requested_path.exists():
            return requested_path

    if requested_font and requested_font != "Auto" and font_map:
        for candidate in font_map.values():
            try:
                if candidate and candidate.exists():
                    return candidate
            except Exception:
                continue

    candidates = []
    # Embedded or project font file path if bundled with the app
    candidates.append(Path(get_resource_path(os.path.join("fonts", "DejaVuSans.ttf"))))

    if sys.platform.startswith("win"):
        candidates += [
            Path("C:/Windows/Fonts/arialuni.ttf"),
            Path("C:/Windows/Fonts/DejaVuSans.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/verdana.ttf"),
        ]
    elif sys.platform == "darwin":
        candidates += [
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/Library/Fonts/DejaVuSans.ttf"),
            Path("/Library/Fonts/NotoSans-Regular.ttf"),
        ]
    else:
        candidates += [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        ]

    for candidate in candidates:
        try:
            if candidate and candidate.exists():
                return candidate
        except Exception:
            continue
    return None


def scan_system_fonts():
    font_dirs = []
    font_map = {}

    resource_fonts = Path(get_resource_path(os.path.join("fonts")))
    if resource_fonts.exists() and resource_fonts.is_dir():
        font_dirs.append(resource_fonts)

    if sys.platform.startswith("win"):
        font_dirs.append(Path("C:/Windows/Fonts"))
    elif sys.platform == "darwin":
        font_dirs += [
            Path("/Library/Fonts"),
            Path("~/Library/Fonts").expanduser()
        ]
    else:
        font_dirs += [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path("~/.local/share/fonts").expanduser(),
            Path("~/.fonts").expanduser()
        ]

    valid_exts = {".ttf", ".otf", ".ttc"}
    for font_dir in font_dirs:
        try:
            if font_dir.exists():
                for font_file in font_dir.rglob("*"):
                    if font_file.suffix.lower() in valid_exts and font_file.is_file():
                        display_name = font_file.stem
                        duplicate = 1
                        while display_name in font_map:
                            duplicate += 1
                            display_name = f"{font_file.stem} ({duplicate})"
                        font_map[display_name] = font_file
        except Exception:
            continue

    return font_map


def contains_unicode(text):
    return bool(re.search(r"[^\x00-]", text))

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
    "pdf_font": "Auto",
    "content": "",
    "titles": ""
}

class ScrollableDropdown(ctk.CTkToplevel):
    def __init__(self, widget, values, command=None, variable=None):
        super().__init__()
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.widget = widget
        self.values = values
        self.command = command
        self.variable = variable

        # Show exactly 10 items if more than 10
        item_height = 30
        max_items = 10
        height = min(len(values), max_items) * item_height + 15
        width = widget.winfo_width()
        
        # Position right below the option menu
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        
        self.frame = ctk.CTkScrollableFrame(self, fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][mode_idx], corner_radius=5)
        self.frame.pack(expand=True, fill="both")
        
        for val in values:
            btn = ctk.CTkButton(
                self.frame, text=val, fg_color="transparent", anchor="w", 
                text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"][mode_idx],
                hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"][mode_idx],
                command=lambda v=val: self.select(v),
                height=28
            )
            btn.pack(fill="x", pady=1, padx=2)
            
        self.focus_set()
        self.bind("<FocusOut>", lambda e: self.destroy())
        
    def select(self, value):
        if self.variable:
            self.variable.set(value)
        self.widget.set(value)
        if self.command:
            self.command(value)
        self.destroy()

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
        self.font_map = scan_system_fonts()
        default_font = self.settings.get("pdf_font", "Auto")
        if default_font != "Auto" and default_font not in self.font_map:
            default_font = "Auto"
        self.pdf_font = tk.StringVar(value=default_font)
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
                    with open(path, "r", encoding="utf-8") as f:
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
            "pdf_font": self.pdf_font.get(),
            "content": content,
            "titles": titles
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=4)

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

        content_frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        self.titles_frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        self.titles_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.titles_frame.grid_columnconfigure(1, weight=1)
        self.titles_frame.grid_rowconfigure(1, weight=1)

        # Fetch theme colors
        bg_color_dynamic = ctk.ThemeManager.theme.get("CTkTextbox", {}).get("fg_color", ["#F9F9FA", "#1D1E1E"])
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        bg_color_static = bg_color_dynamic[mode_idx] if isinstance(bg_color_dynamic, list) else bg_color_dynamic

        # Add heading to the content box
        content_heading = ctk.CTkLabel(
            content_frame,
            text="Markdown Content",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold")
        )
        content_heading.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

        # Shared font ensures identical pixel sizes between tk.Text and ctk.CTkTextbox
        editor_font = ctk.CTkFont(family="Consolas", size=14)

        # Wrapper to make them look like a single input
        content_wrapper = ctk.CTkFrame(content_frame, corner_radius=10, fg_color=bg_color_dynamic, border_width=0)
        content_wrapper.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(5, 0))
        content_wrapper.grid_columnconfigure(1, weight=1)
        content_wrapper.grid_rowconfigure(0, weight=1)

        self.content_gutter = tk.Text(
            content_wrapper,
            width=4,
            padx=5,
            pady=0,
            wrap="none",
            bd=0,
            highlightthickness=0,
            bg=bg_color_static,
            fg="#858585",  # Faded numbering like VS Code
            font=editor_font,
            state="normal"
        )
        self.content_gutter.grid(row=0, column=0, sticky="ns", pady=2)
        self.content_text = ctk.CTkTextbox(content_wrapper, corner_radius=0, fg_color="transparent", border_width=0, undo=True, font=editor_font, wrap="none")
        self.content_text.grid(row=0, column=1, sticky="nsew")
        self.content_text._y_scrollbar.configure(width=0)
        self.content_text._x_scrollbar.configure(width=0)
        
        # Perfect padding match
        pad_y = self.content_text._textbox.cget("pady")
        self.content_gutter.configure(pady=pad_y)

        # Add heading to the titles box
        titles_heading = ctk.CTkLabel(
            self.titles_frame,
            text="Document Titles",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold")
        )
        titles_heading.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

        titles_wrapper = ctk.CTkFrame(self.titles_frame, corner_radius=10, fg_color=bg_color_dynamic, border_width=0)
        titles_wrapper.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(5, 0))
        titles_wrapper.grid_columnconfigure(1, weight=1)
        titles_wrapper.grid_rowconfigure(0, weight=1)

        self.titles_gutter = tk.Text(
            titles_wrapper,
            width=4,
            padx=5,
            pady=0,
            wrap="none",
            bd=0,
            highlightthickness=0,
            bg=bg_color_static,
            fg="#858585",
            font=editor_font,
            state="normal"
        )
        self.titles_gutter.grid(row=0, column=0, sticky="ns", pady=2)
        self.titles_text = ctk.CTkTextbox(titles_wrapper, corner_radius=0, fg_color="transparent", border_width=0, undo=True, font=editor_font, wrap="none")
        self.titles_text.grid(row=0, column=1, sticky="nsew")
        self.titles_text._y_scrollbar.configure(width=0)
        self.titles_text._x_scrollbar.configure(width=0)
        
        # Perfect padding match
        self.titles_gutter.configure(pady=pad_y)

        # Bindings for updating line numbers
        self.content_text.bind("<KeyRelease>", self.refresh_line_gutters)
        self.content_text.bind("<MouseWheel>", lambda e: self.after(10, lambda: self.sync_gutter_scroll(self.content_text, self.content_gutter)))
        self.content_text.bind("<Return>", self.refresh_line_gutters)
        self.content_text.bind("<BackSpace>", self.refresh_line_gutters)
        self.content_text._textbox.bind("<Configure>", lambda e: self.sync_gutter_scroll(self.content_text, self.content_gutter))

        self.titles_text.bind("<KeyRelease>", self.refresh_line_gutters)
        self.titles_text.bind("<MouseWheel>", lambda e: self.after(10, lambda: self.sync_gutter_scroll(self.titles_text, self.titles_gutter)))
        self.titles_text.bind("<Return>", self.refresh_line_gutters)
        self.titles_text.bind("<BackSpace>", self.refresh_line_gutters)
        self.titles_text._textbox.bind("<Configure>", lambda e: self.sync_gutter_scroll(self.titles_text, self.titles_gutter))

        # Placeholder bindings removed to prevent focus-based emoji deletion
        # self.content_text.bind("<FocusIn>", ...) 
        # self.content_text.bind("<FocusOut>", ...) 
        
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

        font_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        font_row.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(font_row, text="PDF Export Font:", font=ctk.CTkFont(size=13)).pack(side="left")
        font_values = ["Auto"] + list(self.font_map.keys())
        self.font_menu = ctk.CTkOptionMenu(font_row, values=font_values, variable=self.pdf_font, command=self.on_font_change)
        self.font_menu._open_dropdown_menu = lambda *args: ScrollableDropdown(self.font_menu, font_values, self.on_font_change, self.pdf_font)
        self.font_menu.pack(side="left", padx=(10, 10), fill="x", expand=True)
        ctk.CTkLabel(font_row, text="Auto uses built-in PDF fonts unless a custom font is required.", font=ctk.CTkFont(size=12), text_color="gray60").pack(side="left")

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
        if not val:
            widget.delete("1.0", "end")
            widget.insert("1.0", placeholder)
            widget.configure(text_color="gray40")
            self.refresh_line_gutters()

    def update_gutter(self, text_widget, gutter_widget):
        content = text_widget.get("1.0", "end-1c")
        if content.strip() == CONTENT_PLACEHOLDER or not content.strip():
            current_lines = 0
        else:
            try:
                current_lines = int(text_widget.index("end-1c").split(".")[0])
            except Exception:
                current_lines = content.count("\n") + 1
        total_lines = current_lines + 5 if current_lines > 0 else 5
        line_text = "\n".join(str(i) for i in range(1, total_lines + 1)) + "\n"
        gutter_widget.configure(state="normal")
        gutter_widget.delete("1.0", "end")
        gutter_widget.insert("1.0", line_text)
        gutter_widget.configure(state="disabled")
        try:
            gutter_widget.yview_moveto(text_widget.yview()[0])
        except Exception:
            pass

    def refresh_line_gutters(self, event=None):
        if hasattr(self, 'content_gutter') and hasattr(self, 'titles_gutter'):
            self.update_gutter(self.content_text, self.content_gutter)
            self.update_gutter(self.titles_text, self.titles_gutter)

    def sync_gutter_scroll(self, text_widget, gutter_widget, event=None):
        try:
            gutter_widget.yview_moveto(text_widget.yview()[0])
        except Exception:
            pass

    def on_font_change(self, value):
        self.save_settings()

    def clear_placeholder(self, widget, placeholder):
        # Only clear if it's precisely the placeholder text
        content = widget.get("1.0", "end-1c")
        if content == placeholder:
            widget.delete("1.0", "end")
            mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
            text_color = ctk.ThemeManager.theme.get("CTkTextbox", {}).get("text_color", ["#000000", "#FFFFFF"])[mode_idx]
            widget.configure(text_color=text_color)
            self.refresh_line_gutters()

    def browse_dir(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_folder.set(dirname)
            self.save_settings()

    def change_appearance_mode(self, mode):
        ctk.set_appearance_mode(mode)
        self.save_settings()
        
        # Update static colors for tk.Text gutters
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        bg_color_dynamic = ctk.ThemeManager.theme.get("CTkTextbox", {}).get("fg_color", ["#F9F9FA", "#1D1E1E"])
        bg_color_static = bg_color_dynamic[mode_idx] if isinstance(bg_color_dynamic, list) else bg_color_dynamic
        
        if hasattr(self, 'content_gutter'):
            self.content_gutter.configure(bg=bg_color_static)
        if hasattr(self, 'titles_gutter'):
            self.titles_gutter.configure(bg=bg_color_static)

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
        self.refresh_line_gutters()

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
        
        selected_font = self.pdf_font.get() if hasattr(self, 'pdf_font') else "Auto"
        font_map = getattr(self, 'font_map', {})

        def generate(use_fallback=False):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            
            font_family = "helvetica"
            
            def add_font_with_bold(family, reg_path):
                pdf.add_font(family, "", str(reg_path), uni=True)
                # Intelligent search for bold variant on Windows/System
                p = Path(reg_path)
                candidates = [
                    p.parent / (p.stem + "bd" + p.suffix),   # e.g., arialbd.ttf
                    p.parent / (p.stem + "b" + p.suffix),    # e.g., verdanab.ttf
                    p.parent / (p.stem + "-Bold" + p.suffix),# e.g., DejaVuSans-Bold.ttf
                    p.parent / (p.stem + "Bold" + p.suffix), # e.g., CalibriBold.ttf
                    p.parent / (p.stem + "_Bold" + p.suffix) # e.g., Custom_Bold.ttf
                ]
                bold_path = None
                for c in candidates:
                    if c.exists():
                        bold_path = c
                        break
                
                if bold_path:
                    pdf.add_font(family, "B", str(bold_path), uni=True)
                else:
                    # Fallback to same file if no bold found
                    pdf.add_font(family, "B", str(reg_path), uni=True)

            if use_fallback:
                font_path = get_unicode_font_path(font_map)
                if font_path is None:
                    raise RuntimeError("No fallback unicode font found.")
                font_family = "AutoContentUnicode"
                add_font_with_bold(font_family, font_path)
            elif selected_font and selected_font != "Auto":
                font_path = get_unicode_font_path(font_map, selected_font)
                if font_path is None:
                    raise RuntimeError(f"Selected PDF font '{selected_font}' was not found on this system.")
                font_family = selected_font
                add_font_with_bold(font_family, font_path)
            
            pdf.set_font(font_family, style="B", size=20)
            
            # Faux bold by overprinting slightly to the right to guarantee bold effect
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(0, 12, title)
            pdf.set_xy(x + 0.3, y)
            pdf.multi_cell(0, 12, title)
            
            pdf.set_draw_color(59, 142, 208)
            pdf.set_line_width(0.8)
            pdf.ln(2)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(10)
            
            md_clean = re.sub(r"^#\s+.*", "", raw_markdown, count=1, flags=re.MULTILINE)
            html_content = markdown(md_clean, extensions=['extra', 'sane_lists'])
            tag_styles = {
                "h1": FontFace(emphasis="B", size_pt=20, color=(26, 26, 46)),
                "h2": FontFace(emphasis="B", size_pt=16, color=(26, 26, 46)),
                "h3": FontFace(emphasis="B", size_pt=14, color=(26, 26, 46)),
                "p": FontFace(size_pt=12, color=(40, 40, 40)),
                "li": FontFace(size_pt=12, color=(40, 40, 40)),
                "blockquote": FontFace(emphasis="I", size_pt=11, color=(85, 85, 85))
            }
            pdf.write_html(html_content, tag_styles=tag_styles)
            return pdf

        try:
            pdf = generate(use_fallback=False)
        except Exception:
            pdf = generate(use_fallback=True)
            
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

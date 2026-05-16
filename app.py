import os
import re
import sys
import json
import threading
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from fpdf import FPDF
from markdown import markdown
import webview

# Initialize environment for PyInstaller
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
APP_VERSION = "2.0.0"
LICENSE_API_URL = "https://imsuraj.pythonanywhere.com"

DEFAULT_SETTINGS = {
    "output_folder": str(USER_DATA_DIR / "output_pdfs"),
    "prefix": "doc",
    "start_num": "1",
    "pdf_font": "Auto",
    "content": "",
    "titles": ""
}

class Api:
    def __init__(self, window):
        self.window = window
        self.is_generating = False
        self.is_activated = False
        self.settings = self.load_settings()

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except: pass
        return DEFAULT_SETTINGS

    def save_settings_internal(self, data):
        self.settings.update(data)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def select_folder(self):
        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        return None

    def deactivate(self):
        """Removes license and notifies backend to release the key."""
        if LICENSE_FILE.exists():
            try:
                # 1. Read the key to notify backend
                with open(LICENSE_FILE, "r") as f:
                    data = json.load(f)
                    old_key = data.get("key")
                
                # 2. Notify backend
                if old_key:
                    try:
                        import uuid
                        hwid = str(uuid.getnode())
                        req_data = json.dumps({"key": old_key, "hwid": hwid}).encode('utf-8')
                        req = urllib.request.Request(LICENSE_API_URL + "/deactivate", data=req_data, headers={'Content-Type': 'application/json'})
                        with urllib.request.urlopen(req, timeout=5) as r:
                            pass # Key released on backend
                    except: pass 

                # 3. Wipe local license
                LICENSE_FILE.unlink()
                self.is_activated = False
                self.window.evaluate_js("setActivation(false)")
                return True
            except: pass
        return False

    def verify_key(self, key):
        user_key = re.sub(r"[\s\-]+", "", key).upper()
        if not user_key: return False
        
        try:
            import uuid
            hwid = str(uuid.getnode())
            req_data = json.dumps({"key": user_key, "hwid": hwid}).encode('utf-8')
            req = urllib.request.Request(LICENSE_API_URL + "/verify", data=req_data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    with open(LICENSE_FILE, "w") as f:
                        json.dump({"date": datetime.now().isoformat(), "key": user_key}, f)
                    self.is_activated = True
                    return True
        except: pass
        return False

    def check_initial_license(self):
        if LICENSE_FILE.exists():
            try:
                with open(LICENSE_FILE, "r") as f:
                    data = json.load(f)
                    user_key = data.get("key", "")
                if self.verify_key(user_key):
                    self.window.evaluate_js("setActivation(true)")
                    return True
            except: pass
        self.window.evaluate_js("setActivation(false)")
        return False

    def run_batch(self, titles_raw, content_raw, config):
        if self.is_generating: return {"success": False, "error": "Already running"}
        self.is_generating = True
        
        self.save_settings_internal({
            "titles": titles_raw,
            "content": content_raw,
            **config
        })

        def worker():
            try:
                titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
                output_dir = Path(config['output_folder'])
                output_dir.mkdir(parents=True, exist_ok=True)
                prefix = config['prefix']
                start_n = int(config['start_num'])
                total = len(titles)

                for i, title in enumerate(titles):
                    file_num = start_n + i
                    filename = f"{prefix}{file_num:02d}.pdf"
                    filepath = output_dir / filename
                    self.build_pdf(filepath, title, content_raw)
                    self.window.evaluate_js(f"updateLog('Generated: {filename}', 'text-emerald-400')")
                
                self.is_generating = False
                self.window.evaluate_js("updateLog('BATCH COMPLETE: All files saved.', 'text-blue-400')")
            except Exception as e:
                self.is_generating = False
                self.window.evaluate_js(f"updateLog('CRITICAL ERROR: {str(e)}', 'text-rose-400')")

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True}

    def build_pdf(self, filepath, title, raw_markdown):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("helvetica", style="B", size=20)
        pdf.multi_cell(0, 12, title)
        pdf.set_draw_color(59, 142, 208)
        pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
        pdf.ln(10)
        html_content = markdown(re.sub(r"^#\s+.*", "", raw_markdown, count=1, flags=re.MULTILINE), extensions=['extra', 'sane_lists'])
        pdf.set_font("helvetica", size=12)
        try:
            from fpdf.fonts import FontFace
            tag_styles = {"h1": FontFace(emphasis="B", size_pt=20), "h2": FontFace(emphasis="B", size_pt=16), "p": FontFace(size_pt=12)}
            pdf.write_html(html_content, tag_styles=tag_styles)
        except:
            pdf.multi_cell(0, 8, html_content)
        pdf.output(str(filepath))

def start_app():
    initial_settings = DEFAULT_SETTINGS
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                initial_settings.update(json.load(f))
        except: pass
    html_file = get_resource_path('index.html')
    window = webview.create_window('AutoContent Pro | Ultimate Engine', html_file, width=1100, height=750, min_size=(900, 600), background_color='#09090b')
    api = Api(window)
    window.expose(api.verify_key, api.select_folder, api.run_batch, api.deactivate)
    def on_loaded():
        js_data = {"titles": initial_settings.get('titles', ''), "content": initial_settings.get('content', ''), "prefix": initial_settings.get('prefix', 'doc'), "start_num": initial_settings.get('start_num', '1'), "folder": initial_settings.get('output_folder', '')}
        js_code = f"""
            document.getElementById('titles-input').value = {json.dumps(js_data['titles'])};
            document.getElementById('content-input').value = {json.dumps(js_data['content'])};
            document.getElementById('prefix').value = {json.dumps(js_data['prefix'])};
            document.getElementById('start-num').value = {json.dumps(js_data['start_num'])};
            document.getElementById('output-folder').value = {json.dumps(js_data['folder'])};
            updateGutter('titles'); updateGutter('content');
            updateLog('System initialized. Ready for batch generation.');
        """
        window.evaluate_js(js_code)
        api.check_initial_license()
    window.events.loaded += on_loaded
    webview.start()

if __name__ == '__main__':
    start_app()

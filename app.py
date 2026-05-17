import os
import re
import sys
import json
import threading
import urllib.request
import webbrowser
import subprocess
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
APP_VERSION = "2.1.1"
LICENSE_API_URL = "https://imsuraj.pythonanywhere.com"

def check_and_apply_patches():
    """
    Checks the license/patch server for a new index.html update.
    If a new patch is available, it downloads and caches it in USER_DATA_DIR.
    Returns the path to the HTML file to load (either cached patch or bundled fallback).
    """
    cached_html = USER_DATA_DIR / "index.html"
    cached_hash_file = USER_DATA_DIR / "patch_hash.txt"
    version_tracking_file = USER_DATA_DIR / "engine_version.txt"
    bundled_html = get_resource_path("index.html")
    
    # 1. Version-Based Cache-Busting
    upgraded = False
    if version_tracking_file.exists():
        try:
            saved_version = version_tracking_file.read_text(encoding="utf-8").strip()
            if saved_version != APP_VERSION:
                upgraded = True
        except:
            upgraded = True
    else:
        upgraded = True
        
    if upgraded:
        try:
            if cached_html.exists(): cached_html.unlink()
            if cached_hash_file.exists(): cached_hash_file.unlink()
            version_tracking_file.write_text(APP_VERSION, encoding="utf-8")
        except: pass
        
    # By default, use bundled file if no cached patch exists
    html_to_load = str(bundled_html)
    if cached_html.exists():
        html_to_load = str(cached_html)
        
    try:
        # Query the patch server for the latest hash
        req = urllib.request.Request(
            f"{LICENSE_API_URL}/api/v1/patch/hash", 
            headers={"User-Agent": "AutoContentPro-Client"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            remote_hash = res_data.get("hash")
            
        if not remote_hash:
            return html_to_load
            
        # Get the local cached hash
        local_hash = ""
        if cached_hash_file.exists():
            try:
                local_hash = cached_hash_file.read_text(encoding="utf-8").strip()
            except:
                pass
                
        # If the hashes differ, or we don't have a cached HTML file, download the patch!
        if remote_hash != local_hash or not cached_html.exists():
            download_req = urllib.request.Request(
                f"{LICENSE_API_URL}/api/v1/patch/download",
                headers={"User-Agent": "AutoContentPro-Client"}
            )
            with urllib.request.urlopen(download_req, timeout=10) as download_response:
                patch_content = download_response.read()
                
            # Perform a quick validation: check if it starts with <!DOCTYPE html
            # to make sure we didn't download an error page or garbage
            content_str = patch_content.decode('utf-8', errors='ignore').strip()
            if "<!DOCTYPE html" in content_str or "<html" in content_str:
                # Write to AppData
                cached_html.write_bytes(patch_content)
                cached_hash_file.write_text(remote_hash, encoding="utf-8")
                html_to_load = str(cached_html)
                print(f"[Stealth Patch] Successfully downloaded and applied new frontend patch (hash: {remote_hash})")
            else:
                print("[Stealth Patch] Invalid patch content received. Skipping patch.")
    except Exception as e:
        print(f"[Stealth Patch] Update check failed or offline: {str(e)}")
        # Offline or server issue, we fall back to whatever we have (cached or bundled)
        
    return html_to_load

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
        self.update_url = None
        self.remote_version = None

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
        # 1. Fallback self-healing migration from Installer folder ({app}/license.key)
        installer_license = EXE_DIR / "license.key"
        if installer_license.exists():
            try:
                with open(installer_license, "r") as f:
                    inst_data = json.load(f)
                    user_key = inst_data.get("key", "")
                if user_key:
                    # Copy the key over to the current standard user's AppData
                    with open(LICENSE_FILE, "w") as f:
                        json.dump({"date": datetime.now().isoformat(), "key": user_key}, f)
                    # Try to clean up/delete the file from the installation folder
                    try:
                        installer_license.unlink()
                    except:
                        pass # Non-admin launch might make this read-only; that is fine
            except Exception as e:
                print(f"[License Migration] Error migrating installer key: {str(e)}")

        # 2. Standard Activation Check
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
    if getattr(sys, 'frozen', False):
        html_file = check_and_apply_patches()
    else:
        # In local development mode, always load the workspace index.html directly!
        html_file = get_resource_path("index.html")
    window = webview.create_window('AutoContent Pro | Ultimate Engine', html_file, width=1100, height=750, min_size=(900, 600), background_color='#09090b')
    api = Api(window)
    window.expose(api.verify_key, api.select_folder, api.run_batch, api.deactivate)
    def on_loaded():
        # Get the patch status to show in console and version tag
        cached_hash_file = USER_DATA_DIR / "patch_hash.txt"
        patch_info = "Engine: Active"
        patch_tag = ""
        if cached_hash_file.exists():
            try:
                local_hash = cached_hash_file.read_text(encoding="utf-8").strip()[:8]
                patch_info = f"Engine: Active (Patch {local_hash})"
                patch_tag = f" ({local_hash})"
            except:
                pass
                
        js_data = {"titles": initial_settings.get('titles', ''), "content": initial_settings.get('content', ''), "prefix": initial_settings.get('prefix', 'doc'), "start_num": initial_settings.get('start_num', '1'), "folder": initial_settings.get('output_folder', '')}
        js_code = f"""
            document.getElementById('titles-input').value = {json.dumps(js_data['titles'])};
            document.getElementById('content-input').value = {json.dumps(js_data['content'])};
            document.getElementById('prefix').value = {json.dumps(js_data['prefix'])};
            document.getElementById('start-num').value = {json.dumps(js_data['start_num'])};
            document.getElementById('output-folder').value = {json.dumps(js_data['folder'])};
            if(typeof setSystemInfo === 'function') {{
                setSystemInfo('{APP_VERSION}', '{patch_tag}');
            }}
            updateGutter('titles'); updateGutter('content');
            updateLog('System initialized. {patch_info} operational.', 'text-zinc-400');
        """
        window.evaluate_js(js_code)
        api.check_initial_license()
    window.events.loaded += on_loaded
    webview.start()

if __name__ == '__main__':
    start_app()

import os
import re
import sys
import json
import threading
import urllib.request
import webbrowser
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from fpdf import FPDF
from markdown import markdown
import webview
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# ==========================================
# APPWRITE CONFIGURATION
# ==========================================
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://sgp.cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "6a09e8a5002e960936ec")
APPWRITE_FUNCTION_ID = os.getenv("APPWRITE_FUNCTION_ID", "verify-license")

APP_VERSION = "2.1.1"

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

def check_and_apply_patches():
    """
    Queries Appwrite Storage to check for a frontend stealth patch (index.html).
    If the remote MD5 signature differs from the local cache, it downloads it silently.
    Returns the path to the HTML file to load (either cached patch or bundled fallback).
    """
    print("[OTA Engine] Initializing Stealth Patching Engine...")
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
                print(f"[OTA Engine] App version upgrade detected (from {saved_version} to {APP_VERSION}). Evicting old cache.")
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
        
    html_to_load = str(bundled_html)
    if cached_html.exists():
        print(f"[OTA Engine] Found locally cached patch at: {cached_html}")
        html_to_load = str(cached_html)
    else:
        print(f"[OTA Engine] No local patch cache found. Using bundled HTML fallback.")
        
    try:
        # Query Appwrite Storage bucket metadata (using the "patches" bucket and "frontend_patch" file ID)
        print(f"[OTA Engine] Connecting to Appwrite Storage to check for on-air patches...")
        url = f"{APPWRITE_ENDPOINT}/storage/buckets/patches/files/frontend_patch"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "AutoContentPro-Client", "X-Appwrite-Project": APPWRITE_PROJECT_ID}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            remote_hash = res_data.get("signature") # Appwrite returns MD5 in signature
            print(f"[OTA Engine] Remote signature retrieved successfully: {remote_hash}")
            
        if not remote_hash:
            print("[OTA Engine] Remote signature is empty. Bypassing patch download.")
            return html_to_load
            
        local_hash = ""
        if cached_hash_file.exists():
            try: 
                local_hash = cached_hash_file.read_text(encoding="utf-8").strip()
                print(f"[OTA Engine] Local cached patch signature: {local_hash}")
            except: pass
                
        if remote_hash != local_hash or not cached_html.exists():
            print("[OTA Engine] Update detected! Starting silent background download...")
            d_url = f"{APPWRITE_ENDPOINT}/storage/buckets/patches/files/frontend_patch/download"
            d_req = urllib.request.Request(
                d_url,
                headers={"User-Agent": "AutoContentPro-Client", "X-Appwrite-Project": APPWRITE_PROJECT_ID}
            )
            with urllib.request.urlopen(d_req, timeout=10) as d_response:
                patch_content = d_response.read()
                
            content_str = patch_content.decode('utf-8', errors='ignore').strip()
            if "<!DOCTYPE html" in content_str or "<html" in content_str:
                cached_html.write_bytes(patch_content)
                cached_hash_file.write_text(remote_hash, encoding="utf-8")
                html_to_load = str(cached_html)
                print(f"[OTA Engine] Success! Applied new Appwrite frontend patch (hash: {remote_hash})")
            else:
                print("[OTA Engine] Error: Invalid patch content received.")
        else:
            print("[OTA Engine] Application is fully up to date! Loading cached interface.")
    except Exception as e:
        print(f"[OTA Engine] Storage check skipped or offline: {str(e)}")
        
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
        if result: return result[0]
        return None

    def call_appwrite_function(self, action, key, hwid):
        """Helper to invoke the Appwrite Serverless Function synchronously"""
        payload = json.dumps({"action": action, "key": key, "hwid": hwid})
        # Appwrite requires "async": False to return the execution response immediately
        req_body = json.dumps({"async": False, "body": payload}).encode('utf-8')
        
        url = f"{APPWRITE_ENDPOINT}/functions/{APPWRITE_FUNCTION_ID}/executions"
        req = urllib.request.Request(
            url, 
            data=req_body, 
            headers={
                "Content-Type": "application/json", 
                "X-Appwrite-Project": APPWRITE_PROJECT_ID,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoContent/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            res = json.loads(r.read().decode('utf-8'))
            if res.get("status") == "failed":
                return {"status": "error", "message": "Serverless execution failed"}, 500
            
            status_code = res.get("responseStatusCode", 500)
            body_str = res.get("responseBody", "{}")
            try:
                return json.loads(body_str), status_code
            except:
                return {"status": "error", "message": "Invalid Appwrite response format"}, 500

    def deactivate(self):
        if LICENSE_FILE.exists():
            try:
                with open(LICENSE_FILE, "r") as f:
                    old_key = json.load(f).get("key")
                if old_key:
                    hwid = str(uuid.getnode())
                    try:
                        self.call_appwrite_function("deactivate", old_key, hwid)
                    except: pass 
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
            hwid = str(uuid.getnode())
            print(f"\n[DEBUG] Calling Appwrite function...")
            print(f"[DEBUG] Endpoint  : {APPWRITE_ENDPOINT}")
            print(f"[DEBUG] Project ID: {APPWRITE_PROJECT_ID}")
            print(f"[DEBUG] Function  : {APPWRITE_FUNCTION_ID}")
            print(f"[DEBUG] Key sent  : {user_key}")
            print(f"[DEBUG] HWID      : {hwid}")
            res, status_code = self.call_appwrite_function("verify", user_key, hwid)
            print(f"[DEBUG] Status code: {status_code}")
            print(f"[DEBUG] Response   : {res}")
            
            if status_code == 200 and res.get("status") == "success":
                user_name = res.get("user", "Active User")
                org_name = res.get("organization", "")
                with open(LICENSE_FILE, "w") as f:
                    json.dump({
                        "date": datetime.now().isoformat(), 
                        "key": user_key, 
                        "user": user_name,
                        "org": org_name,
                        "last_online_sync": datetime.now().isoformat()
                    }, f)
                self.is_activated = True
                self.window.evaluate_js("setActivation(true)")
                self.window.evaluate_js(f"setLicenseInfo({json.dumps(user_key)}, {json.dumps(user_name)}, {json.dumps(org_name)}, {json.dumps(hwid)}, true)")
                self.window.evaluate_js("updateLog('Activation successful! Security gate released.', 'text-emerald-400')")
                return True
            else:
                msg = res.get("message", "Activation failed")
                print(f"[DEBUG] Activation failed - message: {msg}")
                self.window.evaluate_js(f"updateLog('Activation Error: {msg}', 'text-rose-400')")
        except Exception as e:
            print(f"[DEBUG] EXCEPTION: {str(e)}")
            self.window.evaluate_js(f"updateLog('Activation Sync Error: Offline or server unreachable.', 'text-rose-400')")
        return False

    def check_initial_license(self):
        hwid = str(uuid.getnode())
        
        # 1. Fallback self-healing migration from Installer
        installer_license = EXE_DIR / "license.key"
        if installer_license.exists():
            try:
                with open(installer_license, "r") as f:
                    user_key = json.load(f).get("key", "")
                if user_key:
                    with open(LICENSE_FILE, "w") as f:
                        json.dump({
                            "date": datetime.now().isoformat(), 
                            "key": user_key,
                            "last_online_sync": "2000-01-01T00:00:00" # Force a network sync immediately
                        }, f)
                    try: installer_license.unlink()
                    except: pass
            except: pass

        # 2. Advanced Offline Sync Validation Model
        if LICENSE_FILE.exists():
            try:
                with open(LICENSE_FILE, "r") as f:
                    data = json.load(f)
                    user_key = data.get("key", "")
                    user_name = data.get("user", "Active User")
                    last_sync_str = data.get("last_online_sync")
                
                # Check if we can bypass network using the 24-hour cache
                needs_sync = True
                if last_sync_str:
                    try:
                        last_sync = datetime.fromisoformat(last_sync_str)
                        if (datetime.now() - last_sync).total_seconds() < (24 * 3600):
                            needs_sync = False
                    except: pass
                
                if not needs_sync:
                    # Super-fast offline launch
                    self.is_activated = True
                    self.window.evaluate_js("setActivation(true)")
                    self.window.evaluate_js(f"setLicenseInfo({json.dumps(user_key)}, {json.dumps(user_name)}, {json.dumps(data.get('org',''))}, {json.dumps(hwid)}, true)")
                    self.window.evaluate_js("showPage('titles')") 
                    return True
                
                # Perform Online Sync (cache expired)
                try:
                    res, status_code = self.call_appwrite_function("verify", user_key, hwid)
                    if status_code == 200 and res.get("status") == "success":
                        user_name = res.get("user", "Active User")
                        org_name = res.get("organization", "")
                        data["user"] = user_name
                        data["org"] = org_name
                        data["last_online_sync"] = datetime.now().isoformat()
                        with open(LICENSE_FILE, "w") as f: json.dump(data, f)
                        self.is_activated = True
                        self.window.evaluate_js("setActivation(true)")
                        self.window.evaluate_js(f"setLicenseInfo({json.dumps(user_key)}, {json.dumps(user_name)}, {json.dumps(org_name)}, {json.dumps(hwid)}, true)")
                        self.window.evaluate_js("showPage('titles')")
                        return True
                    elif status_code in [403, 404]:
                        # License definitively revoked or deleted from Appwrite
                        msg = res.get("message", "Unknown error")
                        self.window.evaluate_js(f"updateLog('License Revoked: {msg}', 'text-rose-400')")
                        try: LICENSE_FILE.unlink()
                        except: pass
                except Exception as e:
                    # Network offline or Appwrite unreachable - fallback to Grace Period
                    if last_sync_str:
                        try:
                            last_sync = datetime.fromisoformat(last_sync_str)
                            if (datetime.now() - last_sync).total_seconds() < (7 * 24 * 3600): # 7 Days Grace
                                self.is_activated = True
                                self.window.evaluate_js("setActivation(true)")
                                self.window.evaluate_js(f"setLicenseInfo({json.dumps(user_key)}, {json.dumps(user_name)}, {json.dumps(data.get('org',''))}, {json.dumps(hwid)}, true)")
                                self.window.evaluate_js("showPage('titles')")
                                self.window.evaluate_js("updateLog('Network offline. Operating in Grace Period Mode (7 Days max).', 'text-amber-400')")
                                return True
                        except: pass
                    self.window.evaluate_js("updateLog('Network offline. Grace period expired. Please connect to internet to verify license.', 'text-rose-400')")
            except: pass
            
        self.is_activated = False
        self.window.evaluate_js(f"setLicenseInfo('', '', '', {json.dumps(hwid)}, false)")
        self.window.evaluate_js("setActivation(false)")
        return False

    def run_batch(self, titles_raw, content_raw, config):
        if not self.is_activated:
            return {"success": False, "error": "License not activated"}
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
    print("[Boot Log] Starting AutoContent Pro Application...")
    initial_settings = DEFAULT_SETTINGS
    if SETTINGS_FILE.exists():
        try:
            print(f"[Boot Log] Loading initial settings from: {SETTINGS_FILE}")
            with open(SETTINGS_FILE, "r") as f:
                initial_settings.update(json.load(f))
        except Exception as e:
            print(f"[Boot Log] Failed to load settings: {e}")
        
    if getattr(sys, 'frozen', False):
        print("[Boot Log] Running inside compiled executable binary. Starting OTA Engine checks...")
        html_file = check_and_apply_patches()
    else:
        print("[Boot Log] Running in development mode. Bypassing OTA checks and loading local index.html directly...")
        html_file = get_resource_path("index.html")
        
    print(f"[Boot Log] Initializing GUI window with HTML interface: {html_file}")
    window = webview.create_window('AutoContent Pro | Ultimate Engine', html_file, width=1100, height=750, min_size=(900, 600), background_color='#09090b')
    api = Api(window)
    window.expose(api.verify_key, api.select_folder, api.run_batch, api.deactivate)
    print("[Boot Log] Exposed all secure API bridges to GUI.")
    
    def on_loaded():
        cached_hash_file = USER_DATA_DIR / "patch_hash.txt"
        patch_info = "Engine: Active"
        patch_tag = ""
        if cached_hash_file.exists():
            try:
                local_hash = cached_hash_file.read_text(encoding="utf-8").strip()[:8]
                patch_info = f"Engine: Active (Patch {local_hash})"
                patch_tag = f" ({local_hash})"
            except: pass
                
        js_data = {
            "titles": initial_settings.get('titles', ''), 
            "content": initial_settings.get('content', ''), 
            "prefix": initial_settings.get('prefix', 'doc'), 
            "start_num": initial_settings.get('start_num', '1'), 
            "folder": initial_settings.get('output_folder', '')
        }
        
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
            if(typeof syncHistories === 'function') {{
                syncHistories();
            }}
            updateLog('System initialized. {patch_info} operational.', 'text-zinc-400');
        """
        window.evaluate_js(js_code)
        api.check_initial_license()
        
    window.events.loaded += on_loaded
    webview.start()

if __name__ == '__main__':
    start_app()

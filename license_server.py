import os
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app)

# CONFIGURATION
# Default password is 'anytime2027'. Hash is below:
ADMIN_PASSWORD_HASH = "89249c5c307f1ec72dc7ee389fd9d2acbccd37ca8666a91bc4201525f734cfff"
DB_PATH = os.path.join(os.path.dirname(__file__), 'licenses.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licenses
                 (key TEXT PRIMARY KEY, 
                  user_name TEXT, 
                  status TEXT, 
                  created_at TEXT, 
                  duration_days INTEGER,
                  hwid TEXT)''')
    # If the database already existed without hwid, let's add it dynamically
    try:
        c.execute("ALTER TABLE licenses ADD COLUMN hwid TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

# SECURITY DECORATOR
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Hash the incoming key and compare
        hashed_input = hashlib.sha256(admin_key.encode()).hexdigest()
        if hashed_input != ADMIN_PASSWORD_HASH:
            return jsonify({"error": "Invalid Admin Key"}), 403
        
        return f(*args, **kwargs)
    return decorated

@app.route('/verify/<key>', methods=['GET'])
def verify_license(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_name, status, created_at, duration_days FROM licenses WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()

    if row:
        user_name, status, created_at, duration_days = row
        if status != 'Active':
            return jsonify({"status": "Revoked", "message": "License has been revoked"}), 403
            
        # Check expiry
        created_dt = datetime.fromisoformat(created_at)
        days_passed = (datetime.now() - created_dt).days
        if days_passed > duration_days:
            return jsonify({"status": "Expired", "message": "License has expired"}), 403
            
        return jsonify({"status": "Active", "user": user_name}), 200
    
    return jsonify({"status": "Invalid", "message": "License key not found"}), 404

# ADMIN ENDPOINTS (PROTECTED)
@app.route('/admin/list', methods=['GET'])
@require_admin
def list_licenses():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, user_name, status, created_at, duration_days FROM licenses")
    rows = c.fetchall()
    conn.close()
    
    licenses = []
    for row in rows:
        licenses.append({
            "key": row[0],
            "user_name": row[1],
            "status": row[2],
            "created_at": row[3],
            "duration_days": row[4]
        })
    return jsonify({"licenses": licenses})

@app.route('/admin/add_key/<key>', methods=['GET'])
@require_admin
def add_license(key):
    user_name = request.args.get('name', 'Unknown User')
    duration = int(request.args.get('duration', 365))
    created_at = datetime.now().isoformat()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO licenses VALUES (?, ?, 'Active', ?, ?)", 
                 (key, user_name, created_at, duration))
        conn.commit()
        conn.close()
        return jsonify({"message": "License added successfully"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Key already exists"}), 400

@app.route('/admin/revoke/<key>', methods=['GET'])
@require_admin
def revoke_license(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE licenses SET status='Revoked' WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"message": "License revoked"}), 200

@app.route('/admin/activate/<key>', methods=['GET'])
@require_admin
def activate_license(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE licenses SET status='Active' WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"message": "License activated"}), 200

@app.route('/admin/delete/<key>', methods=['GET'])
@require_admin
def delete_license(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM licenses WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"message": "License deleted"}), 200

# NEW: COMPATIBLE POST VERIFY ROUTE WITH HWID LOCKING
@app.route('/verify', methods=['POST'])
def verify_license_post():
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    hwid = data.get("hwid")
    
    if not key:
        return jsonify({"status": "error", "message": "Key is required"}), 400
        
    # Standardize key formatting (remove spaces/dashes, uppercase)
    import re
    user_key = re.sub(r"[\s\-]+", "", key).upper()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_name, status, created_at, duration_days, hwid FROM licenses WHERE key=?", (user_key,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "License key not found"}), 404
        
    user_name, status, created_at, duration_days, stored_hwid = row
    
    # 1. Check status
    if status != 'Active':
        conn.close()
        return jsonify({"status": "error", "message": "License has been revoked"}), 403
        
    # 2. Check expiry
    created_dt = datetime.fromisoformat(created_at)
    days_passed = (datetime.now() - created_dt).days
    if days_passed > duration_days:
        conn.close()
        return jsonify({"status": "error", "message": "License has expired"}), 403
        
    # 3. Check / Bind Hardware ID (HWID)
    if not stored_hwid:
        # First activation: Bind the HWID!
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, user_key))
        conn.commit()
        stored_hwid = hwid
        
    if hwid and stored_hwid != hwid:
        conn.close()
        return jsonify({"status": "error", "message": "License key already active on another machine"}), 403
        
    conn.close()
    return jsonify({"status": "success", "user": user_name}), 200

# NEW: COMPATIBLE POST DEACTIVATE ROUTE TO RELEASE HWID LOCK
@app.route('/deactivate', methods=['POST'])
def deactivate_license_post():
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    hwid = data.get("hwid")
    
    if not key:
        return jsonify({"status": "error", "message": "Key is required"}), 400
        
    import re
    user_key = re.sub(r"[\s\-]+", "", key).upper()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hwid FROM licenses WHERE key=?", (user_key,))
    row = c.fetchone()
    
    if row:
        stored_hwid = row[0]
        if stored_hwid == hwid:
            # Unbind hardware ID so the user can activate on a new machine
            c.execute("UPDATE licenses SET hwid=NULL WHERE key=?", (user_key,))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "License deactivated successfully"}), 200
            
    conn.close()
    return jsonify({"status": "error", "message": "Invalid deactivation request"}), 400

# NEW: STEALTH PATCH ROUTE - RETRIEVE LATEST PATCH HASH
@app.route('/api/v1/patch/hash', methods=['GET'])
def get_patch_hash():
    index_path = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return jsonify({"hash": file_hash}), 200
    return jsonify({"error": "Template not found"}), 404

# NEW: STEALTH PATCH ROUTE - DOWNLOAD LATEST INDEX.HTML
@app.route('/api/v1/patch/download', methods=['GET'])
def download_patch():
    index_path = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path), 200
    return jsonify({"error": "Template not found"}), 404

# NEW: ENGINE UPDATE ROUTE - CHECK LATEST BINARY VERSION & LINK
@app.route('/api/v1/update/check', methods=['GET'])
def check_update():
    # You can update this version to trigger major native updates for users
    return jsonify({
        "version": "2.1.0",
        "url": "https://imsuraj.pythonanywhere.com/api/v1/dist/autocontent_pro.exe"
    }), 200

# NEW: ENGINE UPDATE ROUTE - SERVE THE NATIVE COMPILED EXE
@app.route('/api/v1/dist/autocontent_pro.exe', methods=['GET'])
def download_exe():
    dist_path = os.path.join(os.path.dirname(__file__), 'autocontent_pro.exe')
    if os.path.exists(dist_path):
        return send_file(dist_path), 200
    return jsonify({"error": "Distribution file not found"}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
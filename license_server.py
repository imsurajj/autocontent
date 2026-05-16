from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_FILE = '/home/imsuraj/mysite/licenses.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            hwid TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/verify', methods=['POST'])
def verify_license():
    data = request.get_json()
    if not data or 'key' not in data or 'hwid' not in data:
        return jsonify({"status": "error", "message": "Missing key or hwid"}), 400
        
    key = data['key'].upper().strip()
    hwid = data['hwid'].strip()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status, hwid FROM licenses WHERE key = ?", (key,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid license key."}), 401
        
    status, db_hwid = row
    
    if status != 'Active':
        conn.close()
        return jsonify({"status": "error", "message": f"License is {status}."}), 403
        
    if not db_hwid:
        # First time activation for this key
        c.execute("UPDATE licenses SET hwid = ? WHERE key = ?", (hwid, key))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "License activated successfully!"}), 200
        
    if db_hwid != hwid:
        # Key is already bound to another hardware ID
        conn.close()
        return jsonify({"status": "error", "message": "License already in use on another computer."}), 403
        
    # HWID matches and status is active
    conn.close()
    return jsonify({"status": "success", "message": "License verified."}), 200

# Simple endpoint to add keys (You should secure this or just do it via SQLite shell)
@app.route('/admin/add_key/<key>', methods=['GET'])
def add_key(key):
    # WARNING: This endpoint is public for demonstration. 
    # Do not leave this unprotected in production!
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO licenses (key, status) VALUES (?, ?)", (key.upper(), 'Active'))
        conn.commit()
        msg = "Key added successfully"
    except sqlite3.IntegrityError:
        msg = "Key already exists"
    conn.close()
    return jsonify({"message": msg})

# Initialize DB on startup (works both locally and under WSGI)
init_db()

if __name__ == '__main__':
    app.run(debug=True)

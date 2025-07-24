from flask import Flask, request, jsonify, abort
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'licenses.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            license_key TEXT PRIMARY KEY,
            hardware_id TEXT,
            user TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def get_license(license_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT license_key, hardware_id, user, active FROM licenses WHERE license_key = ?", (license_key,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_license(license_key, hardware_id, user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE licenses SET hardware_id = ?, user = ? WHERE license_key = ?", (hardware_id, user, license_key))
    conn.commit()
    conn.close()
    
@app.route('/upload-db', methods=['POST'])
def upload_db():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    file.save(DB_FILE)  # Save it as 'licenses.db'
    return 'Uploaded', 200

@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.get_json()
    license_key = data.get("license_key")
    hardware_id = data.get("hardware_id")
    user = data.get("user") or "Unknown"

    if not license_key or not hardware_id:
        return jsonify({"status": "error", "message": "Missing license key or hardware ID"}), 400

    license = get_license(license_key)

    if not license:
        return jsonify({"status": "invalid", "message": "Key does not exist"}), 400

    db_license_key, db_hardware_id, db_user, db_active = license

    if db_active == 0:
        return jsonify({"status": "inactive", "message": "Key is deactivated"}), 403

    if db_hardware_id is None:
        update_license(license_key, hardware_id, user)
        return jsonify({"status": "valid", "user": user})

    elif db_hardware_id == hardware_id:
        return jsonify({"status": "valid", "user": db_user})

    else:
        return jsonify({"status": "invalid", "message": "Key already used on another machine"}), 403

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
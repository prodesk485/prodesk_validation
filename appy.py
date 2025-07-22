from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = 'licenses.json'

def load_licenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_licenses(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.get_json()
    license_key = data.get("license_key")
    hardware_id = data.get("hardware_id")
    user = data.get("user")  # username passed from the GUI

    if not license_key or not hardware_id:
        return jsonify({"status": "error", "message": "Missing license key or hardware ID"}), 400

    licenses = load_licenses()

    if license_key not in licenses:
        return jsonify({"status": "invalid", "message": "Key does not exist"}), 400

    license = licenses[license_key]

    if not license.get("active", True):
        return jsonify({"status": "inactive", "message": "Key is deactivated"}), 403

    # First-time activation
    if license.get("hardware_id") is None:
        license["hardware_id"] = hardware_id
        license["user"] = user or "Unknown"  # Save the user if provided
        licenses[license_key] = license
        save_licenses(licenses)
        return jsonify({"status": "valid", "user": license["user"]})

    # Already activated on this machine
    elif license["hardware_id"] == hardware_id:
        return jsonify({"status": "valid", "user": license["user"]})

    # Used on a different machine
    else:
        return jsonify({"status": "invalid", "message": "Key already used on another machine"}), 403

if __name__ == '__main__':
    app.run(debug=True)
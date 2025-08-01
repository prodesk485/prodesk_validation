from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import psycopg2
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session
load_dotenv()
# PostgreSQL connection
POSTGRES_URI = os.getenv("POSTGRES_URI")
print("POSTGRES_URI:",POSTGRES_URI)
conn = psycopg2.connect(POSTGRES_URI)
cursor = conn.cursor()

# Admin credentials (change thse)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hanzala1H@09"

# HTML templates (you can separate into real HTML files later)
LOGIN_TEMPLATE = '''
<!doctype html>
<title>Admin Login</title>
<h2>Login</h2>
<form method="POST">
  <input type="text" name="username" placeholder="Username"><br>
  <input type="password" name="password" placeholder="Password"><br>
  <input type="submit" value="Login">
</form>
'''

DASHBOARD_TEMPLATE = '''
<!doctype html>
<title>Dashboard</title>
<h2>License Dashboard</h2>
<table border="1">
  <tr><th>Key</th><th>Hardware ID</th><th>User</th><th>Status</th></tr>
  {% for row in rows %}
  <tr>
    <td>{{ row[0] }}</td>
    <td>{{ row[1] }}</td>
    <td>{{ row[2] }}</td>
    <td>{{ 'Active' if row[3] else 'Inactive' }}</td>
  </tr>
  {% endfor %}
</table>
<a href="{{ url_for('logout') }}">Logout</a>
'''

def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS _licenses (
            license_key TEXT PRIMARY KEY,
            hardware_id TEXT,
            user TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()

@app.route('/validate', methods=['POST'])
def validate():
    data = request.get_json()
    key = data.get("license_key")
    hwid = data.get("hardware_id")
    user_name = data.get("user_name", "Unknown")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing license key or hardware ID"}), 400
    try:
        cursor.execute("SELECT license_key, hardware_id, user_name, active FROM _licenses WHERE license_key = %s", (key,))
        row = cursor.fetchone()
        print (row)
    except psycopg2.Error as e:
        print("DataBase error:", e)
        conn.rollback()
    if not row:
        return jsonify({"status": "invalid", "message": "Key not found"}), 404

    db_key, db_hwid, db_user, db_active = row

    if db_active == 0:
        return jsonify({"status": "inactive", "message": "Key is deactivated"}), 403

    if db_hwid is None:
        cursor.execute("UPDATE _licenses SET hardware_id = %s, user_name = %s WHERE license_key = %s", (hwid, user_name, key))
        conn.commit()
        return jsonify({"status": "valid", "user": user_name})

    if db_hwid == hwid:
        return jsonify({"status": "valid", "user": db_user})

    return jsonify({"status": "invalid", "message": "Key is used on another device"}), 403

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))
    cursor.execute("SELECT * FROM _licenses")
    rows = cursor.fetchall()
    return render_template_string(DASHBOARD_TEMPLATE, rows=rows)

@app.route('/logout')
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port)
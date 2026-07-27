import os
import sqlite3
import bleach
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

# ====================== Gemini Setup ======================
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai is not installed.")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey-change-in-production")

if GEMINI_AVAILABLE:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("⚠️ GEMINI_API_KEY environment variable is missing.")

DB_NAME = "zeus_agent.db"


def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("SELECT * FROM users WHERE email = 'admin@zeus.com'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash("adminpassword")
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", 
                         ("admin@zeus.com", hashed_pw))
        conn.commit()
    except Exception as e:
        print(f"Database init error: {e}")
    finally:
        if conn:
            conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if row and check_password_hash(row[0], password):
                session['logged_in'] = True
                session['email'] = email
                return redirect(url_for('index'))
            else:
                error = 'Invalid Email or Password'
        except Exception:
            error = 'System error during login'
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    return render_template_string(HTML_LOGIN, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template_string(HTML_DASHBOARD)


@app.route('/api/ask', methods=['POST'])
@login_required
def api_ask():
    if not GEMINI_AVAILABLE:
        return jsonify({"response": "AI service is not available (library not installed)."})

    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"response": "Gemini API key is not configured."})

    data = request.get_json(silent=True) or {}
    prompt = bleach.clean(data.get('prompt', '').strip())

    if not prompt:
        return jsonify({"response": "Please provide a valid prompt."})

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        reply = response.text if response and hasattr(response, 'text') else "Empty response from Zeus."
        
    except Exception as e:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            reply = response.text if response and hasattr(response, 'text') else "Empty response from Zeus."
        except Exception as inner_e:
            reply = f"System notice: Unable to connect to Zeus. {str(inner_e)[:120]}"

    return jsonify({"response": reply})


# ====================== HTML TEMPLATES ======================
HTML_LOGIN = """ ... (your login HTML - unchanged) ... """

HTML_DASHBOARD = """ ... (your dashboard HTML - unchanged) ... """


if __name__ == '__main__':
    print("🚀 Zeus AI Agent is starting on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

import os
import sqlite3
import datetime
import jwt
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
DB_NAME = "zeus_agent.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("adminpassword")
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_pw))
    conn.commit()
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
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Invalid Credentials'
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
    data = request.get_json()
    prompt = bleach.clean(data.get('prompt', ''))
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"You are Zeus, ancient ruler of Olympus, god of thunder, sky, and cosmic law. Answer this query in your majestic, powerful, and wise character: {prompt}"
        )
        reply = response.text
    except Exception as e:
        reply = f"The mists of Olympus obscure my vision at the moment. (Error: {str(e)})"
    return jsonify({"response": reply})

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Zeus Login</title></head>
<body style="background:url('https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1920&auto=format&fit=crop') no-repeat center center fixed; background-size:cover; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
    <div style="background:rgba(18, 18, 18, 0.9); padding:25px; border-radius:10px; width:280px; box-shadow: 0 4px 15px rgba(0,0,0,0.8); border: 1px solid #444;">
        <h2 style="color:#fff; text-align:center; margin-top:0;">Zeus Agent Login</h2>
        {% if error %}<p style="color:#ff6b6b; text-align:center; font-size:14px;">{{error}}</p>{% endif %}
        <form method="POST">
            <label style="color:#ccc; font-size:14px;">Username:</label><br>
            <input type="text" name="username" style="width:100%; padding:8px; margin:5px 0 15px 0; background:#222; color:#fff; border:1px solid #444; border-radius:4px; box-sizing:border-box;"><br>
            <label style="color:#ccc; font-size:14px;">Password:</label><br>
            <input type="password" name="password" style="width:100%; padding:8px; margin:5px 0 20px 0; background:#222; color:#fff; border:1px solid #444; border-radius:4px; box-sizing:border-box;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#007bff; color:#fff; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">Login</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head><title>Zeus AI Agent Dashboard</title></head>
<body style="background:url('https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1920&auto=format&fit=crop') no-repeat center center fixed; background-size:cover; color:#fff; font-family:sans-serif; margin:0; height:100vh; display:flex; flex-direction:column; justify-content:flex-end; padding-bottom:30px;">
    <div style="max-width: 600px; width:90%; margin: auto; background:rgba(15, 15, 15, 0.85); padding:20px; border-radius:12px; border:1px solid #444; box-shadow: 0 8px 32px rgba(0,0,0,0.9);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h2 style="margin:0; font-size:18px; color:#ffda79;">Zeus AI Agent Dashboard</h2>
            <a href="/logout" style="color: #ff6b6b; text-decoration: none; font-weight: bold; font-size:14px;">Logout</a>
        </div>
        <div id="chat-box" style="background:rgba(10, 10, 10, 0.95); padding:15px; height:300px; overflow-y:scroll; border:1px solid #333; border-radius:8px; margin-bottom:15px; box-shadow: inset 0 0 10px rgba(0,0,0,0.8);"></div>
        <div style="display:flex; gap:10px;">
            <input type="text" id="prompt-input" placeholder="Ask Zeus a story or history..." style="flex:1; padding:12px; background:rgba(30,30,30,0.9); color:#fff; border:1px solid #444; border-radius:4px; outline:none;">
            <button onclick="askZeus()" style="padding:12px 20px; background:#28a745; color:#fff; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">Send</button>
        </div>
    </div>

    <script>
    async function askZeus() {
        let prompt = document.getElementById('prompt-input').value;
        if (!prompt) return;
        let chatBox = document.getElementById('chat-box');
        chatBox.innerHTML += `<div style="margin-bottom:10px; color:#e0e0e0;"><b>You:</b> ${prompt}</div>`;
        document.getElementById('prompt-input').value = '';
        
        let res = await fetch('/api/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt: prompt})
        });
        let data = await res.json();
        chatBox.innerHTML += `<div style="margin-bottom:10px; color:#ffda79;"><b>Zeus:</b> ${data.response}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    

import os
import sqlite3
import bleach
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT * FROM users WHERE email = 'admin@zeus.com'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("adminpassword")
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("admin@zeus.com", hashed_pw))
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
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Invalid Email or Password'
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
    data = request.get_json() or {}
    prompt = bleach.clean(data.get('prompt', ''))
    if not prompt:
        return jsonify({"response": "Please provide a valid prompt."})
    
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        reply = response.text if response and response.text else "The oracle returned an empty response."
    except Exception as e:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents=prompt
            )
            reply = response.text if response and response.text else "The oracle returned an empty response."
        except Exception as inner_e:
            reply = f"System notice: Unable to fetch response at this moment."
            
    return jsonify({"response": reply})

    
    

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
</head>
<body style="background: #0f172a url('https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1920&auto=format&fit=crop') no-repeat center center fixed; background-size: cover; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px); padding: 30px; border-radius: 12px; width: 320px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.1);">
        <h2 style="color: #fff; text-align: center; margin-top: 0; font-weight: 500;">Welcome Back</h2>
        <p style="color: #64748b; text-align: center; font-size: 12px; margin-top: -5px; margin-bottom: 15px;">Login: admin@zeus.com / adminpassword</p>
        {% if error %}<p style="color: #f87171; text-align: center; font-size: 13px; margin-bottom: 15px;">{{ error }}</p>{% endif %}
        <form method="POST">
            <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Email Address</label><br>
            <input type="email" name="email" required style="width: 100%; padding: 10px; margin: 6px 0 16px 0; background: rgba(30, 41, 59, 0.8); color: #fff; border: 1px solid #334155; border-radius: 6px; box-sizing: border-box; outline: none;"><br>
            <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Password</label><br>
            <input type="password" name="password" required style="width: 100%; padding: 10px; margin: 6px 0 20px 0; background: rgba(30, 41, 59, 0.8); color: #fff; border: 1px solid #334155; border-radius: 6px; box-sizing: border-box; outline: none;"><br>
            <button type="submit" style="width: 100%; padding: 12px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;">Sign In</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Assistant</title>
</head>
<body style="background: #0f172a url('https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1920&auto=format&fit=crop') no-repeat center center fixed; background-size: cover; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column;">
    
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
        <span style="font-weight: 600; font-size: 16px; letter-spacing: 0.5px;">Chat Assistant</span>
        <a href="/logout" style="color: #94a3b8; text-decoration: none; font-size: 13px; font-weight: 500;">Logout</a>
    </div>

    <div style="flex: 1; max-width: 700px; width: 100%; margin: 20px auto; display: flex; flex-direction: column; padding: 0 15px; box-sizing: border-box; overflow: hidden;">
        <div id="chat-box" style="flex: 1; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px); padding: 20px; overflow-y: auto; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: flex; flex-direction: column; gap: 15px; margin-bottom: 15px;">
            <div style="color: #64748b; text-align: center; font-size: 13px; margin-top: auto; margin-bottom: auto;">How can I help you today?</div>
        </div>

        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <input type="text" id="prompt-input" placeholder="Type a message..." style="flex: 1; padding: 14px 16px; background: rgba(30, 41, 59, 0.85); color: #fff; border: 1px solid #334155; border-radius: 8px; outline: none; font-size: 14px;" onkeydown="if(event.key === 'Enter') askAI();">
            <button onclick="askAI()" style="padding: 0 20px; background: #3b82f6; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px;">Send</button>
        </div>
    </div>

    <script>
    async function askAI() {
        let inputField = document.getElementById('prompt-input');
        let prompt = inputField.value.trim();
        if (!prompt) return;
        
        let chatBox = document.getElementById('chat-box');
        
        if (chatBox.children.length === 1 && chatBox.children[0].style.textAlign === 'center') {
            chatBox.innerHTML = '';
        }

        chatBox.innerHTML += `<div style="align-self: flex-end; background: #2563eb; color: #fff; padding: 10px 14px; border-radius: 10px; max-width: 80%; word-break: break-word; font-size: 14px;">${prompt}</div>`;
        inputField.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            let res = await fetch('/api/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: prompt})
            });
            let data = await res.json();
            
            chatBox.innerHTML += `<div style="align-self: flex-start; background: #1e293b; color: #f8fafc; padding: 10px 14px; border-radius: 10px; max-width: 80%; word-break: break-word; font-size: 14px; border: 1px solid #334155;">${data.response}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        } catch (err) {
            chatBox.innerHTML += `<div style="align-self: flex-start; background: #7f1d1d; color: #fca5a5; padding: 10px 14px; border-radius: 10px; max-width: 80%; font-size: 14px;">Error connecting to server.</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        

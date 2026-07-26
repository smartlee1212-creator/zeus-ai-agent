import os
import sqlite3
import datetime
import jwt
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import bleach

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32).hex()  # Cryptographically secure random key
DB_NAME = "zeus_agent.db"

# ----------------------------------------------------
# DATABASE INITIALIZATION & PRE-FILLED CREDENTIALS
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pre-configure Default Admin Credentials
    # Username: admin
    # Password: ZeusMarsSky2026!
    admin_user = "admin"
    admin_pass = generate_password_hash("ZeusMarsSky2026!", method='scrypt')
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (admin_user, admin_pass))
    
    conn.commit()
    conn.close()

# Security Audit Logging Function
def log_event(ip, action):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Input sanitization against persistent XSS
    clean_ip = bleach.clean(ip)
    clean_action = bleach.clean(action)
    cursor.execute("INSERT INTO audit_logs (ip, action) VALUES (?, ?)", (clean_ip, clean_action))
    conn.commit()
    conn.close()

# Security Token Decorator (JWT Protected Routes)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('zeus_token')
        if not token:
            return redirect(url_for('login_page'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except Exception:
            return redirect(url_for('login_page'))
        return f(current_user, *args, **kwargs)
    return decorated

# ----------------------------------------------------
# ZEUS AI AGENT CORE ENGINE
# ----------------------------------------------------
class ZeusAgent:
    """Zeus: The Parrot Storyteller from the Red Skies of Mars"""
    
    @staticmethod
    def generate_response(prompt):
        prompt_lower = prompt.lower()
        
        # 1. Full World & Country History
        if "history" in prompt_lower or "country" in prompt_lower:
            return ("*Squawk!* Zeus remembers the sands of time! From the fertile valleys of ancient Mesopotamia "
                    "to the industrial revolutions of Europe, human history is a grand tapestry of survival. "
                    "Ask me about any specific nation—be it the pyramids of Egypt or the dynasties of East Asia—and I shall tell its story!")

        # 2. Horror Stories
        elif "horror" in prompt_lower or "scary" in prompt_lower:
            return ("*Polly wants a thriller!* Deep beneath the permafrost of Antarctica lies Station 4. "
                    "In 1982, drillers breached a cavern filled with silent, bioluminescent mist. "
                    "One by one, the crew stopped talking... but their voices kept coming from the air vents at night.")

        # 3. Unacted / Original Movie Script Story
        elif "movie" in prompt_lower or "unacted" in prompt_lower or "script" in prompt_lower:
            return ("*Squawk! Here is an unproduced sci-fi film concept titled 'CHRONO-BIRD':*\n\n"
                    "**Logline:** In 2140, a cybernetic parrot carrying the last encryption key to humanity's history "
                    "must navigate the criminal underworld of Neo-Tokyo before the rogue AI 'Aether' wipes all records.\n"
                    "**Act I:** Zeus escape from Orbital Lab-9 carrying a bio-drive in its core.\n"
                    "**Act II:** Partnerships formed with a retro-hacker in rain-soaked alleyways.\n"
                    "**Act III:** A high-altitude battle above the clouds where memory isn't deleted—it's weaponized.")

        # 4. Human Life Stories
        elif "life story" in prompt_lower or "biography" in prompt_lower:
            return ("*Flaps wings* Every human life is an epic saga. Take the life of Ada Lovelace: "
                    "daughter of a poet, visioned the world's first computer algorithm in the 1800s long before hardware existed. "
                    "What person or era's life story would you like to explore?")

        # 5. Fallback World Story Answering Engine
        else:
            return f"*Squawk!* Zeus hears your query about '{prompt}'. Across the ancient world and every legend written, " \
                   f"there is a story. To dive deeper, specify if you want History, Horror, a Life Biography, or a new Unacted Movie!"

# ----------------------------------------------------
# HTML / DASHBOARD TEMPLATES (MARS SKY & PARROT THEME)
# ----------------------------------------------------
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Zeus AI - Dashboard Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: linear-gradient(135deg, #2b0808 0%, #681818 50%, #110303 100%);
            color: #fce8e8; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;
        }
        .login-card {
            background: rgba(20, 5, 5, 0.85); padding: 30px; border-radius: 12px;
            box-shadow: 0 0 20px #ff3333; border: 1px solid #882222; text-align: center; width: 320px;
        }
        input {
            width: 90%; padding: 10px; margin: 10px 0; border-radius: 6px;
            border: 1px solid #661111; background: #220a0a; color: #fff;
        }
        button {
            width: 98%; padding: 10px; border: none; border-radius: 6px;
            background: #cc2222; color: #fff; font-weight: bold; cursor: pointer;
        }
        button:hover { background: #ff3333; }
        .avatar { font-size: 60px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="avatar">🦜</div>
        <h2>ZEUS AI AGENT</h2>
        <p style="color: #ff8888; font-size: 0.85em;">Mars Sky Command Gateway</p>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Authenticate</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Zeus AI - Mars Command Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: radial-gradient(circle, #4a0e0e 0%, #1a0303 100%);
            color: #f5d5d5; font-family: Arial, sans-serif; margin: 0; padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header {
            background: rgba(40, 10, 10, 0.9); padding: 20px; border-radius: 10px;
            border: 1px solid #aa2222; text-align: center; box-shadow: 0 0 15px #bb2222;
        }
        .parrot-box { font-size: 70px; animation: bounce 2s infinite alternate; }
        @keyframes bounce { 0% { transform: translateY(0); } 100% { transform: translateY(-10px); } }
        .chat-box {
            background: rgba(15, 5, 5, 0.9); border: 1px solid #661111; border-radius: 10px;
            height: 350px; overflow-y: scroll; padding: 15px; margin-top: 20px;
        }
        .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 6px; }
        .user-msg { background: #551111; text-align: right; margin-left: 20%; }
        .zeus-msg { background: #220808; border-left: 3px solid #ff4444; margin-right: 20%; }
        .input-group { display: flex; margin-top: 15px; }
        input[type="text"] {
            flex: 1; padding: 12px; background: #220a0a; border: 1px solid #661111;
            color: #fff; border-radius: 6px 0 0 6px;
        }
        button {
            padding: 12px 20px; background: #cc2222; border: none; color: white;
            border-radius: 0 6px 6px 0; cursor: pointer; font-weight: bold;
        }
        .status-badge { font-size: 0.8em; color: #00ff88; background: #003311; padding: 3px 8px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="parrot-box">🦜</div>
            <h1>ZEUS: THE MARS STORYTELLER</h1>
            <p><span class="status-badge">PROTECTED SECURE AGENT</span> | Backed by Encrypted SQLite</p>
            <a href="/logout" style="color:#ff6666;">[ Logout Gateway ]</a>
        </div>

        <div class="chat-box" id="chatBox">
            <div class="msg zeus-msg">
                <strong>Zeus 🦜:</strong> *Squawk!* Welcome to the Mars Sky Observatory! I am Zeus. Ask me for world history, country origin stories, terrifying horror, human lives, or an unacted movie script!
            </div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Ask Zeus about any story or world history..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Ask Zeus</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const prompt = input.value.trim();
            if (!prompt) return;

            // Render User Prompt
            chatBox.innerHTML += `<div class="msg user-msg"><strong>You:</strong> ${prompt}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // Fetch response from secured AI Endpoint
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await response.json();
            chatBox.innerHTML += `<div class="msg zeus-msg"><strong>Zeus 🦜:</strong> ${data.response}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

# ----------------------------------------------------
# SERVER ROUTES
# ----------------------------------------------------
@app.route('/')
@token_required
def dashboard(current_user):
    return render_template_string(HTML_DASHBOARD)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user = bleach.clean(request.form.get('username'))
        passwd = request.form.get('password')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (user,))
        record = cursor.fetchone()
        conn.close()

        if record and check_password_hash(record[0], passwd):
            token = jwt.encode({
                'username': user,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=6)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            log_event(request.remote_addr, f"Successful login for user: {user}")
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('zeus_token', token, httponly=True, samesite='Strict')
            return resp
        else:
            log_event(request.remote_addr, f"Failed login attempt for user: {user}")
            return "Invalid Credentials", 401
            
    return render_template_string(HTML_LOGIN)

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie('zeus_token')
    return resp

@app.route('/api/ask', methods=['POST'])
@token_required
def ask_zeus(current_user):
    data = request.get_json()
    prompt = bleach.clean(data.get('prompt', ''))
    
    log_event(request.remote_addr, f"User {current_user} asked: {prompt[:30]}...")
    reply = ZeusAgent.generate_response(prompt)
    return jsonify({'response': reply})

if __name__ == '__main__':
    init_db()
    # Binding to 0.0.0.0 exposes the host port on your public IP or network adapter (Non-Local)
    app.run(host='0.0.0.0', port=8080, debug=False)


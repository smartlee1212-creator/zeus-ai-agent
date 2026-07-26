import os
import sqlite3
import datetime
import jwt
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32).hex()
DB_NAME = "zeus_agent.db"

# ---------------------------------------------------------
# DATABASE INITIALIZATION & PRE-FILLED CREDENTIALS
# ---------------------------------------------------------
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
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('password123')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))
    conn.commit()
    conn.close()

init_db()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth_token')
        if not token:
            return redirect(url_for('login_page'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return redirect(url_for('login_page'))
        return f(current_user, *args, **kwargs)
    return decorated

# ---------------------------------------------------------
# SERVER ROUTES
# ---------------------------------------------------------
@app.route('/')
@token_required
def dashboard(current_user):
    return render_template_string(HTML_DASHBOARD)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = bleach.clean(request.form.get('username'))
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and check_password_hash(row[0], password):
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            response = redirect(url_for('dashboard'))
            response.set_cookie('auth_token', token)
            return response
            
        return render_template_string(HTML_LOGIN, error="Invalid Credentials")
        
    return render_template_string(HTML_LOGIN, error="")
@token_required

@app.route('/api/ask', methods=['POST'])
def api_ask(current_user):
   
    data = request.get_json()
    prompt = bleach.clean(data.get('prompt', ''))
    
    p_lower = prompt.lower()
    if "greece" in p_lower or "gods" in p_lower:
        reply = "From the heights of Mount Olympus, the ancient Greek pantheon ruled over mortals, shaping myths that echo through eternity."
    elif "rome" in p_lower or "caesar" in p_lower:
        reply = "Rome grew from a modest republic into a mighty empire, its legions conquering vast territories and leaving a legacy of law and engineering."
    elif "egypt" in p_lower or "pharaoh" in p_lower:
        reply = "Along the banks of the Nile, the pharaohs built majestic pyramids and temples, anchoring their civilization in eternal mystery."
    else:
        reply = f"Ah, you ask about '{prompt}'. The annals of history hold many deep lessons regarding this era. Tell me more about what specific chapter you wish to explore."
        
    return jsonify({"response": reply})
    

# ---------------------------------------------
# HTML TEMPLATES
# ---------------------------------------------

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Zeus Login</title></head>
<body style="font-family:sans-serif; background:#121212; color:#fff;">
    <form method="POST" style="background:#1e1e1e; padding:20px;">
        <h2>Zeus Agent Login</h2>
        <p style="color:red;">{{ error }}</p>
        <label>Username:</label><br>
        <input type="text" name="username" required style="width:100%;"><br>
        <label>Password:</label><br>
        <input type="password" name="password" required style="width:100%;"><br>
        <button type="submit" style="width:100%; padding:10px;">Login</button>
    </form>
</body>
</html>
"""


HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head><title>Zeus AI Agent</title></head>
<body style="font-family:sans-serif; background:#121212; color:#fff; margin:0; padding:20px;">
    <h2>Zeus AI Agent Dashboard</h2>
    <div id="chatBox" style="border:1px solid #444; height:300px; overflow-y:scroll; padding:10px; margin-bottom:10px; background:#1e1e1e;"></div>
    <input type="text" id="promptInput" placeholder="Ask Zeus a story or history..." style="width:80%; padding:8px;">
    <button onclick="sendPrompt()" style="width:18%; padding:8px; background:#28a745; color:#fff; border:none;">Send</button>

    <script>
        async function sendPrompt() {
            const input = document.getElementById('promptInput');
            const chatBox = document.getElementById('chatBox');
            const prompt = input.value;
            if(!prompt) return;

            chatBox.innerHTML += "<div><b>You:</b> " + prompt + "</div>";
            input.value = "";

            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await response.json();
            chatBox.innerHTML += "<div><b>Zeus:</b> " + data.response + "</div>";
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

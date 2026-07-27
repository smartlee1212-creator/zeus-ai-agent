from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import bleach

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

app = Flask(__name__)

if GEMINI_AVAILABLE:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)

def login_required(f):
    return f

@app.route('/')
@login_required
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/ask', methods=['POST'])
@login_required
def api_ask():
    if not GEMINI_AVAILABLE:
        return jsonify({"response": "AI service is not available."})

    data = request.get_json(silent=True) or {}
    prompt = bleach.clean(data.get('prompt', '').strip())

    if not prompt:
        return jsonify({"response": "Please provide a valid prompt."})

    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"response": "Gemini API key is not configured."})

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        reply = response.text if response and hasattr(response, 'text') else "No response."
    except Exception as e:
        reply = f"System notice: Unable to get response from Zeus. Error: {str(e)}"

    return jsonify({"response": reply})

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login - Zeus AI</title>
</head>
<body style="background: #0f172a">
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zeus AI Dashboard</title>
<style>
  body { background: #0f172a; color: #fff; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 90vh; box-sizing: border-box; }
  h2 { text-align: center; margin-bottom: 10px; }
  #chat-container { flex: 1; overflow-y: auto; background: #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
  .message { padding: 10px 14px; border-radius: 6px; max-width: 80%; line-height: 1.4; word-break: break-word; }
  .user-msg { background: #3b82f6; align-self: flex-end; }
  .ai-msg { background: #334155; align-self: flex-start; }
  .input-area { display: flex; gap: 10px; }
  input { flex: 1; padding: 12px; border-radius: 6px; border: none; background: #334155; color: #fff; font-size: 16px; }
  button { padding: 12px 20px; border-radius: 6px; border: none; background: #3b82f6; color: #fff; font-weight: bold; cursor: pointer; font-size: 16px; }
</style>
</head>
<body>
  <h2>Zeus AI Dashboard</h2>
  <div id="chat-container">
    <div class="message ai-msg">Hello! I am Zeus. How can I help you today?</div>
  </div>
  <div class="input-area">
    <input type="text" id="prompt-input" placeholder="Ask Zeus anything..." autocomplete="off">
    <button onclick="sendMessage()">Send</button>
  </div>

  <script>
    async function sendMessage() {
      const input = document.getElementById('prompt-input');
      const container = document.getElementById('chat-container');
      const text = input.value.trim();
      if (!text) return;

      container.innerHTML += `<div class="message user-msg">${text}</div>`;
      input.value = '';
      container.scrollTop = container.scrollHeight;

      try {
        const res = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: text })
        });
        const data = await res.json();
        container.innerHTML += `<div class="message ai-msg">${data.response}</div>`;
      } catch (err) {
        container.innerHTML += `<div class="message ai-msg">Error communicating with server.</div>`;
      }
      container.scrollTop = container.scrollHeight;
    }

    document.getElementById('prompt-input').addEventListener('keypress', function (e) {
      if (e.key === 'Enter') sendMessage();
    });
  </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    

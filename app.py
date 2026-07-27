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
</head>
<body style="background: #0f172a">
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

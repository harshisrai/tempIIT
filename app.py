import hashlib
import requests
import webbrowser
from flask import Flask, request, render_template_string
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# --- 🧠 Fill in your credentials here ---
API_KEY=os.getenv("API_KEY")
API_SECRET=os.getenv("API_SECRET")  

# --- HTML template for visual confirmation ---
html_template = """
<!doctype html>
<html>
<head>
    <title>Kite Redirect</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f5f5f5; }
        pre { background: #fff; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Kite Connect Authentication Result</h1>
    {% if error %}
        <p style="color: red;">Error: {{ error }}</p>
    {% else %}
        <p><b>Request Token:</b> {{ request_token }}</p>
        <p><b>Access Token:</b> {{ access_token }}</p>
        <h2>Full Response:</h2>
        <pre>{{ data | tojson(indent=2) }}</pre>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    login_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}"
    return f"""
    <h2>✅ Flask redirect server is running.</h2>
    <p>Click below to start the login flow:</p>
    <a href="{login_url}" target="_blank">{login_url}</a>
    """

# --- 🧭 Redirect URL endpoint ---
@app.route("/kite_redirect")
def kite_redirect():
    # Kite sends ?request_token=...&status=success
    request_token = request.args.get("request_token")
    status = request.args.get("status")

    if not request_token:
        return render_template_string(html_template, error="Missing request_token", request_token=None, access_token=None, data=None)

    print(f"✅ Received request_token: {request_token}")

    # Step 1: Compute checksum = SHA256(api_key + request_token + api_secret)
    raw = API_KEY + request_token + API_SECRET
    checksum = hashlib.sha256(raw.encode()).hexdigest()
    print(f"🔐 Generated checksum: {checksum}")

    # Step 2: Exchange request_token for access_token
    url = "https://api.kite.trade/session/token"
    headers = {"X-Kite-Version": "3"}
    payload = {
        "api_key": API_KEY,
        "request_token": request_token,
        "checksum": checksum
    }

    response = requests.post(url, headers=headers, data=payload)
    print(f"🌐 POST {url} → {response.status_code}")

    try:
        data = response.json()
    except Exception:
        data = {"error": "Invalid JSON", "text": response.text}

    # Step 3: Extract access_token if successful
    access_token = data.get("data", {}).get("access_token") if "data" in data else None

    # Log for debugging
    print("🔍 Kite response:")
    print(data)

    # Step 4: Render HTML with result
    return render_template_string(html_template,
                                  error=None,
                                  request_token=request_token,
                                  access_token=access_token,
                                  data=data)


if __name__ == "__main__":
    print("🚀 Starting redirect server on http://localhost:8000 ...")
    webbrowser.open(f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}")
    app.run(host="0.0.0.0", port=8000, debug=True)

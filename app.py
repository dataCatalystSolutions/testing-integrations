from flask import Flask, redirect, request, render_template, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# TikTok API credentials
CLIENT_KEY = 'sbawg3wqzsusdoh4tt'
CLIENT_SECRET = 'YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR'
REDIRECT_URI = 'https://testing-integrations.onrender.com/callback/'  # Update for deployment

# Step 1: Start OAuth Flow
@app.route("/")
def home():
    return '<a href="/start-auth">Login with TikTok</a>'  # Simple login link

@app.route("/start-auth")
def start_auth():
    scope = "user.info.basic"
    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={CLIENT_KEY}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state=test_state"
    )
    return redirect(oauth_url)

# Step 2: Handle OAuth Callback
@app.route("/callback/")
def callback():
    code = request.args.get("code")
    print("DEBUG: Received code from TikTok:", code)  # Debugging step 1

    if not code:
        return "Authorization failed or no code received.", 400

    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    print("DEBUG: Sending token request with payload:", payload)  # Debugging step 2


    response = requests.post(token_url, json=payload)
    print("DEBUG: Token Response Status Code:", response.status_code)
    print("DEBUG: Token Response JSON:", response.text)  # Log the full response

    if response.status_code == 200:
        data = response.json()
        session["access_token"] = data.get("access_token")  # Store token
        print("DEBUG: Stored Access Token:", session['access_token'])  # Debugging step 5
        return f"Access Token: {session['access_token']}", 200
    else:
        return f"Failed to obtain access token: {response.text}", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
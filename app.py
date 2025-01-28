from flask import Flask, redirect, request, render_template, url_for, session
import requests
import os
import logging

logging.basicConfig(level=logging.DEBUG)

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
    scope = "user.info.basic,video.upload"
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
    app.logger.info("DEBUG: Received code from TikTok: %s", code)  # Debugging step 1

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
    app.logger.info("DEBUG: Sending token request with payload: %s", payload)  # Debugging step 2

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)

    app.logger.info("DEBUG: Token Response Status Code: %s", response.status_code)
    app.logger.info("DEBUG: Token Response JSON: %s", response.text)  # Log the full response

    if response.status_code == 200:
        data = response.json()
        
        # Store the access token, refresh token, and open_id
        session["access_token"] = data.get("access_token")
        session["refresh_token"] = data.get("refresh_token")
        session["open_id"] = data.get("open_id")
        
        app.logger.info("DEBUG: Stored Access Token: %s", session["access_token"])  
        app.logger.info("DEBUG: Stored Refresh Token: %s", session["refresh_token"])  
        app.logger.info("DEBUG: Stored Open ID: %s", session["open_id"])  

        return f"Access Token: {session['access_token']}", 200
    else:
        return f"Failed to obtain access token: {response.text}", 400
        
# Step 3: Token Refresh Endpoint (For When Token Expires)
@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" not in session:
        return "No refresh token available. Please log in again.", 400

    refresh_url = "https://open.tiktokapis.com/v2/oauth/token/"
    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": session["refresh_token"],
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(refresh_url, data=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        session["access_token"] = data.get("access_token")
        session["refresh_token"] = data.get("refresh_token")  # Save new refresh token

        app.logger.info("DEBUG: Refreshed Access Token: %s", session["access_token"])
        return "Access token refreshed successfully!", 200
    else:
        return f"Failed to refresh access token: {response.text}", 400


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # Enables debug logging
    app.run(host="0.0.0.0", port=5000)
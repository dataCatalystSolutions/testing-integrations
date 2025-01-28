from flask import Flask, redirect, request, render_template, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# TikTok API credentials
CLIENT_KEY = 'sbawg3wqzsusdoh4tt'
CLIENT_SECRET = 'YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR'
REDIRECT_URI = 'https://testing-integrations.onrender.com/callback/'  # Update for deployment

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

# Start Authentication (Step 1)
@app.route('/start-auth')
def start_auth():
    """ Redirect user to TikTok for authentication """
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

# Callback Route (Step 2)
@app.route('/callback/')
def callback():
    """ Handles TikTok redirect and retrieves access token """
    code = request.args.get('code')
    if code:
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        payload = {
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }
        response = requests.post(token_url, json=payload)
        if response.status_code == 200:
            data = response.json()
            session["access_token"] = data.get("access_token")
            return redirect(url_for('upload_video_page'))
        else:
            return "Failed to exchange authorization code for access token.", 400
    return "Authorization failed or no code received.", 400

# Upload Video Page (Step 3)
@app.route('/upload-video-page')
def upload_video_page():
    """ Page where the user selects a video to upload """
    if "access_token" not in session:
        return redirect(url_for('start_auth'))
    return render_template("upload.html")  # New upload page

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
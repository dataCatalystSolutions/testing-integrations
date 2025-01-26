from flask import Flask, redirect, request, render_template

app = Flask(__name__)

# TikTok API credentials
CLIENT_KEY = "sbawg3wqzsusdoh4tt"  # Replace with your actual Client Key
CLIENT_SECRET = "YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR"  # Replace with your actual Client Secret
REDIRECT_URI = "https://testing-integrations.onrender.com/callback/"  # Replace with your Render URL

# Home page with a button
@app.route('/')
def home():
    return render_template("index.html")

# Route to generate OAuth URL and redirect to TikTok
@app.route('/start-auth')
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

# Callback route to handle TikTok redirection
@app.route('/callback/')
def callback():
    code = request.args.get('code')
    if code:
        return f"Authorization successful! Your code is: {code}", 200
    else:
        return "Authorization failed or no code received.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

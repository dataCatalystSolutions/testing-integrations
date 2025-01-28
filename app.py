from flask import Flask, redirect, request, render_template, jsonify, session
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session storage


# TikTok API credentials
CLIENT_KEY = 'sbawg3wqzsusdoh4tt'  # Replace with your actual Client Key
CLIENT_SECRET = 'YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR'  # Replace with your actual Client Secret
REDIRECT_URI = 'https://testing-integrations.onrender.com/callback/'  # Replace with your Render URL

# Home page with a button
@app.route('/')
def home():
    return render_template("index.html")

# Route to generate OAuth URL and redirect to TikTok
@app.route('/start-auth')
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

# Callback route to handle TikTok redirection
@app.route('/callback/')
def callback():
    code = request.args.get('code')
    if code:
        # Exchange the authorization code for an access token
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
            return "Authorization successful! Access token obtained.", 200
        else:
            return f"Failed to get access token: {response.text}", 400
    return "Authorization failed or no code received.", 400

# Route to upload video
@app.route('/upload-video', methods=['POST'])
def upload_video():
    access_token = session.get("access_token")
    if not access_token:
        return "User is not authenticated. Please log in first.", 401
    
    file = request.files.get('video')
    if not file:
        return "No file uploaded.", 400
    
    # Save the file temporarily
    file_path = f"./uploads/{file.filename}"
    file.save(file_path)
    
    # Step 1: Initialize video upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    video_size = os.path.getsize(file_path)
    payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,  # Get file size
            "chunk_size": video_size,  # Full file size for single-chunk upload
            "total_chunk_count": 1  # Number of chunks (1 for single upload)
        }
    }
    response = requests.post(init_url, headers=headers, json=payload)
    if response.status_code != 200:
        return f"Failed to initialize video upload: {response.text}", 400
    
    data = response.json().get("data", {})
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")
    
    # Step 2: Upload the video file (single chunk assumed here)
    with open(file_path, "rb") as video_file:
        upload_response = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"
            },
            data=video_file
        )
    if upload_response.status_code != 200:
        return f"Failed to upload video: {upload_response.text}", 400
    
    # Step 3: Check the status of the post
    status_url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    status_payload = {"publish_id": publish_id}
    status_response = requests.post(status_url, headers=headers, json=status_payload)
    if status_response.status_code == 200:
        return "Video uploaded successfully!", 200
    else:
        return f"Failed to fetch post status: {status_response.text}", 400
    
# Check token status
@app.route('/check-token')
def check_token():
    access_token = session.get("access_token")
    if not access_token:
        return "User not authenticated.", 401

    url = "https://open.tiktokapis.com/v2/user/info/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    return response.json(), response.status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

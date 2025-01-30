from flask import Flask, redirect, request, render_template, url_for, session
import requests
import os
import logging
import math

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# TikTok API credentials
CLIENT_KEY = 'sbawg3wqzsusdoh4tt'
CLIENT_SECRET = 'YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR'
REDIRECT_URI = 'https://testing-integrations.onrender.com/callback/'  # Update for deployment

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists

# Home Page - Show login or upload options
@app.route("/")
def home():
    return render_template("index.html")

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
    
# Route to display the upload form
@app.route("/upload-video")
def upload_video():
    if "access_token" not in session:
        return redirect(url_for("start_auth"))  # Redirect if not logged in
    
    return render_template("upload.html")  # Render the upload form

@app.route("/process-upload", methods=["POST"])
def process_upload():
    if "access_token" not in session:
        return redirect(url_for("start_auth"))  # Ensure user is logged in

    access_token = session["access_token"]

    # Get uploaded file & caption
    video_file = request.files.get("video")
    caption = request.form.get("caption")

    if not video_file:
        return "No video file uploaded.", 400

    # Save video file temporarily
    video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(video_path)
    
    # Step 1: Initialize TikTok Video Upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    video_size = os.path.getsize(video_path)  # Get file size
    CHUNK_SIZE = 64 * 1024 * 1024  # TikTok allows a max of 64MB per chunk
    TOTAL_CHUNKS = math.ceil(video_size / CHUNK_SIZE)
    app.logger.info(f"DEBUG: Video size: {video_size} bytes, Chunk size: {CHUNK_SIZE}, Total Chunks: {TOTAL_CHUNKS}")


    payload = {
    "source_info": {
        "source": "FILE_UPLOAD",
        "video_size": video_size,
        "chunk_size": CHUNK_SIZE,
        "total_chunk_count": TOTAL_CHUNKS
        }
    }

    # Send request to initialize upload
    app.logger.info("DEBUG: Payload being sent: %s", payload)
    init_response = requests.post(init_url, headers=headers, json=payload)
    app.logger.info("DEBUG: TikTok API Response: %s", init_response.text)
    response_data = init_response.json()
    
    if init_response.status_code == 200:
        upload_url = response_data.get("data", {}).get("upload_url")
        publish_id = response_data.get("data", {}).get("publish_id")

        session["upload_url"] = upload_url  # Store upload URL in session
        session["publish_id"] = publish_id  # Store publish ID in session

        # Upload the video in chunks
        with open(video_path, "rb") as file:
            for chunk_index in range(TOTAL_CHUNKS):
                chunk = file.read(CHUNK_SIZE)
                chunk_start = chunk_index * CHUNK_SIZE
                chunk_end = min((chunk_index + 1) * CHUNK_SIZE - 1, video_size - 1)

                upload_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes {chunk_start}-{chunk_end}/{video_size}"
                }

                upload_response = requests.put(upload_url, headers=upload_headers, data=chunk)
                app.logger.info(f"DEBUG: Uploading chunk {chunk_index + 1}/{TOTAL_CHUNKS}")

                if upload_response.status_code != 200:
                    return f"Failed to upload chunk {chunk_index + 1}: {upload_response.text}", 400

        # Finalize the upload
        publish_url = "https://open.tiktokapis.com/v2/post/publish/video/"
        publish_payload = {
            "publish_id": publish_id,
            "post_info": {"title": caption}
        }
        publish_response = requests.post(publish_url, headers=headers, json=publish_payload)

        if publish_response.status_code == 200:
            return "Video uploaded successfully!", 200
        else:
            return f"Failed to publish video: {publish_response.text}", 400

    else:
        return f"Failed to initialize video upload: {response_data}", 400


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # Enables debug logging
    app.run(host="0.0.0.0", port=5000)
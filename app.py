from flask import Flask, redirect, request, render_template, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# TikTok API credentials
CLIENT_KEY = 'sbawg3wqzsusdoh4tt'
CLIENT_SECRET = 'YX8gMe5OhNXovaw9Uj3IGSoMYOtYH7KR'
REDIRECT_URI = 'https://testing-integrations.onrender.com/callback/'  # Update for deployment

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

# Step 1: Handle Button Click to Start Authentication or Upload
@app.route('/post-video')
def post_video():
    if 'access_token' not in session:
        return redirect(url_for('start_auth'))  # Redirect to authentication

    return redirect(url_for('upload_video'))  # Proceed to upload video

# Step 2: OAuth Authentication
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

# Step 3: Handle TikTok OAuth Callback
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
            session['access_token'] = data.get("access_token")  # Store in session
            return redirect(url_for('upload_video'))
        else:
            return "Failed to obtain access token.", 400
    return "Authorization failed.", 400


# Step 4: Upload Video (Placeholder)
@app.route('/upload-video')
def upload_video():
    if 'access_token' not in session:
        return redirect(url_for('start_auth'))  # Make sure user is logged in
    
    return render_template("upload.html")  # Show file upload form

# Step 5: Process Video Upload
@app.route('/process-upload', methods=['POST'])
def process_upload():
    if 'access_token' not in session:
        return redirect(url_for('start_auth'))  # Ensure user is logged in

    access_token = session['access_token']

    # Get uploaded file & caption
    video_file = request.files.get('video')
    caption = request.form.get('caption')

    if not video_file:
        return "No video file uploaded.", 400

    # Save video file temporarily
    video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(video_path)

    # Step 1: Initialize TikTok video upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {"Authorization": f"Bearer {access_token}"}
    video_size = os.path.getsize(video_path)

    payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,  
            "chunk_size": video_size,  
            "total_chunk_count": 1  
        }
    }
    
    init_response = requests.post(init_url, headers=headers, json=payload)

    if init_response.status_code != 200:
        return f"Failed to initialize video upload: {init_response.text}", 400

    data = init_response.json()
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")

    # Step 2: Upload video
    with open(video_path, "rb") as video_file:
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

    # Step 3: Publish Video with Caption
    publish_url = "https://open.tiktokapis.com/v2/post/publish/video/"
    publish_payload = {
        "publish_id": publish_id,
        "post_info": {
            "title": caption  # Use caption as title
        }
    }

    publish_response = requests.post(publish_url, headers=headers, json=publish_payload)

    if publish_response.status_code == 200:
        return "Video uploaded successfully!", 200
    else:
        return f"Failed to publish video: {publish_response.text}", 400

# Step 6: Confirm Upload Success
@app.route('/upload-success')
def upload_success():
    return "Your video has been uploaded to TikTok successfully!"
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, send_from_directory, render_template_string
import subprocess
import signal
import os
import requests
import zipfile
from io import BytesIO
from datetime import datetime
import atexit
import glob
import sys

app = Flask(__name__)

# global handle
_screensaver_proc = None

DOWNLOAD_URL = "http://meghavi-kiosk-api.onrender.com/api/videos/download-all"
EXTRACT_DIR = "downloaded_videos"
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')

def open_screensaver():
    global _screensaver_proc
    if _screensaver_proc is None or _screensaver_proc.poll() is not None:
        script = os.path.join(os.path.dirname(__file__), 'screensaver.py')
        _screensaver_proc = subprocess.Popen([sys.executable, script])

def close_screensaver():
    global _screensaver_proc
    if _screensaver_proc and _screensaver_proc.poll() is None:
        _screensaver_proc.terminate()
        try:
            _screensaver_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("[server.py] Terminate timed out, killing screensaver.py")
            _screensaver_proc.kill()
        _screensaver_proc = None

# --- Cleanup screensaver.py process on exit

def cleanup_screensaver():
    close_screensaver()

atexit.register(cleanup_screensaver)

# --- Video screensaver page and video serving
@app.route('/')
def index():
    video_files = [os.path.basename(f) for f in glob.glob(os.path.join(VIDEO_FOLDER, '*.mp4'))]
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screensaver Videos</title>
        <style>body, html { margin:0; padding:0; background:black; height:100%; width:100%; overflow:hidden; }</style>
    </head>
    <body>
        <video id="screensaverVideo" width="100%" height="100%" autoplay muted></video>
        <script>
            const videos = {{ videos|safe }};
            let idx = 0;
            const videoElem = document.getElementById('screensaverVideo');
            function playNext() {
                videoElem.src = '/videos/' + videos[idx];
                videoElem.play();
            }
            videoElem.onended = function() {
                idx = (idx + 1) % videos.length;
                playNext();
            };
            if (videos.length > 0) {
                playNext();
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, videos=video_files)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

# --- Process control for screensaver.py
@app.route('/url_matched', methods=['POST'])
def url_matched():
    data = request.get_json()
    status = data.get("status")
    url = data.get("url")

    if status == "entered":
        print(f"✅ User ENTERED target page: {url} - Starting screensaver.py")
        open_screensaver()
    elif status == "left":
        print(f"🚪 User LEFT target page. Now on: {url} - Stopping screensaver.py")
        close_screensaver()
    else:
        print(f"⚠️ Unknown status: {data}")
    
    return jsonify({"status": "received"}), 200

@app.route('/trigger-download', methods=['POST'])
def trigger_download():
    try:
        print(f"[{datetime.now()}] Download started...")

        response = requests.get(DOWNLOAD_URL)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download zip"}), 500

        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            os.makedirs(EXTRACT_DIR, exist_ok=True)
            zip_ref.extractall(EXTRACT_DIR)

        # Remove the old 'videos' folder if it exists
        videos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
        if os.path.exists(videos_path):
            import shutil
            shutil.rmtree(videos_path)
        # Rename the extracted folder to 'videos'
        extracted_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXTRACT_DIR)
        os.rename(extracted_full_path, videos_path)

        print(f"[{datetime.now()}] Download complete. Extracted to 'videos'")
        return jsonify({"status": "Downloaded and extracted, videos folder replaced"}), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
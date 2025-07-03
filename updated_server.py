# ✅ Updated server.py with /url_matched logic
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import requests
import zipfile
import shutil
import time
from io import BytesIO
from datetime import datetime
import subprocess
import sys
import glob

app = Flask(__name__)
CORS(app)

# Global screensaver process handle
_screensaver_proc = None

# Paths
DOWNLOAD_URL = "http://meghavi-kiosk-api.onrender.com/api/videos/download-all"
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')
TEMP_FOLDER = os.path.join(os.path.dirname(__file__), 'videos_new')
STOP_VLC_FLAG = os.path.join(os.path.dirname(__file__), 'stop_vlc.txt')

# --- Screensaver process control

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
            _screensaver_proc.kill()
        _screensaver_proc = None

# --- URL matched endpoint from Chrome extension
@app.route('/url_matched', methods=['POST'])
def url_matched():
    data = request.get_json()
    status = data.get("status")
    url = data.get("url")

    if status == "entered":
        print(f"✅ ENTERED target page: {url} — launching screensaver")
        open_screensaver()
    elif status == "left":
        print(f"🚪 LEFT target page: {url} — closing screensaver")
        close_screensaver()
    else:
        print(f"⚠️ Unknown URL event: {data}")

    return jsonify({"status": "received"}), 200

# --- Video preview page
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

# --- Triggered by Chrome extension or scheduled alarm
@app.route('/trigger-download', methods=['POST'])
def trigger_download():
    try:
        print(f"[{datetime.now()}] 🔔 Triggered video update...")

        # Signal to stop VLC
        with open(STOP_VLC_FLAG, "w") as f:
            f.write("stop")

        # Wait for VLC to release files
        for attempt in range(5):
            try:
                if os.path.exists(VIDEO_FOLDER):
                    shutil.rmtree(VIDEO_FOLDER)
                break
            except Exception as e:
                print(f"⏳ Attempt {attempt+1}/5 — Waiting for VLC to release video files... {e}")
                time.sleep(1)
        else:
            return jsonify({"error": "Could not delete videos folder after 5 tries"}), 500

        # Download video ZIP
        response = requests.get(DOWNLOAD_URL)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download video zip"}), 500

        # Extract to temp
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            os.makedirs(TEMP_FOLDER, exist_ok=True)
            zip_ref.extractall(TEMP_FOLDER)

        os.rename(TEMP_FOLDER, VIDEO_FOLDER)

        print(f"[{datetime.now()}] ✅ Video update completed.")
        return jsonify({"status": "Videos updated successfully"}), 200

    except Exception as e:
        print(f"❌ Error in /trigger-download: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)

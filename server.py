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

def cleanup_screensaver():
    close_screensaver()

atexit.register(cleanup_screensaver)

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screensaver Video</title>
        <style>
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: black;
                height: 100%;
            }
            video {
                position: fixed;
                top: 50%;
                left: 50%;
                min-width: 100%;
                min-height: 100%;
                transform: translate(-50%, -50%);
                object-fit: cover;
            }
        </style>
    </head>
    <body>
        <video id="myVideo" loop playsinline>
            <source src="/videos/video.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>

        <div id="overlay" style="
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: black;
            color: white;
            font-size: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10;
        ">
            Click to start screensaver
        </div>

        <script>
            const video = document.getElementById("myVideo");
            const overlay = document.getElementById("overlay");

            overlay.onclick = () => {
                overlay.remove();
                video.muted = false;
                video.volume = 1.0;
                video.play().then(() => {
                    console.log("Video is playing with sound.");
                }).catch((err) => {
                    console.warn("Autoplay with sound failed:", err);
                });
            };
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

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

        videos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
        if os.path.exists(videos_path):
            import shutil
            shutil.rmtree(videos_path)

        extracted_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXTRACT_DIR)
        os.rename(extracted_full_path, videos_path)

        print(f"[{datetime.now()}] Download complete. Extracted to 'videos'")
        return jsonify({"status": "Downloaded and extracted, videos folder replaced"}), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)

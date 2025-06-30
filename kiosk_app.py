from flask import Flask, request, jsonify, send_from_directory, render_template_string
import cv2
import time
import threading
import os
import requests
import zipfile
from io import BytesIO
from datetime import datetime
import atexit
import sys
import subprocess
from ultralytics import YOLO
import glob
import shutil

app = Flask(__name__)

# --- Configuration
TARGET_URL = "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy"
DOWNLOAD_URL = "http://meghavi-kiosk-api.onrender.com/api/videos/download-all"
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')
EXTRACT_DIR = "downloaded_videos"
MODEL_PATH = "models/model.pt"
FACE_DISTANCE_THRESHOLD = 110  # cm
NO_FACE_TIMER_SECONDS = 5  # seconds
A = 9703.20  # Distance calculation constant
B = -0.4911842338691967  # Distance calculation constant

# Global state
_screensaver_proc = None
_face_detection_thread = None
_stop_face_detection = threading.Event()

def start_screensaver():
    global _screensaver_proc
    if _screensaver_proc is None or _screensaver_proc.poll() is not None:
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Update path if needed
        try:
            print("Starting screensaver with Chrome")
            _screensaver_proc = subprocess.Popen([
                chrome_path,
                "--kiosk",
                "--start-fullscreen",
                "--new-window",
                "http://localhost:5000/"
            ])
            return True
        except FileNotFoundError:
            print(f"Error: Chrome not found at {chrome_path}")
            return False
    return True

def stop_screensaver():
    global _screensaver_proc
    if _screensaver_proc and _screensaver_proc.poll() is None:
        print("Terminating screensaver")
        _screensaver_proc.terminate()
        try:
            _screensaver_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("Terminate timed out, killing screensaver")
            _screensaver_proc.kill()
        _screensaver_proc = None

def face_detection_loop():
    global _screensaver_proc
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file {MODEL_PATH} not found.")
        return
    model = YOLO(MODEL_PATH)
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Unable to access webcam.")
            return
        frame_count = 0
        no_face_start = None
        last_face_in_range = False
        while not _stop_face_detection.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            frame_count += 1
            if frame_count % 5 == 0:  # Process every 5th frame
                results = model(frame, conf=0.4, verbose=False)
                detections = results[0].boxes
                face_in_range = False
                if detections is not None:
                    for box in detections:
                        conf = float(box.conf[0])
                        if conf < 0.4:
                            continue
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        area_px = (x2 - x1) * (y2 - y1)
                        distance = A * (area_px ** B)
                        if distance < FACE_DISTANCE_THRESHOLD:
                            face_in_range = True
                            break
                last_face_in_range = face_in_range
            else:
                face_in_range = last_face_in_range
            now = time.time()
            if not face_in_range:
                if no_face_start is None:
                    no_face_start = now
                elif now - no_face_start >= NO_FACE_TIMER_SECONDS:
                    if _screensaver_proc is None or _screensaver_proc.poll() is not None:
                        start_screensaver()
            else:
                no_face_start = None
                if _screensaver_proc is not None and _screensaver_proc.poll() is None:
                    stop_screensaver()
            time.sleep(0.05)  # Reduce CPU usage
    except KeyboardInterrupt:
        print("\nExiting face detection...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_screensaver()

def start_face_detection():
    global _face_detection_thread, _stop_face_detection
    if _face_detection_thread is None or not _face_detection_thread.is_alive():
        _stop_face_detection.clear()
        _face_detection_thread = threading.Thread(target=face_detection_loop)
        _face_detection_thread.start()
        print("Started face detection")
        return True
    return True

def stop_face_detection():
    global _face_detection_thread, _stop_face_detection
    if _face_detection_thread is not None and _face_detection_thread.is_alive():
        print("Stopping face detection")
        _stop_face_detection.set()
        _face_detection_thread.join(timeout=5)
        if _face_detection_thread.is_alive():
            print("Warning: Face detection thread did not stop gracefully")
        _face_detection_thread = None
    stop_screensaver()

def cleanup():
    print("Cleaning up...")
    stop_face_detection()
    stop_screensaver()

atexit.register(cleanup)

@app.route('/')
def index():
    video_files = [os.path.basename(f) for f in glob.glob(os.path.join(VIDEO_FOLDER, '*.mp4'))]
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Screensaver</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: black;
            }
            video {
                width: 100%;
                height: 100%;
                object-fit: fill;
            }
        </style>
    </head>
    <body>
        <video id="videoPlayer" autoplay>
            <source src="/videos/{{ videos[0] }}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
        <script>
            const videos = {{ videos | tojson }};
            let currentVideoIndex = 0;
            const videoPlayer = document.getElementById('videoPlayer');
            videoPlayer.onended = function() {
                currentVideoIndex = (currentVideoIndex + 1) % videos.length;
                videoPlayer.src = '/videos/' + videos[currentVideoIndex];
                videoPlayer.play();
            };
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, videos=video_files)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route('/url_matched', methods=['POST'])
def url_matched():
    data = request.get_json()
    if not data or 'status' not in data or 'url' not in data:
        print(f"⚠️ Invalid request data: {data}")
        return jsonify({"error": "Missing status or url"}), 400

    status = data.get("status")
    url = data.get("url")

    if status == "entered" and url == TARGET_URL:
        print(f"✅ User ENTERED target page: {url} - Starting face detection")
        start_face_detection()
    elif status == "left" or (status == "entered" and url != TARGET_URL):
        print(f"🚪 User LEFT target page or on wrong URL: {url} - Stopping face detection")
        stop_face_detection()
    else:
        print(f"⚠️ Unknown status: {data}")
        return jsonify({"error": "Invalid status"}), 400
    
    return jsonify({"status": "received"}), 200

@app.route('/trigger-download', methods=['POST'])
def trigger_download():
    try:
        print(f"[{datetime.now()}] Download started...")
        response = requests.get(DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            os.makedirs(EXTRACT_DIR, exist_ok=True)
            zip_ref.extractall(EXTRACT_DIR)
        videos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
        if os.path.exists(videos_path):
            shutil.rmtree(videos_path)
        os.rename(EXTRACT_DIR, videos_path)
        print(f"[{datetime.now()}] Download complete. Extracted to 'videos'")
        return jsonify({"status": "Downloaded and extracted, videos folder replaced"}), 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except zipfile.BadZipFile as e:
        print(f"❌ Corrupt zip file: {e}")
        return jsonify({"error": "Corrupt zip file"}), 500
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
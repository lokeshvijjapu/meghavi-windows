import cv2
import time
import threading
import os
from ultralytics import YOLO
from multiprocessing import Process
import signal
import sys
import webview

# --- Distance calculation constants
A = 9703.20
B = -0.4911842338691967
MODEL_PATH = "models/model.pt"

# Global face distance threshold (cm)
FACE_DISTANCE_THRESHOLD = 110
# Global timer for screensaver activation (seconds)
NO_FACE_TIMER_SECONDS = 5

# --- Screensaver process using pywebview

def run_webview():
    # Point to the root of the Flask server, which now serves the video screensaver page
    webview.create_window(
        'Screensaver',
        'http://localhost:5000/',
        frameless=True,
        fullscreen=True,
        on_top=True
    )
    webview.start()

def face_detection_loop():
    model = YOLO(MODEL_PATH)
    screensaver_proc = None
    no_face_start = None
    frame_count = 0
    last_face_in_range = False
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Unable to access webcam.")
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            frame_count += 1
            # Only run YOLO every 5th frame
            if frame_count % 5 == 0:
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
                            # import subprocess
                            # chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Make sure this path is correct
                            # subprocess.Popen([
                            # chrome_path,
                            # "--kiosk",  # Opens in fullscreen
                            # "--start-fullscreen",
                            # "--new-window",
                            # "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy"
                            # ])
                            break 

                last_face_in_range = face_in_range
            else:
                face_in_range = last_face_in_range
            now = time.time()
            if not face_in_range:
                if no_face_start is None:
                    no_face_start = now
                elif now - no_face_start >= NO_FACE_TIMER_SECONDS:
                    if screensaver_proc is None or not screensaver_proc.is_alive():
                        screensaver_proc = Process(target=run_webview)
                        screensaver_proc.start()
            else:
                no_face_start = None
                if screensaver_proc is not None and screensaver_proc.is_alive():
                    screensaver_proc.terminate()
                    screensaver_proc.join()
                    screensaver_proc = None
            # Sleep a bit to reduce CPU usage
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if screensaver_proc is not None and screensaver_proc.is_alive():
            screensaver_proc.terminate()
            screensaver_proc.join()

def main():
    face_detection_loop()

if __name__ == "__main__":
    main()

import os
import sys
import time
import glob
import cv2
from multiprocessing import Process
from ultralytics import YOLO

# 1) point to your VLC install
vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
os.environ['VLC_PLUGIN_PATH'] = vlc_path

import vlc  # now safe to load 64‑bit VLC

# --- face‑distance calibration
A = 9703.20
B = -0.4911842338691967
MODEL_PATH = "models/model.pt"
FACE_DISTANCE_THRESHOLD = 110       # cm
NO_FACE_TIMER_SECONDS  = 5          # seconds

def run_vlc_screensaver():
    """Play all .mp4 in ./videos full‑screen with sound, looping."""
    video_folder = os.path.join(os.path.dirname(__file__), 'videos')
    files = glob.glob(os.path.join(video_folder, '*.mp4'))
    if not files:
        return

    instance = vlc.Instance(
        "--no-video-title-show",
        "--loop",
        "--fullscreen",
        "--video-on-top",
        "--no-video-deco"
    )

    media_list = instance.media_list_new(files)
    list_player = instance.media_list_player_new()
    list_player.set_media_list(media_list)
    list_player.play()

    # ensure fullscreen
    time.sleep(0.5)
    try:
        mp = list_player.get_media_player()
        mp.set_fullscreen(True)
    except:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        list_player.stop()

def face_detection_loop():
    """Continuously detect faces; spawn/kill VLC as needed."""
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return

    screensaver_proc = None
    no_face_time   = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=0.4, verbose=False)
            boxes   = results[0].boxes
            face_in_range = False

            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area_px = (x2-x1)*(y2-y1)
                    distance = A * (area_px ** B)
                    if distance < FACE_DISTANCE_THRESHOLD:
                        face_in_range = True
                        break

            if face_in_range:
                no_face_time = None
                if screensaver_proc and screensaver_proc.is_alive():
                    screensaver_proc.terminate()
                    screensaver_proc.join()
                    screensaver_proc = None
            else:
                if no_face_time is None:
                    no_face_time = time.time()
                elif time.time() - no_face_time >= NO_FACE_TIMER_SECONDS:
                    if not (screensaver_proc and screensaver_proc.is_alive()):
                        screensaver_proc = Process(target=run_vlc_screensaver)
                        screensaver_proc.start()

            time.sleep(0.1)

    finally:
        cap.release()
        if screensaver_proc and screensaver_proc.is_alive():
            screensaver_proc.terminate()
            screensaver_proc.join()

if __name__ == "__main__":
    face_detection_loop()

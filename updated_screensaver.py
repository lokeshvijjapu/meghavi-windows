import os
import sys
import time
import cv2
from multiprocessing import Process
from ultralytics import YOLO
import tkinter as tk
from tkinter import Button

# VLC setup
vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.environ["PATH"] = vlc_path + os.pathsep + os.environ["PATH"]
os.environ["VLC_PLUGIN_PATH"] = vlc_path
import vlc

# Constants
A = 9703.20
B = -0.4911842338691967
MODEL_PATH = "models/model.pt"
FACE_DISTANCE_THRESHOLD = 110
NO_FACE_TIMER_SECONDS = 5
COOLDOWN_SECONDS = 10
STOP_VLC_FLAG = os.path.join(os.path.dirname(__file__), "stop_vlc.txt")

def run_vlc_loop_all_videos():
    video_folder = os.path.join(os.path.dirname(__file__), "videos")
    video_files = [f for f in os.listdir(video_folder) if f.lower().endswith(".mp4")]
    if not video_files:
        print("⚠️ No .mp4 files found in 'videos' folder.")
        return

    video_paths = [os.path.join(video_folder, f) for f in sorted(video_files)]

    instance = vlc.Instance(
        "--no-video-title-show",
        "--video-on-top",
        "--no-video-deco"
    )

    media_list = instance.media_list_new(video_paths)
    list_player = instance.media_list_player_new()
    list_player.set_media_list(media_list)
    list_player.set_playback_mode(vlc.PlaybackMode.loop)

    # Create Tkinter fullscreen window
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.bind("<Escape>", lambda e: root.quit())

    video_frame = tk.Frame(root, bg='black')
    video_frame.pack(fill=tk.BOTH, expand=True)

    if sys.platform == "win32":
        video_frame_id = video_frame.winfo_id()
        list_player.get_media_player().set_hwnd(video_frame_id)
    elif sys.platform == "linux":
        video_frame_id = video_frame.winfo_id()
        list_player.get_media_player().set_xwindow(video_frame_id)

    # Book button logic with stop flag
    close_button = Button(
        root,
        text="Book your service",
        command=lambda: [
            print("🟡 Book button pressed — writing stop flag"),
            open(STOP_VLC_FLAG, 'w').close(),
            list_player.stop(),
            root.quit()
        ],
        bg="red", fg="white", font=("Arial", 60), width=20, height=1
    )
    screen_height = root.winfo_screenheight()
    screen_width = root.winfo_screenwidth()
    close_button.place(x=screen_width / 2 - 1000, y=screen_height - 150)

    list_player.play()
    root.lift()
    root.focus_force()

    def check_stop_flag():
        if os.path.exists(STOP_VLC_FLAG):
            print("🟥 Detected stop_vlc.txt — closing screensaver")
            list_player.stop()
            root.quit()
        else:
            root.after(1000, check_stop_flag)

    root.after(1000, check_stop_flag)
    root.mainloop()

def face_detection_loop():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("🚫 Could not access webcam.")
        return

    screensaver_proc = None
    no_face_time = None
    cooldown_until = 0  # ⏳ Cooldown timer to prevent restart after manual stop

    try:
        while True:
            # Handle stop flag
            if os.path.exists(STOP_VLC_FLAG):
                print("🟥 STOP flag detected — closing VLC and entering cooldown")
                if screensaver_proc and screensaver_proc.is_alive():
                    screensaver_proc.terminate()
                    screensaver_proc.join()
                    screensaver_proc = None
                os.remove(STOP_VLC_FLAG)
                cooldown_until = time.time() + COOLDOWN_SECONDS

            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=0.4, verbose=False)
            boxes = results[0].boxes
            face_in_range = False

            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)
                    distance = A * (area ** B)
                    if distance < FACE_DISTANCE_THRESHOLD:
                        face_in_range = True
                        break

            if face_in_range:
                no_face_time = None
                if screensaver_proc and screensaver_proc.is_alive():
                    print("🟢 Face detected — stopping screensaver")
                    screensaver_proc.terminate()
                    screensaver_proc.join()
                    screensaver_proc = None
            else:
                if no_face_time is None:
                    no_face_time = time.time()
                elif time.time() - no_face_time >= NO_FACE_TIMER_SECONDS:
                    if time.time() < cooldown_until:
                        print("⏳ In cooldown — not restarting screensaver")
                    elif not (screensaver_proc and screensaver_proc.is_alive()):
                        print("🟡 No face & cooldown passed — launching screensaver")
                        screensaver_proc = Process(target=run_vlc_loop_all_videos)
                        screensaver_proc.start()

            time.sleep(0.1)

    finally:
        cap.release()
        if screensaver_proc and screensaver_proc.is_alive():
            screensaver_proc.terminate()
            screensaver_proc.join()

if __name__ == "__main__":
    face_detection_loop()

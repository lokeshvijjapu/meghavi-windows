import os
import sys
import time
import cv2
from multiprocessing import Process
from ultralytics import YOLO
import tkinter as tk
import ctypes  # for mouse click detection

# VLC setup
vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.environ["PATH"] = vlc_path + os.pathsep + os.environ.get("PATH", "")
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
    root.overrideredirect(True)  # remove window decorations

    # Close on Escape
    root.bind("<Escape>", lambda e: on_click_override(list_player, root))

    # VLC video frame
    video_frame = tk.Frame(root, bg='black')
    video_frame.pack(fill=tk.BOTH, expand=True)

    if sys.platform == "win32":
        video_frame_id = video_frame.winfo_id()
        list_player.get_media_player().set_hwnd(video_frame_id)
    elif sys.platform == "linux":
        video_frame_id = video_frame.winfo_id()
        list_player.get_media_player().set_xwindow(video_frame_id)

    list_player.play()
    root.lift()
    root.focus_force()

    def on_click_override(player, window):
        print("🟡 Click detected — writing stop flag and closing VLC")
        with open(STOP_VLC_FLAG, 'w'):
            pass
        player.stop()
        window.quit()

    # Periodically check for click or external stop flag
    def check_events():
        # External stop flag
        if os.path.exists(STOP_VLC_FLAG):
            print("🟥 Detected stop_vlc.txt — closing screensaver")
            list_player.stop()
            root.quit()
            return
        # Check left mouse button
        if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            on_click_override(list_player, root)
            return
        root.after(100, check_events)

    root.after(100, check_events)
    root.mainloop()


def face_detection_loop():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)
    camera_working = cap.isOpened()
    if not camera_working:
        print("🚫 Could not access webcam. Assuming no human is present.")

    screensaver_proc = None
    no_face_time = None
    cooldown_until = 0

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
                continue

            if camera_working:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Failed to grab frame. Assuming no human is present.")
                    camera_working = False
                    continue

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
            else:
                # Camera not working, assume no human is present
                if no_face_time is None:
                    no_face_time = time.time()
                elif time.time() - no_face_time >= NO_FACE_TIMER_SECONDS:
                    if time.time() < cooldown_until:
                        print("⏳ In cooldown — not restarting screensaver")
                    elif not (screensaver_proc and screensaver_proc.is_alive()):
                        print("🟡 Camera not working & cooldown passed — launching screensaver")
                        screensaver_proc = Process(target=run_vlc_loop_all_videos)
                        screensaver_proc.start()

            time.sleep(0.1)

    finally:
        if camera_working:
            cap.release()
        if screensaver_proc and screensaver_proc.is_alive():
            screensaver_proc.terminate()
            screensaver_proc.join()

if __name__ == "__main__":
    face_detection_loop()

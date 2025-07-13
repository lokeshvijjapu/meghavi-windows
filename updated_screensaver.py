import os
import sys
import time
import cv2
from multiprocessing import Process
from ultralytics import YOLO
import tkinter as tk

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

# ─── RoundedButton class with explicit width/height ─────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, radius=30, padding=20,
                 width=None, height=None, command=None, **kwargs):
        font = kwargs.get("font", ("Arial", 24))

        # Measure text to get a reasonable default size
        tmp = tk.Label(font=font, text=text)
        tmp.update_idletasks()
        text_w = tmp.winfo_width()
        text_h = tmp.winfo_height()
        tmp.destroy()

        # Determine final width/height
        w = width if width is not None else (text_w + padding * 2)
        h = height if height is not None else (text_h + padding)

        super().__init__(parent, width=w, height=h,
                         highlightthickness=0, bg=parent["bg"])
        self.command = command
        self.radius = radius
        self.font = font
        self.kwargs = kwargs
        self.text = text

        # Draw the rounded rectangle and text
        self._draw_rect(w, h)
        self.create_text(w//2, h//2, text=text, font=font,
                         fill=kwargs.get("fg", "black"))
        self.bind("<Button-1>", lambda e: command())

    def _draw_rect(self, w, h):
        r = self.radius
        bg = self.kwargs.get("bg", "skyblue")
        # Four corner arcs
        self.create_arc((0, 0, 2*r, 2*r), start=90, extent=90,
                        style="pieslice", outline="", fill=bg)
        self.create_arc((w-2*r, 0, w, 2*r), start=0, extent=90,
                        style="pieslice", outline="", fill=bg)
        self.create_arc((0, h-2*r, 2*r, h), start=180, extent=90,
                        style="pieslice", outline="", fill=bg)
        self.create_arc((w-2*r, h-2*r, w, h), start=270, extent=90,
                        style="pieslice", outline="", fill=bg)
        # Edge rectangles
        self.create_rectangle((r, 0, w-r, h), outline="", fill=bg)
        self.create_rectangle((0, r, w, h-r), outline="", fill=bg)


# ─── Screensaver launcher ───────────────────────────────────────────────────────
def run_vlc_loop_all_videos():
    video_folder = os.path.join(os.path.dirname(__file__), "videos")
    video_files = [f for f in os.listdir(video_folder) if f.lower().endswith(".mp4")]
    if not video_files:
        print("⚠️ No .mp4 files found in 'videos' folder.")
        return

    video_paths = [os.path.join(video_folder, f) for f in sorted(video_files)]
    instance = vlc.Instance("--no-video-title-show", "--video-on-top", "--no-video-deco")
    media_list = instance.media_list_new(video_paths)
    list_player = instance.media_list_player_new()
    list_player.set_media_list(media_list)
    list_player.set_playback_mode(vlc.PlaybackMode.loop)

    # Tkinter fullscreen window
    root = tk.Tk()
    root.configure(bg="black")
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.bind("<Escape>", lambda e: root.quit())

    video_frame = tk.Frame(root, bg='black')
    video_frame.pack(fill=tk.BOTH, expand=True)

    root.update_idletasks()
    if sys.platform == "win32":
        list_player.get_media_player().set_hwnd(video_frame.winfo_id())
    else:
        list_player.get_media_player().set_xwindow(video_frame.winfo_id())

    # Book button callback
    def on_book():
        print("🟡 Book button pressed — writing stop flag")
        open(STOP_VLC_FLAG, 'w').close()
        list_player.stop()
        root.quit()

    # **Explicitly sized** sky-blue, rounded button
    book_btn = RoundedButton(
        root,
        text="Book your service",
        radius=30,                  # corner roundness
        padding=40,                 # still used if width/height not set
        width=220,                  # explicit width in pixels
        height=90,                 # explicit height in pixels
        font=("Arial", 20),         # text size
        bg="skyblue",
        fg="black",
        command=on_book
    )

    # Place at bottom-right with margin
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    bw, bh = book_btn.winfo_reqwidth(), book_btn.winfo_reqheight()
    margin = 18
    book_btn.place(x=sw - bw - margin, y=sh - bh - margin)

    list_player.play()

    # Stop-flag watcher
    def check_stop_flag():
        if os.path.exists(STOP_VLC_FLAG):
            print("🟥 Detected stop_vlc.txt — closing screensaver")
            list_player.stop()
            root.quit()
        else:
            root.after(1000, check_stop_flag)

    root.after(1000, check_stop_flag)
    root.mainloop()


# ─── Face-detection loop ───────────────────────────────────────────────────────
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
            # STOP flag handler
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
                # Camera down → assume no one
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


# ─── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    face_detection_loop()

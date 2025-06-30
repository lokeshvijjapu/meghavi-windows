import cv2
import time
import threading
import os
import glob
from ultralytics import YOLO
from PIL import Image, ImageTk
import tkinter as tk

# --- Distance calculation constants
A = 9703.20
B = -0.4911842338691967
MODEL_PATH = "models/model.pt"
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')

# Global face distance threshold (cm)
FACE_DISTANCE_THRESHOLD = 110
# Global timer for screensaver activation (seconds)
NO_FACE_TIMER_SECONDS = 5

# --- Screensaver class (from video_screensaver.py, slightly adapted)
class VideoScreensaver:
    def __init__(self, root):
        self.root = root
        # Remove fullscreen attribute, use overrideredirect and geometry instead
        self.root.overrideredirect(True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill='both', expand=True, padx=0, pady=0)
        self.video_files = glob.glob(os.path.join(VIDEO_FOLDER, '*.mp4'))
        if not self.video_files:
            raise RuntimeError("No video files found in videos folder!")
        self.current_video_index = 0
        self.cap = None
        self.running = False
        self.visible = False
        self._after_id = None
        self.fps = 30  # default fallback

    def show(self):
        if not self.visible:
            self.running = True
            self.root.deiconify()
            self.play_next_video()
            self.visible = True

    def hide(self):
        if self.visible:
            self.running = False
            if self.cap is not None:
                self.cap.release()
            if self._after_id is not None:
                try:
                    self.root.after_cancel(self._after_id)
                except Exception:
                    pass
                self._after_id = None
            self.root.withdraw()
            self.visible = False

    def play_next_video(self):
        if not self.running:
            return
        if self.cap is not None:
            self.cap.release()
        video_path = self.video_files[self.current_video_index]
        self.cap = cv2.VideoCapture(video_path)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        if self.fps <= 1 or self.fps > 120:
            self.fps = 30  # fallback for weird/corrupt FPS
        self.canvas.config(width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
        self.update_frame()

    def update_frame(self):
        if not self.running or not self.root.winfo_exists():
            return
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            frame_resized = cv2.resize(frame_rgb, (screen_width, screen_height))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
            x = 0
            y = 0
            self.canvas.delete("all")
            self.canvas.create_image(x, y, image=photo, anchor='nw')
            self.canvas.photo = photo
            delay = int(1000 / self.fps)
            self._after_id = self.root.after(delay, self.update_frame)
        else:
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
            self.play_next_video()

def face_detection_loop(root):
    model = YOLO(MODEL_PATH)
    while True:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Unable to access webcam. Retrying in 5 seconds...")
            time.sleep(5)
            continue
        no_face_start = None
        screensaver = None
        frame_count = 0
        last_face_in_range = False
        try:
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
                                break
                    last_face_in_range = face_in_range
                else:
                    face_in_range = last_face_in_range
                now = time.time()
                # Screensaver logic only, no camera feed window
                if not face_in_range:
                    if no_face_start is None:
                        no_face_start = now
                    elif now - no_face_start >= NO_FACE_TIMER_SECONDS:
                        if screensaver is None:
                            def create_screensaver():
                                nonlocal screensaver
                                screensaver = VideoScreensaver(root)
                                screensaver.show()
                            if root.winfo_exists():
                                root.after(0, create_screensaver)
                else:
                    no_face_start = None
                    if screensaver is not None:
                        def destroy_screensaver():
                            nonlocal screensaver
                            if screensaver is not None:
                                screensaver.hide()
                                # Do not destroy the root window, just hide the screensaver
                                screensaver = None
                        if root.winfo_exists():
                            root.after(0, destroy_screensaver)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        finally:
            cap.release()
            cv2.destroyAllWindows()
            if screensaver is not None:
                if root.winfo_exists():
                    root.after(0, screensaver.hide)
        # Wait a bit before retrying if the loop restarts
        time.sleep(1)

def main():
    while True:
        root = tk.Tk()
        root.withdraw()  # Start hidden
        # Start face detection in a background thread
        t = threading.Thread(target=face_detection_loop, args=(root,), daemon=True)
        t.start()
        root.mainloop()
        # If root.mainloop() exits, restart the loop

if __name__ == "__main__":
    main()


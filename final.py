import cv2
import time
import threading
import os
import glob
import subprocess
from ultralytics import YOLO
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

class VideoScreensaver:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.video_files = glob.glob(os.path.join(VIDEO_FOLDER, '*.mp4'))
        if not self.video_files:
            raise RuntimeError("No video files found in videos folder!")
        self.current_video_index = 0
        self.visible = False
        self.running = False
        self.process = None

    def show(self):
        if not self.visible:
            self.running = True
            self.root.deiconify()
            threading.Thread(target=self._play_loop, daemon=True).start()
            self.visible = True

    def _play_loop(self):
        while self.running:
            video_path = self.video_files[self.current_video_index]
            cmd = ['ffplay', '-fs', '-autoexit', '-nodisp', video_path]
            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )

            self.process.wait()
            if not self.running:
                break
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)

        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None

    def hide(self):
        if self.visible:
            self.running = False
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process = None
            self.root.withdraw()
            self.visible = False

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
        time.sleep(1)

def main():
    while True:
        root = tk.Tk()
        root.withdraw()
        t = threading.Thread(target=face_detection_loop, args=(root,), daemon=True)
        t.start()
        root.mainloop()

if __name__ == "__main__":
    main()

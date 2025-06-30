import sys
import time
import threading
import cv2
import os
from PyQt5 import QtCore, QtWidgets, QtMultimedia, QtMultimediaWidgets, QtWebEngineWidgets

# Configuration
VIDEOS_DIR = r"C:\Users\meghavi\camera\videos"
SPA_URL = "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy"
NO_FACE_TIMEOUT = 5  # seconds without face to switch back to video
FACE_DISTANCE_THRESHOLD_CM = 100  # Threshold for face proximity (estimated)

class FaceDetector(QtCore.QObject):
    face_detected = QtCore.pyqtSignal()
    face_lost = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self._last_face_time = time.time()
        threading.Thread(target=self._run, daemon=True).start()

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        close_faces = []
        for (x, y, w, h) in faces:
            if w >= 200:  # heuristic for distance threshold, adjust as needed
                close_faces.append((x, y, w, h))
        return close_faces

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            boxes = self.detect_faces(frame)
            now = time.time()
            if len(boxes) > 0:
                self._last_face_time = now
                self.face_detected.emit()
            else:
                if now - self._last_face_time > NO_FACE_TIMEOUT:
                    self.face_lost.emit()
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.cap.release()

class KioskApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.showFullScreen()

        self.stack = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.video_widget = QtMultimediaWidgets.QVideoWidget()
        self.player = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)
        self.stack.addWidget(self.video_widget)

        self.web_view = QtWebEngineWidgets.QWebEngineView()
        self.web_view.load(QtCore.QUrl(SPA_URL))
        self.stack.addWidget(self.web_view)

        self.detector = FaceDetector()
        self.detector.face_detected.connect(self.on_face_detected)
        self.detector.face_lost.connect(self.on_face_lost)

        self.play_video()

    def play_video(self):
        files = [f for f in os.listdir(VIDEOS_DIR) if f.lower().endswith(('.mp4','.avi','.mov'))]
        if not files:
            print("No video files found in", VIDEOS_DIR)
            return
        video_path = os.path.join(VIDEOS_DIR, files[0])
        url = QtCore.QUrl.fromLocalFile(video_path)
        self.player.setMedia(QtMultimedia.QMediaContent(url))
        self.player.play()
        self.stack.setCurrentIndex(0)

    def show_website(self):
        self.web_view.load(QtCore.QUrl(SPA_URL))
        self.stack.setCurrentIndex(1)

    @QtCore.pyqtSlot()
    def on_face_detected(self):
        self.show_website()

    @QtCore.pyqtSlot()
    def on_face_lost(self):
        self.play_video()

    def closeEvent(self, event):
        self.detector.stop()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = KioskApp()
    window.show()
    sys.exit(app.exec_())
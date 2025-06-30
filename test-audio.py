from ffpyplayer.player import MediaPlayer
import time

player = MediaPlayer("videos/WhatsApp Video 2025-06-13 at 12.56.30.mp4")  # Use one of your actual .mp4 files
while True:
    frame, val = player.get_frame()
    if val == 'eof':
        break
    time.sleep(0.01)

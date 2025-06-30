from flask import Flask, send_from_directory, render_template_string
import os
import glob

app = Flask(__name__)
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')

@app.route('/')
def index():
    video_files = [os.path.basename(f) for f in glob.glob(os.path.join(VIDEO_FOLDER, '*.mp4'))]
    # HTML/JS to loop through all videos
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screensaver Videos</title>
        <style>body, html { margin:0; padding:0; background:black; height:100%; width:100%; overflow:hidden; }</style>
    </head>
    <body>
        <video id="screensaverVideo" width="100%" height="100%" autoplay playsinline></video>
        <script>
            const videos = {{ videos|safe }};
            let idx = 0;
            const videoElem = document.getElementById('screensaverVideo');
            function playNext() {
                videoElem.src = '/videos/' + videos[idx];
                videoElem.play();
            }
            videoElem.onended = function() {
                idx = (idx + 1) % videos.length;
                playNext();
            };
            if (videos.length > 0) {
                playNext();
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, videos=video_files)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time

app = Flask(__name__)

picam2 = Picamera2()

camera_config = picam2.create_video_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(camera_config)
picam2.start()

time.sleep(2)


def generate_frames():
    while True:
        frame = picam2.capture_array()

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html>
        <body>
            <h1>Raspberry Pi Camera Stream</h1>
            <img src="/video_feed">
        </body>
    </html>
    """


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    print("Local stream:")
    print("http://127.0.0.1:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
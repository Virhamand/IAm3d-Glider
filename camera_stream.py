import threading
import time

import cv2
from flask import Flask, Response
from picamera2 import Picamera2


# -----------------------------
# SETTINGS
# -----------------------------

HOST = "0.0.0.0"
PORT = 5000

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 30

JPEG_QUALITY = 60


# -----------------------------
# FLASK
# -----------------------------

app = Flask(__name__)


# -----------------------------
# CAMERA
# -----------------------------

picam2 = Picamera2()

camera_configuration = picam2.create_video_configuration(
    main={
        "size": (FRAME_WIDTH, FRAME_HEIGHT),
        "format": "RGB888"
    },
    controls={
        "FrameRate": FRAME_RATE
    },
    buffer_count=2
)

picam2.configure(camera_configuration)


# -----------------------------
# SHARED FRAME DATA
# -----------------------------

latest_jpeg = None
frame_number = 0
running = True

frame_condition = threading.Condition()


# -----------------------------
# CAMERA CAPTURE THREAD
# -----------------------------

def capture_frames():
    global latest_jpeg
    global frame_number
    global running

    while running:
        try:
            frame = picam2.capture_array()

            success, encoded_frame = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    JPEG_QUALITY
                ]
            )

            if not success:
                continue

            jpeg_bytes = encoded_frame.tobytes()

            # Replace the previous frame instead of creating a queue.
            with frame_condition:
                latest_jpeg = jpeg_bytes
                frame_number += 1
                frame_condition.notify_all()

        except Exception as error:
            if running:
                print(f"Camera capture error: {error}")
                time.sleep(0.1)


# -----------------------------
# MJPEG GENERATOR
# -----------------------------

def generate_stream():
    previous_frame_number = -1

    while running:
        with frame_condition:
            # Wait until the capture thread produces a newer frame.
            frame_condition.wait_for(
                lambda: (
                    frame_number != previous_frame_number
                    or not running
                ),
                timeout=1
            )

            if not running:
                break

            if latest_jpeg is None:
                continue

            current_jpeg = latest_jpeg
            previous_frame_number = frame_number

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: "
            + str(len(current_jpeg)).encode()
            + b"\r\n"
            b"Cache-Control: no-cache, no-store, must-revalidate\r\n"
            b"Pragma: no-cache\r\n"
            b"Expires: 0\r\n\r\n"
            + current_jpeg
            + b"\r\n"
        )


# -----------------------------
# WEB ROUTES
# -----------------------------

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>IAM3D Camera Stream</title>
        </head>

        <body>
            <h1>IAM3D Raspberry Pi Camera</h1>

            <img
                src="/video_feed"
                width="640"
                height="480"
            >
        </body>
    </html>
    """


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_stream(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
        headers={
            "Cache-Control": (
                "no-cache, no-store, "
                "must-revalidate"
            ),
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no"
        }
    )


# -----------------------------
# MAIN
# -----------------------------

def main():
    global running

    try:
        picam2.start()
        time.sleep(1)

        capture_thread = threading.Thread(
            target=capture_frames,
            daemon=True
        )

        capture_thread.start()

        print("Camera stream started.")
        print(f"Local:   http://127.0.0.1:{PORT}")
        print(
            "Laptop:  "
            f"http://<PI_IP>:{PORT}/video_feed"
        )

        app.run(
            host=HOST,
            port=PORT,
            threaded=True,
            debug=False,
            use_reloader=False
        )

    except KeyboardInterrupt:
        print("\nStopping camera stream...")

    finally:
        running = False

        with frame_condition:
            frame_condition.notify_all()

        picam2.stop()
        picam2.close()

        print("Camera stream stopped.")


if __name__ == "__main__":
    main()
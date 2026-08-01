import cv2
import math
from datetime import datetime
from ultralytics import YOLO
import numpy as np
import requests
import threading
import time


# -----------------------------
# SETTINGS
# -----------------------------

MODEL_PATH = "best10new.pt"
DEFAULT_PI_IP = "192.168.1.101"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

INFERENCE_SCALE = 1
CONFIDENCE_STEP = 0.05
MIN_CONFIDENCE = 0.10
MAX_CONFIDENCE = 0.95

DEFAULT_RECORD_FPS = 30


# -----------------------------
# CAMERA FUNCTIONS
# -----------------------------

class ManualMJPEGStream:
    def __init__(self, url, timeout=10, chunk_size=16384):
        self.url = url
        self.timeout = timeout
        self.chunk_size = chunk_size

        self.response = None
        self.latest_frame = None

        self.frame_lock = threading.Lock()
        self.running = False
        self.opened = False
        self.thread = None

        self._connect()

    def _connect(self):
        try:
            self.response = requests.get(
                self.url,
                stream=True,
                timeout=self.timeout,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
            )

            self.response.raise_for_status()

            self.running = True
            self.opened = True

            self.thread = threading.Thread(
                target=self._receive_frames,
                daemon=True
            )

            self.thread.start()

        except requests.RequestException as error:
            print(f"Stream connection failed: {error}")
            self.release()

    def _receive_frames(self):
        byte_buffer = bytearray()

        try:
            for chunk in self.response.iter_content(
                chunk_size=self.chunk_size
            ):
                if not self.running:
                    break

                if not chunk:
                    continue

                byte_buffer.extend(chunk)

                newest_jpeg = None

                # Extract every complete JPEG currently in the buffer.
                # Keep only the newest one.
                while True:
                    jpg_start = byte_buffer.find(b"\xff\xd8")

                    if jpg_start == -1:
                        byte_buffer.clear()
                        break

                    jpg_end = byte_buffer.find(
                        b"\xff\xd9",
                        jpg_start + 2
                    )

                    if jpg_end == -1:
                        # Remove garbage before the JPEG start,
                        # but keep the incomplete JPEG.
                        if jpg_start > 0:
                            del byte_buffer[:jpg_start]
                        break

                    newest_jpeg = bytes(
                        byte_buffer[jpg_start:jpg_end + 2]
                    )

                    del byte_buffer[:jpg_end + 2]

                if newest_jpeg is None:
                    continue

                encoded_frame = np.frombuffer(
                    newest_jpeg,
                    dtype=np.uint8
                )

                frame = cv2.imdecode(
                    encoded_frame,
                    cv2.IMREAD_COLOR
                )

                if frame is None:
                    continue

                # Overwrite the old frame instead of creating a queue.
                with self.frame_lock:
                    self.latest_frame = frame

        except requests.RequestException as error:
            if self.running:
                print(f"Stream read error: {error}")

        except Exception as error:
            if self.running:
                print(f"Unexpected stream error: {error}")

        finally:
            self.opened = False

    def isOpened(self):
        return self.opened

    def read(self):
        if not self.opened:
            return False, None

        with self.frame_lock:
            frame = self.latest_frame
        
        if frame is None:
            return False, None
        
        return True, frame.copy()

    def get(self, property_id):
        if property_id == cv2.CAP_PROP_FRAME_WIDTH:
            return 640

        if property_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return 480

        if property_id == cv2.CAP_PROP_FPS:
            return 30

        return 0

    def set(self, property_id, value):
        return False

    def release(self):
        self.running = False
        self.opened = False

        if self.response is not None:
            self.response.close()
            self.response = None

        if (
            self.thread is not None
            and self.thread.is_alive()
            and threading.current_thread() is not self.thread
        ):
            self.thread.join(timeout=1)

        self.thread = None
        

def list_cameras(max_cameras=3):
    available_cameras = []

    for index in range(max_cameras):
        cap = cv2.VideoCapture(index)

        if cap.isOpened():
            ret, _ = cap.read()

            if ret:
                available_cameras.append(index)

        cap.release()

    return available_cameras


def open_source():
    print("\nChoose a video source:")
    print("  c - Local camera")
    print("  v - Saved video")
    print("  p - Raspberry Pi stream")

    source_type = input("Choice: ").strip().lower()

    if source_type == "v":
        file_name = input("Video name or path: ").strip()

        if not file_name.lower().endswith(".mp4"):
            file_name += ".mp4"

        source = file_name
        is_saved_video = True
        
        cap = cv2.VideoCapture(source)

    elif source_type == "p":
        pi_ip = input(
            f"Raspberry Pi IP [{DEFAULT_PI_IP}]: "
        ).strip()

        if not pi_ip:
            pi_ip = DEFAULT_PI_IP

        stream_url = f"http://{pi_ip}:5000/video_feed"

        print(f"Connecting to {stream_url}...")

        cap = ManualMJPEGStream(stream_url)
        is_saved_video = False

    elif source_type == "c":
        cameras = list_cameras()

        if not cameras:
            raise RuntimeError("No local cameras were detected")

        print("\nAvailable cameras:")

        for index in cameras:
            print(f"  [{index}]")

        try:
            camera_index = int(input("Choose camera index: "))
        except ValueError as error:
            raise RuntimeError("Camera index must be a number") from error

        if camera_index not in cameras:
            raise RuntimeError(
                f"Camera {camera_index} was not detected"
            )

        source = camera_index
        is_saved_video = False
        
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    else:
        raise RuntimeError(
            "Invalid choice. Enter c, v, or p."
        )

    if not cap.isOpened():
        raise RuntimeError("Could not open source")
    
    return cap, is_saved_video


# -----------------------------
# DRAWING FUNCTIONS
# -----------------------------

def draw_text(
    frame,
    text,
    position,
    font_scale=0.7,
    color=(0, 255, 0),
    thickness=2
):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA
    )


def draw_fps(frame, fps):
    text = f"FPS: {fps:.1f}"

    (text_width, _), _ = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        2
    )

    x = frame.shape[1] - text_width - 10
    y = 25

    draw_text(
        frame,
        text,
        (x, y),
        font_scale=0.7,
        color=(0, 255, 0),
        thickness=2
    )


def draw_detection(frame, box, class_name, confidence):
    x1, y1, x2, y2 = box

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 0, 255),
        3
    )

    label = f"{class_name} {confidence:.2f}"

    (label_width, label_height), baseline = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        2
    )

    label_y = max(y1, label_height + baseline + 5)

    cv2.rectangle(
        frame,
        (x1, label_y - label_height - baseline - 5),
        (x1 + label_width + 8, label_y + 2),
        (255, 0, 255),
        -1
    )

    draw_text(
        frame,
        label,
        (x1 + 4, label_y - baseline),
        font_scale=0.7,
        color=(255, 255, 255),
        thickness=2
    )


# -----------------------------
# YOLO FUNCTION
# -----------------------------

def run_yolo(frame, model, confidence_threshold):
    results = model(
        frame,
        imgsz = 320,
        conf=confidence_threshold,
        verbose=False
    )
    
    result = results[0]
    
    for box in result.boxes:
        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        confidence = float(box.conf[0])
        class_index = int(box.cls[0])
        class_name = model.names[class_index]

        draw_detection(
            frame,
            (x1, y1, x2, y2),
            class_name,
            confidence
        )

    return frame


# -----------------------------
# RECORDING FUNCTIONS
# -----------------------------

def create_video_writer(frame_width, frame_height, fps):
    filename = datetime.now().strftime(
        "video_%Y%m%d_%H%M%S.mp4"
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        filename,
        fourcc,
        fps,
        (frame_width, frame_height)
    )

    if not writer.isOpened():
        raise RuntimeError(
            "Could not create video file"
        )

    return writer, filename


# -----------------------------
# MAIN PROGRAM
# -----------------------------

def main():
    print("Loading YOLO model...")

    model = YOLO(MODEL_PATH)

    print("YOLO model loaded.")

    cap, is_saved_video = open_source()
    
    if not is_saved_video:
        print("Waiting for first frame...")

    start_time = time.time()

    while True:
        ret, frame = cap.read()

        if ret:
            break

        if time.time() - start_time > 10:
            cap.release()
            raise RuntimeError("Timed out waiting for stream frames")

        time.sleep(0.01)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        width = CAMERA_WIDTH
        height = CAMERA_HEIGHT

    source_fps = cap.get(cv2.CAP_PROP_FPS)

    if source_fps <= 0 or source_fps > 240:
        source_fps = DEFAULT_RECORD_FPS

    record_fps = source_fps

    if is_saved_video:
        delay = max(1, int(1000 / source_fps))
    else:
        delay = 1

    confidence_threshold = 0.25

    recording = False
    video_writer = None

    previous_tick = cv2.getTickCount()
    displayed_fps = 0.0

    print("\nControls:")
    print("  . - Increase confidence threshold")
    print("  , - Decrease confidence threshold")
    print("  r - Start or stop recording")
    print("  s - Save screenshot")
    print("  q - Quit")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("End of stream or failed to read frame.")
                break

            current_tick = cv2.getTickCount()
            elapsed = (
                current_tick - previous_tick
            ) / cv2.getTickFrequency()

            previous_tick = current_tick

            if elapsed > 0:
                instantaneous_fps = 1 / elapsed

                displayed_fps = (
                    0.9 * displayed_fps
                    + 0.1 * instantaneous_fps
                )

            frame = run_yolo(
                frame,
                model,
                confidence_threshold
            )

            confidence_text = (
                f"Confidence: {confidence_threshold:.2f}"
            )

            draw_text(
                frame,
                confidence_text,
                (10, 25),
                font_scale=0.7,
                color=(0, 255, 0),
                thickness=2
            )

            draw_fps(frame, displayed_fps)

            if recording and video_writer is not None:
                video_writer.write(frame)

                draw_text(
                    frame,
                    "REC",
                    (10, 60),
                    font_scale=0.8,
                    color=(0, 0, 255),
                    thickness=3
                )

            cv2.imshow("IAM3D Vision", frame)

            key = cv2.waitKey(delay) & 0xFF

            if key == ord("."):
                if confidence_threshold < MAX_CONFIDENCE:
                    confidence_threshold += CONFIDENCE_STEP
                    confidence_threshold = round(
                        confidence_threshold,
                        2
                    )

            elif key == ord(","):
                if confidence_threshold > MIN_CONFIDENCE:
                    confidence_threshold -= CONFIDENCE_STEP
                    confidence_threshold = round(
                        confidence_threshold,
                        2
                    )

            elif key == ord("r"):
                if not recording:
                    video_writer, filename = create_video_writer(
                        width,
                        height,
                        record_fps
                    )

                    recording = True
                    print(f"Recording started: {filename}")

                else:
                    recording = False

                    if video_writer is not None:
                        video_writer.release()
                        video_writer = None

                    print("Recording stopped.")

            elif key == ord("s"):
                filename = datetime.now().strftime(
                    "image_%Y%m%d_%H%M%S.jpg"
                )

                if cv2.imwrite(filename, frame):
                    print(f"Saved screenshot: {filename}")
                else:
                    print("Failed to save screenshot.")

            elif key == ord("q"):
                break

    finally:
        if video_writer is not None:
            video_writer.release()

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
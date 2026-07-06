import cv2
import numpy as np
import math

# -----------------------------
# USER SETTINGS
# -----------------------------

CAMERA_INDEX = 0

# Assumed real target diameter.
# Change this once the real target size is known.
REAL_DIAMETER_M = 0.75

# Approximate camera horizontal field of view in degrees.
# Change this to match your camera.
CAMERA_FOV_DEG = 62.0

# Optional: only detect red-ish circles.
# Set to False to detect any circle-like object.
DETECT_RED_ONLY = False


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def estimate_focal_length_px(frame_width_px, fov_deg):
    """
    Estimate focal length in pixels from camera field of view.

    This is a rough approximation.
    For accurate results, use camera calibration with a checkerboard.
    """
    fov_rad = math.radians(fov_deg)
    return frame_width_px / (2.0 * math.tan(fov_rad / 2.0))


def estimate_distance(real_diameter_m, apparent_diameter_px, focal_length_px):
    """
    Pinhole camera distance estimate:

        distance = real_size * focal_length / image_size

    Works best when the target size is known and the target is not too tilted.
    """
    if apparent_diameter_px <= 0:
        return None

    return (real_diameter_m * focal_length_px) / apparent_diameter_px


def circularity(contour):
    """
    Returns how circle-like a contour is.
    A perfect circle is near 1.0.
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    if perimeter == 0:
        return 0

    return 4 * math.pi * area / (perimeter * perimeter)


def get_red_mask(frame):
    """
    Detect red areas in HSV color space.
    Red wraps around hue=0, so two ranges are needed.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red_1 = np.array([0, 80, 50])
    upper_red_1 = np.array([10, 255, 255])

    lower_red_2 = np.array([170, 80, 50])
    upper_red_2 = np.array([180, 255, 255])

    mask_1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask_2 = cv2.inRange(hsv, lower_red_2, upper_red_2)

    mask = mask_1 | mask_2

    # Clean noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


# -----------------------------
# MAIN PROGRAM
# -----------------------------

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("Could not open camera.")

ret, frame = cap.read()

if not ret:
    raise RuntimeError("Could not read from camera.")

frame_height, frame_width = frame.shape[:2]
FOCAL_LENGTH_PX = estimate_focal_length_px(frame_width, CAMERA_FOV_DEG)

print(f"Estimated focal length: {FOCAL_LENGTH_PX:.2f} px")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    output = frame.copy()

    if DETECT_RED_ONLY:
        processed = get_red_mask(frame)
    else:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 1.5)

        # Edge detection works better for general circle-like targets
        processed = cv2.Canny(gray, 50, 150)

        kernel = np.ones((5, 5), np.uint8)
        processed = cv2.dilate(processed, kernel, iterations=1)

    contours, _ = cv2.findContours(
        processed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    best_candidate = None
    best_score = 0

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < 500:
            continue

        circ = circularity(contour)

        # Need at least 5 points to fit ellipse
        if len(contour) < 5:
            continue

        ellipse = cv2.fitEllipse(contour)
        (cx, cy), (axis_a, axis_b), angle = ellipse

        major_axis = max(axis_a, axis_b)
        minor_axis = min(axis_a, axis_b)

        if major_axis <= 0:
            continue

        ellipse_ratio = minor_axis / major_axis

        # This allows angled circles.
        # A tilted circle appears as an ellipse.
        if ellipse_ratio < 0.25:
            continue

        # Combined score: large, circular/elliptical objects are preferred
        score = area * (0.5 + circ) * ellipse_ratio

        if score > best_score:
            best_score = score
            best_candidate = {
                "contour": contour,
                "ellipse": ellipse,
                "center": (int(cx), int(cy)),
                "major_axis": major_axis,
                "minor_axis": minor_axis,
                "ellipse_ratio": ellipse_ratio,
                "area": area,
                "circularity": circ
            }

    if best_candidate is not None:
        ellipse = best_candidate["ellipse"]
        cx, cy = best_candidate["center"]

        major_axis = best_candidate["major_axis"]
        minor_axis = best_candidate["minor_axis"]

        # For distance, use the major axis.
        # Reason: when a circle tilts, its minor axis shrinks,
        # but the major axis is closer to the original diameter.
        apparent_diameter_px = major_axis

        distance_m = estimate_distance(
            REAL_DIAMETER_M,
            apparent_diameter_px,
            FOCAL_LENGTH_PX
        )

        # Draw detected ellipse
        cv2.ellipse(output, ellipse, (0, 255, 0), 2)
        cv2.circle(output, (cx, cy), 4, (255, 0, 0), -1)

        text_1 = f"Distance: {distance_m:.2f} m"
        text_2 = f"Center: ({cx}, {cy})"
        text_3 = f"Ellipse ratio: {best_candidate['ellipse_ratio']:.2f}"

        cv2.putText(output, text_1, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(output, text_2, (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(output, text_3, (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Circle Detection", output)
    cv2.imshow("Processed View", processed)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
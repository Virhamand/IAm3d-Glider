import cv2
from datetime import datetime

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open camera")

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = 30

recording = False
video_writer = None

print("Controls:")
print("  r - Start/Stop recording")
print("  s - Save screenshot")
print("  q - Quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    if recording:
        video_writer.write(frame)
        cv2.putText(frame, "REC", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255), 3)
        
    cv2.imshow("Camera", frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('r'):
        if not recording:
            filename = datetime.now().strftime("video_%Y%m%d_%H%M%S.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            recording = True
            print(f"Recording started: {filename}")
        else:
            recording = False
            video_writer.release()
            video_writer = None
            print("Recording stopped.")
            
    elif key == ord('s'):
        filename = datetime.now().strftime("image_%Y%m%d_%H%M%S.jpg")
        cv2.imwrite(filename, frame)
        print(f"Saved {filename}")
    
    elif key == ord('q'):
        break
    
if video_writer is not None:
    video_writer.release()
    
cap.release()
cv2.destroyAllWindows()
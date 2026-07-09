import cv2
from ultralytics import YOLO
import math

# model
model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

while True:
    ret, img= cap.read()
    if not ret: break

    results = model(img, stream=True)

    for r in results:
        boxes = r.boxes

        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

            # confidence
            confidence = math.ceil((box.conf[0]*100))/100
            
            # class name
            cls = int(box.cls[0])
            class_name = model.names[cls]

            print("Confidence --->", confidence)
            print("Class name -->", class_name)

            # draw box
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

            # object details
            label = f"{class_name} {confidence}"
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2

            cv2.putText(img, class_name, org, font, fontScale, color, thickness)


    cv2.imshow('Webcam', img)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
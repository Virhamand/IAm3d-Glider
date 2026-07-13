import cv2
from ultralytics import YOLO
import math

# model parameters
CONF_THRESHOLD = 0.25

# model
model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

while True:
    ret, img= cap.read()
    if not ret: break
    
    # Reduce image resolution to ratio of original size
    ratio = 0.5
    resized_img = cv2.resize(img, (0,0), fx=ratio,fy=ratio,interpolation=cv2.INTER_AREA)
    scale = 1 / ratio

    results = model(resized_img, stream=True, conf=CONF_THRESHOLD)

    for r in results:
        boxes = r.boxes

        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale) # convert to int values

            # confidence
            confidence = math.ceil((box.conf[0]*100))/100
            
            # class name
            cls = int(box.cls[0])
            class_name = model.names[cls]

            # print("Confidence --->", confidence)
            # print("Class name -->", class_name)

            # draw box
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

            # object details
            label = f"{class_name} {confidence}"
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2

            # Resized image is used for predictions, but result will be displayed on original image
            cv2.putText(img, label, org, font, fontScale, color, thickness)


    cv2.imshow('Webcam', img)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
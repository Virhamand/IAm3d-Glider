from ultralytics import YOLO
import numpy as np
import cv2

def get_model(): # prepare the model
    model = YOLO('yolov8n.pt')
    model.fuse()
    return model

def plot_bboxes(results):
    img = results[0].orig_img # original image
    names = results[0].names # class names dict
    scores = results[0].boxes.conf.numpy() # probabilities
    classes = results[0].boxes.cls.numpy() # predicted classes
    boxes = results[0].boxes.xyxy.numpy().astype(np.int32) # bboxes
    for score, cls, bbox in zip(scores, classes, boxes): # loop over all bboxes
        class_label = names[cls] # class name
        label = f"{class_label} : {score:0.2f}" # bbox label
        lbl_margin = 3 #label margin
        img = cv2.rectangle(img, (bbox[0], bbox[1]),
                            (bbox[2], bbox[3]),
                            color=(0, 0, 255),
                            thickness=1)
        label_size = cv2.getTextSize(label, # labelsize in pixels 
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
                                     fontScale=1, thickness=1)
        lbl_w, lbl_h = label_size[0] # label w and h
        lbl_w += 2* lbl_margin # add margins on both sides
        lbl_h += 2*lbl_margin
        img = cv2.rectangle(img, (bbox[0], bbox[1]), # plot label background
                             (bbox[0]+lbl_w, bbox[1]-lbl_h),
                             color=(0, 0, 255), 
                             thickness=-1) # thickness=-1 means filled rectangle
        cv2.putText(img, label, (bbox[0]+ lbl_margin, bbox[1]-lbl_margin), # write label to the image
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=1.0, color=(255, 255, 255 ),
                    thickness=1)
    return img

results = get_model()('pool.jpg') # run inference
img = plot_bboxes(results) # plot annotated bboxes
cv2.imshow('img', img) # show annotated image
cv2.waitKey(0) # wait for a keypressed
cv2.destroyAllWindows() # clear windows
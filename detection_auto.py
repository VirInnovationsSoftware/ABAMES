import cv2
import torch

from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO('./best.pt')

# Initialize OpenCV's CSRT tracker
tracker = cv2.TrackerCSRT_create()

# Global variables
is_tracking = False
bbox = None  # Bounding box for tracking
detections = []  # Store detections globally
clicked_point = None  # Store the user clicked point

# Mouse callback function to get user click position
def select_point(event, x, y, flags, param):
    global clicked_point
    if event == cv2.EVENT_LBUTTONUP:
        clicked_point = (x, y)
        print("Saving Point")
    else:
        print(event)

# Function to check if clicked point is inside a bounding box
def check_point_in_bbox(point, detection):
    x1, y1, x2, y2 = map(int, detection.boxes.xyxy[0].cpu().numpy())
    return x1 <= point[0] <= x2 and y1 <= point[1] <= y2

# Function to allow user to click on a detected object
def select_object(frame, detections):
    global clicked_point, bbox, is_tracking
    
    if clicked_point:
        for detection in results:
            if detection.boxes.xyxy.shape[0]:
                if check_point_in_bbox(clicked_point, detection):
                    # If the clicked point is inside a detected bounding box, initialize tracker
                    x1, y1, x2, y2 = map(int, detection.boxes.xyxy[0].cpu().numpy())
                    bbox = (x1, y1, x2 - x1, y2 - y1)
                    tracker.init(frame, bbox)
                    is_tracking = True
                    clicked_point = None  # Reset clicked point after selection
                    return True
            else:
                print("Point not in bbox")
        # If no bounding box matches the clicked point, reject selection
        clicked_point = None
    return False

# Function to update the output screen with detection/tracking info
def update_output(frame, text, bbox=None, color=(0, 0, 255)):
    if bbox:
        x, y, w, h = map(int, bbox)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, f"Tracking: {text}", (frame.shape[1] - 150, frame.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow('Output', frame)

# Access video stream
cap = cv2.VideoCapture(0)  # Change the camera index if needed

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow('Output')
cv2.setMouseCallback('Output', select_point)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if not is_tracking:
        # Run detection using YOLOv8
        results = model(frame, conf=0.5)

        for detection in results:
            if detection.boxes.xyxy.shape[0]:
                x1, y1, x2, y2 = map(int, detection.boxes.xyxy[0].cpu().numpy())
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw green bounding boxes

        if select_object(frame, results):
            is_tracking = True
        else:
            update_output(frame, "NO", color=(0, 255, 0))

    else:
        # Update tracker
        success, bbox = tracker.update(frame)

        if success:
            update_output(frame, "YES", bbox, color=(0, 0, 255))
        else:
            # If tracking fails, reset and switch back to detector
            is_tracking = False
            update_output(frame, "NO", color=(0, 255, 0))

    # Press 'q' to exit
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
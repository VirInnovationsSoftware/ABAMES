import cv2
import serial


cap = cv2.VideoCapture(0)
ser = serial.Serial("/dev/tty", 115200, timeout=0.5)


tracker = cv2.TrackerCSRT_create()

tracking = False
bbox = None

frame_center_y = 0
frame_center_x = 0

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    pan_dir = 0
    tilt_dir = 0
    center_x, center_y = 0, 0

    if tracking and bbox is not None:
        success, bbox = tracker.update(frame)
        if success:
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))

            center_x, center_y = int(bbox[0] + bbox[2] / 2) - frame_center_x, int(bbox[1] + bbox[3] / 2) - frame_center_y

            pan_dir = int(center_x < 0)
            tilt_dir = int(center_y > 0)

            center_x, center_y = (abs(center_x) / 320) * 95000, (abs(center_y) / 240) * 200
            print(f"${pan_dir}, {int(center_x)}, {tilt_dir}, {int(center_y)}, {0}\n")
            ser.write(f"${pan_dir}, {int(center_x)}, {tilt_dir}, {int(center_y)}, {0}\n".encode())

            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
        else:
            ser.write(f"${pan_dir}, {int(center_x)}, {tilt_dir}, {int(center_y)}, {0}\n".encode())
    else:
        ser.write(f"${pan_dir}, {int(center_x)}, {tilt_dir}, {int(center_y)}, {0}\n".encode())

    cv2.imshow('Frame', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('a'):
        h, w = frame.shape[:2]
        frame_center_y = h / 2
        frame_center_x = w / 2
        bbox = (w//2 - 75, h//2 - 75, 150, 150)
        tracker.init(frame, bbox)
        tracking = True

    elif key == ord('b'):
        tracking = False

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
import sys

import time
import cv2

import struct
import serial

# Initialize global variables
refpt = []
tr_log = 0


# Initialize COM Port
try:
    ser = serial.Serial(f'{sys.argv[1]}', 115200, timeout=1)
except serial.SerialException as e:
    print(f"Error: Could not open COM port: {e}")
    sys.exit(1)

# Arduino map function equivalent
def arduino_map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# Load and display the welcome screen, get user input
def display_welcome_screen():
    while(True):
        try:
            path = r'image.jpg'
            wlcm_img = cv2.imread(path, cv2.IMREAD_COLOR)
            cv2.imshow('WELCOME SCREEN', wlcm_img)
        except cv2.error as e:
            print(f"Error loading image: {e}")
            sys.exit(1)

        key = cv2.waitKey(0)
        cv2.destroyWindow("WELCOME SCREEN")
        if key == ord('2'):
            manual_tracker_CSRT_main()
        # if key == ord('3'):
        #     manual_tracker_TLD_main()        
        elif key == 27:  # ESC key
            cv2.destroyAllWindows()
            sys.exit(0)
        else:
            print("Invalid selection. Exiting.")
            sys.exit(1)

# Mouse event handler for manual tracking
def moused_click_handler(event, x, y, flags, params):
    print("mouse click recognized")
    global nx, ny, tr_log, frame, start
    if event == cv2.EVENT_LBUTTONDBLCLK:
        nx, ny = x, y
        cv2.rectangle(frame, (nx - 50, ny - 50), (nx + 50, ny + 50), (0, 0, 200), 3)
        coord = (nx - 50, ny - 50, 100, 100)
        print()
        print(nx,ny)
        refpt.append(coord)
        tr_log = 1
        start = time.time()

# # Initialize PID controllers for pan and tilt
# pid_pan = PID(1, 0.1, 0.05, setpoint=0)
# # pid_tilt = PID(1, 0.1, 0.0, setpoint=0)

# # TLD Tracker function
# def manual_tracker_TLD_main():
#     print("Started TLD Tracker")
#     global tr_log, frame

#     # Create TLD tracker
#     tracker = cv2.legacy_TrackerTLD.create()
#     initBB = None
#     org = (640, 360)
#     fsize = 0.6

#     try:
#         vs = cv2.VideoCapture(f"{sys.argv[2]}")
#         if not vs.isOpened():
#             raise Exception("Failed to open video capture.")
#     except Exception as e:
#         print(f"Error initializing video capture: {e}")
#         sys.exit(1)
    
#     while True:
#         start_time = time.perf_counter()
#         ret, frame = vs.read()
#         frame = cv2.resize(frame, (1280, 720))

#         if not ret:
#             print("Failed to grab frame. Reinitializing video stream.")
#             sys.exit(1)

#         (H, W) = frame.shape[:2]

#         if initBB is not None:
#             success, box = tracker.update(frame)
#             if success:
#                 (x, y, w, h) = [int(v) for v in box]
#                 b = (y + h / 2) - (H / 2)
#                 a = (x + w / 2) - (W / 2)
#                 print("Pixel Error:", (a, b))

#                 # Map PID outputs to Arduino commands
#                 if b < 0:
#                     el = arduino_map(b, -(H / 2), 0, 255, 0)
#                     chara = 0
#                 elif b > 0:
#                     el = arduino_map(b, 0, (H / 2), 0, 255)
#                     chara = 1
#                 else:
#                     el = 0
#                     chara = 0

#                 if a < 0:
#                     az = arduino_map(a, -(W / 2), 0, 255, 0)
#                     char = 1
#                 elif a > 0:
#                     az = arduino_map(a, 0, (W / 2), 0, 255)
#                     char = 0
#                 else:
#                     az = 0
#                     char = 0

#                 az = abs(az)
#                 el = abs(el)

#                 # Send to Arduino (commented for now)
#                 # ser.write(binary_packet)

#                 print(f"Sent: {char, az, chara, el}")

#                 cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

#         # Measure the elapsed time
#         end_time = time.perf_counter()
#         elapsed_time_ms = (end_time - start_time) * 1000
#         print(f"TLD Time elapsed: {elapsed_time_ms:.2f} ms")

#         cv2.putText(frame, "+", org, cv2.FONT_HERSHEY_SIMPLEX, fsize, (0, 0, 255), 2)
#         cv2.imshow("frame", frame)
#         cv2.setMouseCallback('frame', moused_click_handler)

#         if len(refpt) > 0 and tr_log == 1:
#             initBB = refpt[-1]
#             tracker = cv2.legacy_TrackerTLD.create()
#             tracker.init(frame, initBB)
#             tr_log = 0

#         if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
#             break

#     vs.release()
#     cv2.destroyAllWindows()


# Manual Tracking Function
def manual_tracker_CSRT_main():
    print("started manual CSRT Tracker")
    global tr_log, frame

    tracker = cv2.legacy_TrackerCSRT.create()
    initBB = None
    org = (640, 360)
    fsize = 0.6

    try:
        vs = cv2.VideoCapture(0)
        if not vs.isOpened():
            raise Exception("Failed to open video capture.")
    except Exception as e:
        print(f"Error initializing video capture: {e}")
        sys.exit(1)
    i=0

    while True:
        start_time = time.perf_counter()
        ret, frame = vs.read()
        frame = cv2.resize(frame, (1280, 720))

        print(f"Sent No of Times:",i)
        if not ret:
            print("Failed to grab frame. Reinitializing video stream.")
            vs.release()
            vs = cv2.VideoCapture(1)
            continue

        (H, W) = frame.shape[:2]

        if initBB is not None:
            success, box = tracker.update(frame)
            if success:
                (x, y, w, h) = [int(v) for v in box]
                (x, y, w, h) = [int(v) for v in box]
                b = (y + h / 2) - (H / 2)
                a = (x + w / 2) - (W / 2)
                print ("Pixel Error :",(a,b))

                if b < 0:
                    el = arduino_map(b, -(H / 2), 0, 150, 0)
                    chara = 0
                elif b > 0:
                    el = arduino_map(b, 0, (H / 2), 0, 150)
                    chara = 1
                else:
                    el = 0
                    chara = 0

                if a < 0:
                    az = arduino_map(a, -(W / 2), 0, 255, 0)
                    char = 1
                elif a > 0:
                    az = arduino_map(a, 0, (W / 2), 0, 255)
                    char = 0
                else:
                    az = 0
                    char =0

                az = abs(az)
                el = abs(el)

                #print(char, az, chara, el, 0, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                #print(char, az, chara, el, 0, 0)
                format_string = 'BBBBIf'
                #binary_packet = struct.pack(format_string, 0, 0, 0,0, 0, 0)
                binary_packet = struct.pack(format_string, char, az, chara, el, 0, 0)
                print(f"Sent: {char, az, chara, el}")
                ser.write(binary_packet)
                i=i+1
                # sys.exit(0)

        # Measure the elapsed time
        end_time = time.perf_counter()
        elapsed_time_ms = (end_time - start_time) * 1000
        print(f"CSRT Time elapsed: {elapsed_time_ms:.2f} ms")

        cv2.putText(frame, "+", org, cv2.FONT_HERSHEY_SIMPLEX, fsize, (0, 0, 255), 2)
        cv2.imshow("frame", frame)
        cv2.setMouseCallback('frame', moused_click_handler)

        if len(refpt) > 0 and tr_log == 1:
            initBB = refpt[-1]

            tracker = cv2.legacy_TrackerCSRT.create()
            tracker.init(frame, initBB)
            tr_log = 0
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit

            end = time.time()
            print(end - start)
            break

    vs.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    display_welcome_screen()

import numpy as np
import cv2
import sys, socket, struct, time

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent

MODE_UNSELECTED_STYLESHEET = '''
QPushButton{
	background:rgb(50, 50, 50);
	color:white; 
	border:0px;
	border-radius: 8px;
}
QPushButton:hover{
	background:rgb(0, 75, 0);
	color:rgb(180, 180, 180); 
	border:0px;
	border-radius: 8px;
}
QPushButton:pressed{
	background:green;
	color:white; 
	border:0px;
	border-radius: 8px;
}
'''

MODE_SELECTED_STYLESHEET = '''
QPushButton{
	background:green;
	color:white; 
	border:0px;
	border-radius: 8px;
}
'''

class commandClient(QThread):
    def __init__(self, address):
        super().__init__()
        self.host, self.port = address
        self.client = None
        self.running = True

    def run(self):
        while self.running:
            try:
                if not self.client:
                    self.connect_to_server()

                self.msleep(1)  # Prevent busy-waiting

            except (ConnectionResetError, BrokenPipeError):
                print("Disconnected from server, attempting to reconnect...")
                self.client.close()
                self.client = None  # Reset the client for a new connection

    def connect_to_server(self):
        while self.client is None:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((self.host, self.port))
                print("Connected to server.")
            except Exception:
                print("Connection failed, retrying in 5 seconds...")
                self.msleep(5)

    def sendPlatformCommand(self, command):
        if self.client:
            # print(f"Sending command: {command}")
            try:
                self.client.send(command.encode('utf-8'))
            except BrokenPipeError:
                print("Failed to send command, connection may be closed.")

    def close(self):
        self.running = False
        if self.client:
            self.client.close()
        self.quit()  # Exit the thread
        self.wait()  # Wait for the thread to finish
    
class CameraStreamerClient(QThread):
    pixmapSignal = pyqtSignal(QPixmap)
    commandSignal = pyqtSignal(str)
    
    def __init__(self, address, device_id_text):
        super().__init__()
        try:
            self.device_id_text = device_id_text # for degugging
            self.address = address
            self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"[{self.device_id_text}] [Init] Exception: {e}")
            
        self.frame_count = 0
        self.frame_skip = 1

        self.bboxUpdated = False
        self.trackerBox = None
        
        self.isTracking = False
        self.tracker = cv2.legacy_TrackerCSRT.create()
        
        self.defaultFrameCenter = (320, 240)
        self.frameCenter = (320, 240)

    def setFrameCenter(self, center):
        self.frameCenter = center
        
    def enableTracking(self, box):
        self.isTracking = False
        self.msleep(100)
        self.trackBox = box
        self.bboxUpdated = True
                
    def disableTracking(self):
        self.isTracking = False

    def run(self):
        while True:
            try:
                self.sock_fd.sendto(b"data", self.address)
                
                self.sock_fd.settimeout(0.5)

                size, _ = self.sock_fd.recvfrom(4)
                size = struct.unpack("!I", size)[0]
                compressed_frame, _ = self.sock_fd.recvfrom(size)
                frame = cv2.imdecode(np.frombuffer(compressed_frame, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                self.sock_fd.settimeout(None)
                
                if self.bboxUpdated:
                    self.tracker = None
                    self.tracker = cv2.legacy_TrackerCSRT.create()
                    self.tracker.init(frame, self.trackBox)

                    self.bboxUpdated = False
                    self.isTracking = True

                if self.isTracking and self.trackBox is not None:
                    _, self.trackBox = self.tracker.update(frame)
                    if _:
                        center_x, center_y = (int(self.trackBox[0] + self.trackBox[2] / 2) - self.frameCenter[0], int(self.trackBox[1] + self.trackBox[3] / 2) - self.frameCenter[1])
                        x_dir, y_dir = 0, 0
                        if center_x < 0:
                            x_dir = 1
                            center_x /=  self.frameCenter[0]
                        else:
                            x_dir = 0
                            center_x /= 640 - self.frameCenter[0]

                        
                        if center_y < 0:
                            y_dir = 1
                            center_y /=  self.frameCenter[1]
                        else:
                            y_dir = 0
                            center_y /= 480 - self.frameCenter[1]

                        center_x = abs(center_x)
                        center_y = abs(center_y)
                            
                        center_x *= 85000
                        center_y *= 200
                        
                        self.commandSignal.emit(f"${x_dir}, {int(center_x)}, {y_dir}, {int(center_y)}, {0}\n")
                        
                        cv2.rectangle(frame, (int(self.trackBox[0]), int(self.trackBox[1])), (int(self.trackBox[0] + self.trackBox[2]), int(self.trackBox[1] + self.trackBox[3])), (255, 0, 0), 2, 1)

                    else:
                        self.isTracking = False
                
                # Convert OpenCV frame (BGR) to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert OpenCV frame to QImage
                height, width, channels = rgb_frame.shape
                bytes_per_line = channels * width

                # Emit the signal with the QPixmap
                self.pixmapSignal.emit(QPixmap.fromImage(QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)))
                
            except Exception as e:
                print(f"[{self.device_id_text}] [Main Loop] Exception: {e}")
                pass

    def close(self):
        self.sock_fd.close()

class Application(QMainWindow):
    manualMouseBBoxSignal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        uic.loadUi("design.ui", self)
        
        self.camera_client = CameraStreamerClient(("192.168.0.150", 9000), "camera-streamer-client")
        self.command_client = commandClient(("192.168.0.150", 9001))
        
        self.camera_client.pixmapSignal.connect(self.StreamLabel.setPixmap)
        self.manualMouseBBoxSignal.connect(self.camera_client.enableTracking)
        self.camera_client.commandSignal.connect(self.command_client.sendPlatformCommand, type=Qt.ConnectionType.DirectConnection)
        
        self.camera_client.start()
        self.command_client.start()

        self.setBtnInputSlots()
        
        self.changeModeToJoystick()

    def cursorUpPressed(self):
        pass
    
    def cursorDownPressed(self):
        pass
    
    def cursorLeftPressed(self):
        pass
    
    def cursorRightPressed(self):
        pass
    
    def cursorSavePressed(self):
        pass
    
    def changeModeToAuto(self):
        self.MODE = 1
        self.ModeAutoBtn.setStyleSheet(MODE_SELECTED_STYLESHEET)
        
        self.ModeJoystickBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)
        self.ModeManualBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)        

    def changeModeToManual(self):
        self.MODE = 2
        self.ModeManualBtn.setStyleSheet(MODE_SELECTED_STYLESHEET)
        
        self.ModeJoystickBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)
        self.ModeAutoBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)

    def changeModeToJoystick(self):
        self.MODE = 3
        self.ModeJoystickBtn.setStyleSheet(MODE_SELECTED_STYLESHEET)
        
        self.ModeAutoBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)
        self.ModeManualBtn.setStyleSheet(MODE_UNSELECTED_STYLESHEET)
    
    def setBtnInputSlots(self):
        self.CursorUpBtn.clicked.connect(self.cursorUpPressed)
        self.CursorDownBtn.clicked.connect(self.cursorDownPressed)
        self.CursorLeftBtn.clicked.connect(self.cursorLeftPressed)
        self.CursorRightBtn.clicked.connect(self.cursorRightPressed)
        self.CursorSaveBtn.clicked.connect(self.cursorSavePressed)

        self.ModeAutoBtn.clicked.connect(self.changeModeToAuto)
        self.ModeManualBtn.clicked.connect(self.changeModeToManual)
        self.ModeJoystickBtn.clicked.connect(self.changeModeToJoystick)

    def mousePressEvent(self, event: QMouseEvent):
        boxSize = 50
        x = event.position().x()
        y = event.position().y()
        if 640 > x > 0  and 540 > y > 60:
            # make sure mouse click does not go out of bounds
            if x < boxSize: x = boxSize
            elif x > 590: x = 590
            if y < boxSize: y = boxSize
            elif y > 430: y = 430
            
            # adjust mouse position according to pixmap position on window
            y -= boxSize
            
            # emit bbox
            self.manualMouseBBoxSignal.emit([int(x-boxSize), int(y-boxSize), boxSize*2, boxSize*2])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Application()
    window.show()
    sys.exit(app.exec())
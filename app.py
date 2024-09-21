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
    
    def run(self):
        while True:
            self.msleep(1000)
    
    def sendPlatformCommand(self, command):
        # print(command)
        pass
    
    def close(self):
        pass
    
class CameraStreamerClient(QThread):
    pixmapSignal = pyqtSignal(QPixmap)
    commandSignal = pyqtSignal(tuple)
    
    def __init__(self, address, device_id_text):
        super().__init__()
        try:
            self.device_id_text = device_id_text # for degugging
            self.address = address
            self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"[{self.device_id_text}] [Init] Exception: {e}")
            
        self.frame_count = 0
        self.frame_skip = 3

        self.bboxUpdated = False
        self.trackerBox = None
        
        self.isTracking = False
        self.tracker = cv2.TrackerCSRT_create()
        
        self.defaultFrameCenter = (320, 240)
        self.frameCenter = (320, 240)

    def setFrameCenter(self, center):
        self.frameCenter = center
        
    def enableTracking(self, box):
        self.isTracking = False
        self.trackBox = box
        self.bboxUpdated = True
        self.frame_count = 0
                
    def disableTracking(self):
        self.isTracking = False

    def run(self):
        while True:
            try:
                start = time.time()
                self.sock_fd.sendto(b"data", self.address)
                
                self.sock_fd.settimeout(0.5)

                size, _ = self.sock_fd.recvfrom(4)
                size = struct.unpack("!I", size)[0]
                compressed_frame, _ = self.sock_fd.recvfrom(size)
                frame = cv2.imdecode(np.frombuffer(compressed_frame, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                self.sock_fd.settimeout(None)
                
                if self.isTracking and self.trackBox is not None:
                    self.frame_count += 1
                    if self.frame_count % self.frame_skip == 0:
                        print(self.frame_count)
                        _, self.trackBox = self.tracker.update(frame)

                        if _:
                            # x_dir, y_dir = 0, 0
                            # if center_x < 0:
                            #     x_dir = 1
                            #     center_x /=  self.frameCenter[0]
                            # else:
                            #     x_dir = 0
                            #     center_x /= 640 - self.frameCenter[0]
                            
                            # if center_y < 0:
                            #     y_dir = 1
                            #     center_y /=  self.frameCenter[1]
                            # else:
                            #     y_dir = 0
                            #     center_y /= 480 - self.frameCenter[1]
                                
                            # center_x *= 85000
                            # center_y *= 200
                            
                            self.commandSignal.emit((int(self.trackBox[0] + self.trackBox[2] / 2) - self.frameCenter[0], int(self.trackBox[1] + self.trackBox[3] / 2) - self.frameCenter[1]))
                            
                            cv2.rectangle(frame, (int(self.trackBox[0]), int(self.trackBox[1])), (int(self.trackBox[0] + self.trackBox[2]), int(self.trackBox[1] + self.trackBox[3])), (255, 0, 0), 2, 1)

                        else:
                            self.isTracking = False                        
                
                if self.bboxUpdated:
                    self.tracker.init(frame, self.trackBox)
                    self.bboxUpdated = False
                    self.isTracking = True
                
                # Convert OpenCV frame (BGR) to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert OpenCV frame to QImage
                height, width, channels = rgb_frame.shape
                bytes_per_line = channels * width

                # Emit the signal with the QPixmap
                self.pixmapSignal.emit(QPixmap.fromImage(QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)))
                
                end = time.time()
                print(f"processing tracking took: {(end - start) * 1000}ms")
                
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
        
        self.camera_client = CameraStreamerClient(("127.0.0.1", 9000), "camera-streamer-client")
        self.command_client = commandClient(("127.0.0.1", 9000))
        
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
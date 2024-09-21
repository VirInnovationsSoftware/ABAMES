import sys
import socket
import cv2
import struct
import numpy as np

class CameraStreamerClient:
    def __init__(self, address, device_id_text):
        try:
            self.device_id_text = device_id_text # for degugging
            self.address = address
            self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"[{self.device_id_text}] [Init] Exception: {e}")

    def update(self):
        try:
            self.sock_fd.sendto(b"data", self.address)
            
            self.sock_fd.settimeout(0.5)

            size, _ = self.sock_fd.recvfrom(4)
            size = struct.unpack("!I", size)[0]
            compressed_frame, _ = self.sock_fd.recvfrom(size)
            frame = cv2.imdecode(np.frombuffer(compressed_frame, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            self.sock_fd.settimeout(None)

            cv2.imshow("stream", frame)
            cv2.waitKey(1)
        except Exception as e:
            print(f"[{self.device_id_text}] [Main Loop] Exception: {e}")


    def close(self):
        cv2.destroyAllWindows()
        self.sock_fd.close()

if __name__ == "__main__":
    # obj = CameraStreamerClient((sys.argv[1], int(sys.argv[2])), sys.argv[3])
    obj = CameraStreamerClient(("127.0.0.1", 9000), "PYTEST CAM STREAM")
    while True:
        obj.update()
    obj.close()

import socket
import time

class TCPClient:
    def __init__(self, host='192.168.0.150', port=9001, timeout=10):
        self.host = host
        self.port = port
        print(host, port)
        self.timeout = timeout  # Timeout for the client socket
        self.client_socket = None
        self._connect()

    def create_socket(self):
        # Create and configure the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(self.timeout)

    def _connect(self):
        self.create_socket()
        while True:
            try:
                self.client_socket.connect((self.host, self.port))
                print(f"Connected to server at {self.host}:{self.port}")
                break

            except Exception as e:
                print(f"Failed to connect to server: {e}")
                time.sleep(2)  # Retry every 2 seconds

    def _reconnect(self):
        if self.client_socket:
            self.client_socket.close()
        self._connect()

    def send_zoom_preset_command(self, preset):
        try:
            self.client_socket.sendall(f"client@{time.time()} zpreset; {int(preset)}".encode('utf-8'))
            # print(f"{time.time()} @ client zpreset; {int(preset)}".encode('utf-8'))
            return  # Exit the loop if the message is sent successfully

        except socket.timeout:
            print("Socket timeout occurred. Reconnecting...")
            self._reconnect()
        except BrokenPipeError:
            print("BrokenPipeError: Server disconnected abruptly. Reconnecting...")
            self._reconnect()
        except Exception as e:
            print(f"Unexpected error: {e}")

    def close(self):
        if self.client_socket:
            self.client_socket.close()
        print("Connection closed")

# Example usage
if __name__ == "__main__":
    client = TCPClient()  # Adjust host and port if needed
    while True:
        client.send_zoom_preset_command(100)

import socket
import time

class TCPClient:
    def __init__(self, host='127.0.0.1', port=9000, timeout=10):
        self.host = host
        self.port = port
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
            self.client_socket.sendall(f"zpreset; {int(preset)}".encode('utf-8'))
            print(f"Sent message: zpreset; {int(preset)}")
            return  # Exit the loop if the message is sent successfully

        except socket.timeout:
            print("Socket timeout occurred. Reconnecting...")
            self._reconnect()
        except BrokenPipeError:
            print("BrokenPipeError: Server disconnected abruptly. Reconnecting...")
            self._reconnect()
        except Exception as e:
            print(f"Unexpected error: {e}")


    def send_mouse_position(self, position):
        try:
            self.client_socket.sendall(f"mpos; {position[0]}, {position[1]}".encode('utf-8'))
            print(f"Sent message: mpos; {position[0]}, {position[1]}")
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
    client = TCPClient(host='127.0.0.1', port=9000)  # Adjust host and port if needed
    client.send_mouse_position((100, 100))

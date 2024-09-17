import socket
import time

class TCPServer:
    def __init__(self, host='0.0.0.0', port=9000, timeout=1):
        self.host = host
        self.port = port
        self.timeout = timeout  # Timeout for send/recv
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Server can handle up to 5 clients in queue
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            try:
                conn, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                self.handle_client(conn)

            except Exception as e:
                print(f"Error accepting client connection: {e}")
                continue

    def handle_client(self, conn):
        try:
            while True:
                data = conn.recv(1024)
                if not data:  # If client disconnects
                    print("Client disconnected")
                    break

                # Process the received data
                print(f"Received from client: {data.decode('utf-8')}")

        except BrokenPipeError:
            print("BrokenPipeError: Client disconnected abruptly.")
        
        except ConnectionResetError:
            print("ConnectionResetError: Client disconnected abruptly.")
        
        except Exception as e:
            print(f"Unexpected error: {e}")

        finally:
            self.close(conn)

    def close(self, conn):
        conn.close()
        print("Connection closed")

# Example usage
if __name__ == "__main__":
    server = TCPServer(timeout=1)  # Timeout set to 10 seconds for both send and recv
    server.start()

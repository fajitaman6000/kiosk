# video_server.py (add to kiosk side)
from PIL import Image, ImageTk
# video_server.py
import cv2
import socket
import pickle
import struct
import threading

class VideoServer:
    def __init__(self, port=8089):
        self.port = port
        self.running = False
        self.server_socket = None
        self.current_client = None
        
    def check_camera(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                cap.release()
                print("Failed to open camera")
                return False
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                print("Failed to capture frame")
                return False
            print("Camera check successful")
            return True
        except Exception as e:
            print(f"Camera check error: {e}")
            return False

    def start(self):
        if not self.check_camera():
            print("Camera check failed")
            return False
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(1)
            self.running = True
            threading.Thread(target=self.accept_connections, daemon=True).start()
            print("Video server started successfully")
            return True
        except Exception as e:
            print(f"Failed to start video server: {e}")
            return False
        
    def accept_connections(self):
        while self.running:
            try:
                print("Waiting for video connection...")
                client, addr = self.server_socket.accept()
                print(f"Video connection from {addr}")
                if self.current_client:
                    self.current_client.close()
                self.current_client = client
                threading.Thread(target=self.stream_video, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Connection error: {e}")
                break
                
    def stream_video(self, client):
        print("Starting video stream")
        cap = cv2.VideoCapture(0)
        try:
            while self.running and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Resize frame to reduce network load
                    frame = cv2.resize(frame, (640, 480))
                    # Convert to JPEG for better compression
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    data = pickle.dumps(buffer)
                    message = struct.pack("Q", len(data)) + data
                    try:
                        client.sendall(message)
                    except:
                        print("Client disconnected")
                        break
                else:
                    print("Failed to get frame")
                    break
        except Exception as e:
            print(f"Streaming error: {e}")
        finally:
            print("Closing video stream")
            cap.release()
            client.close()
            
    def stop(self):
        print("Stopping video server")
        self.running = False
        if self.current_client:
            self.current_client.close()
        if self.server_socket:
            self.server_socket.close()
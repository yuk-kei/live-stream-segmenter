from time import sleep
import os
import requests
from threading import Thread



class StreamReceiver:
    def __init__(self, url, camera_name, save_time=15):
        self.url = url
        self.save_time = save_time
        self.camera_name = camera_name
        self.save_thread = None
        self.cleanup_thread = None
        self.is_running = False

        # Create camera-specific directory to store segments
        self.camera_folder = os.path.join('../temp_trunks', self.camera_name)
        if not os.path.exists(self.camera_folder):
            os.makedirs(self.camera_folder)

    def _run(self):
        with requests.get(self.url, stream=True) as response:
            frame_data = b''
            for chunk in response.iter_content(chunk_size=8192):
                frame_data += chunk
                if b'\r\n--frame\r\n' in frame_data:
                    parts = frame_data.split(b'---timestamp---')
                    timestamp_bytes = parts[1].split(b'\r\n--frame\r\n')[0]
                    timestamp = timestamp_bytes.decode('utf-8')
                    frame = parts[0].split(b'Content-Type: image/jpeg\r\n\r\n')[1]
                    # Save the frame using timestamp as the filename
                    frame_path = os.path.join(self.camera_folder, f"{timestamp}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame)
                    frame_data = b''

                if not self.is_running:
                    break

    def start(self):
        self.is_running = True
        self.save_thread = Thread(target=self._run)
        self.save_thread.start()

    def stop(self):
        self.is_running = False
        if self.save_thread:
            self.save_thread.join()


# if __name__ == "__main__":
#     STREAM_URL = "http://128.195.169.221:8080/video_feed"
#
#     receiver = StreamReceiver(STREAM_URL, "pi camera1", save_time=15)
#     receiver.start()
#
#     # For demonstration purposes, we'll stop the stream after a short delay.
#
#     sleep(30)
#     receiver.stop()
from threading import Thread
import sys
import requests
import queue
import cv2
import numpy as np
import time
import os


class FrameQueue:
    def __init__(self, save_time=15):
        self.queue_size = save_time * 60 * 30  # Assuming 30fps for 15 minutes
        self.frames = queue.Queue(maxsize=self.queue_size)

    def push(self, frame, timestamp):
        if self.frames.full():
            self.frames.get()
        self.frames.put((frame, timestamp))

    def get_past_n_minutes_frames(self, start_time, cur_time):
        return [f for f in list(self.frames.queue) if start_time <= f[1] <= cur_time]

    def get_next_n_minutes_frames(self, cur_time, end_time):
        return [f for f in list(self.frames.queue) if cur_time <= f[1] <= end_time]


class JpegStreamSegmenter:
    def __init__(self, url, camera_name, retention=15, cam_type="pi"):

        if cam_type == "pi":
            self.url = url + "/video_feed"
        if cam_type == "webcam":
            self.url = url + "/preview_webcam"

        self.camera_name = camera_name
        self.frame_queue = FrameQueue(retention)
        self.is_running = False
        self.save_thread = None

        self.recording = None
        self.start_recorded_time = None
        print("init")
        # Create camera-specific directory to store segments
        self.camera_folder = os.path.join('../videos', self.camera_name)
        if not os.path.exists(self.camera_folder):
            os.makedirs(self.camera_folder)

    def receive_stream(self):
        with requests.get(self.url, stream=True) as response:
            print(self.url)
            buffer = b''
            for chunk in response.iter_content(chunk_size=8192):
                buffer += chunk
                if b'\r\n--frame\r\n' in buffer:
                    parts = buffer.split(b'---timestamp---')
                    timestamp = int(parts[1].split(b'\r\n--frame\r\n')[0].decode('utf-8'))
                    frame = parts[0].split(b'Content-Type: image/jpeg\r\n\r\n')[1]
                    self.frame_queue.push(frame, timestamp)

                    buffer = b''

                if not self.is_running:
                    break

    def save_video(self, frames, save_path, rate=30):
        # firstframe = frames[0][0]
        # height, width, layers = first_frame.shape
        # size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        first_frame = cv2.imdecode(np.frombuffer(frames[0][0], np.uint8), cv2.IMREAD_COLOR)
        height, width, layers = first_frame.shape
        size = (width, height)
        out = cv2.VideoWriter(f"{save_path}.mp4", fourcc, rate, size)  # Assuming frame size of 640x480
        print(len(frames))
        with open(f"{save_path}.txt", 'w') as ts_file:
            for frame_data, timestamp in frames:
                # print(sys.getsizeof(frame_data))
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                out.write(frame)
                ts_file.write(f"{timestamp}\n")
        print(len(frames))
        out.release()

    def save_past(self, start_time, cur_time, dest_folder=None, save_path=None):

        if not save_path:
            if not dest_folder:
                dest_folder = self.camera_folder
            save_path = os.path.join(dest_folder, f"{self.camera_name}_{start_time}_{cur_time}")

        frames = self.frame_queue.get_past_n_minutes_frames(start_time, cur_time)
        self.save_video(frames, save_path)

    def save_next_n_minutes(self, minutes, dest_folder=None, save_path=None, ):
        cur_time = int(time.time() * 1000)
        end_time = cur_time + (minutes * 60 * 1000)
        time.sleep(minutes * 60)
        if not save_path:
            if not dest_folder:
                dest_folder = self.camera_folder
            save_path = os.path.join(dest_folder, f"{self.camera_name}_{cur_time}_{end_time}")
        frames = self.frame_queue.get_next_n_minutes_frames(cur_time, end_time)
        self.save_video(frames, save_path)

    def start_recording(self):
        self.recording = True
        self.start_recorded_time = int(time.time() * 1000)

    def stop_recording(self):
        self.recording = False
        end_time = int(time.time() * 1000)

        self.save_past(self.start_recorded_time, end_time)


    def start(self):
        self.is_running = True
        self.save_thread = Thread(target=self.receive_stream)
        self.save_thread.start()

    def stop(self):
        self.is_running = False
        if self.save_thread:
            self.save_thread.join()

# if __name__ == '__main__':
#     stream = VideoManager("http://128.195.169.221:8080", "pi_camera_6")
#     stream.start()
#     stream.save_next_n_minutes(1)
#     stream.stop()

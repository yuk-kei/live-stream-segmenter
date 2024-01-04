import copy
import threading
from threading import Thread
import sys
import requests
import queue
import cv2
import numpy as np
import time
import os

VIDEO_DIR = "../videos"


class FrameQueue:
    """
    This class provides a queue system for storing frames of a video stream.
    It allows for a fixed number of frames to be stored, removing the oldest
    frame when the limit is reached.
    """

    def __init__(self, save_time=15):
        self.queue_size = save_time * 60 * 30  # Assuming 30fps for 15 minutes
        self.frames = queue.Queue(maxsize=self.queue_size)

    def push(self, frame, timestamp):
        """
        Pushes a frame to the queue. If the queue is full, removes the oldest frame.

        :param frame: The video frame.
        :param timestamp: Timestamp associated with the frame.
        """
        if self.frames.full():
            self.frames.get()
        self.frames.put((frame, timestamp))

    def get_past_n_minutes_frames(self, start_time, cur_time):
        return [copy.deepcopy(f) for f in list(self.frames.queue) if start_time <= f[1] <= cur_time]

    def get_next_n_minutes_frames(self, cur_time, end_time):
        return [f for f in list(self.frames.queue) if cur_time <= f[1] <= end_time]


class JpegStreamSegmenter:
    """
    This class receives a specific JPEG stream with timestamps and segments the video frames.
    The Jpeg Stream contains a timestamp for each frame, which will be extracted and stored along with the frame.
    It allows for saving past or future video frames as a video file and the corresponding timestamps as a text file.
    """

    def __init__(self, url, camera_name, retention=15, cam_type="pi"):
        """
        Initializes the JpegStreamSegmenter with the given parameters.

        :param url: Base URL of the video stream.
        :param camera_name: Unique name for the camera.
        :param retention: Time duration for which frames should be stored, in minutes.
        :param cam_type: Type of camera (either "pi" or "webcam").
        """

        if cam_type == "pi":
            self.url = url + "/video_feed"
        if cam_type == "webcam":
            self.url = url + "/preview_webcam"

        self.camera_name = camera_name
        self.frame_queue = FrameQueue(retention)

        # a flag to indicate whether the stream is running
        self.is_running = False
        # a thread to save the stream
        self.save_thread = None
        # a flag to indicate whether the stream is being recorded
        self.recording = None
        # the start time of the recording
        self.start_recorded_time = None
        print("init")
        # Create camera-specific directory to store segments
        self.camera_folder = os.path.join(VIDEO_DIR, self.camera_name)
        if not os.path.exists(self.camera_folder):
            os.makedirs(self.camera_folder)

    def start_service_for(self):
        """
        Receives the stream, extracts frames and timestamps, and adds them to the frame queue.
        """

        with requests.get(self.url, stream=True) as response:
            print(self.url)
            # buffer to store the stream bytes
            buffer = b''
            # iterate over the stream
            for chunk in response.iter_content(chunk_size=8192):
                # add the chunk to the buffer
                buffer += chunk
                if b'\r\n--frame\r\n' in buffer:
                    # split the buffer into parts
                    parts = buffer.split(b'---timestamp---')
                    # extract the timestamp and frame
                    timestamp = int(parts[1].split(b'\r\n--frame\r\n')[0].decode('utf-8'))
                    # extract the frame
                    frame = parts[0].split(b'Content-Type: image/jpeg\r\n\r\n')[1]
                    # add the frame to the queue
                    self.frame_queue.push(frame, timestamp)
                    # reset the buffer
                    buffer = b''
                # check if the stream is still running
                if not self.is_running:
                    break

    def save_video(self, frames, save_path, rate=30):
        """
        Saves a sequence of frames as a video.

        :param frames: List of frames and associated timestamps.
        :param save_path: Path where the video should be saved.
        :param rate: Frame rate for the output video.
        """

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        # Exact the first frame to get the size
        first_frame = cv2.imdecode(np.frombuffer(frames[0][0], np.uint8), cv2.IMREAD_COLOR)
        height, width, layers = first_frame.shape
        size = (width, height)
        # Create the video writer
        out = cv2.VideoWriter(f"{save_path}.mp4", fourcc, rate, size)  # Assuming frame size of 640x480

        # Save the timestamps
        with open(f"{save_path}.txt", 'w') as ts_file:
            for frame_data, timestamp in frames:
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                out.write(frame)
                ts_file.write(f"{timestamp}\n")
        print(len(frames))
        out.release()

    def save_past(self, start_time, cur_time, dest_folder=None, save_path=None):
        """
        Saves video frames from the past.

        :param start_time: Start timestamp.
        :param cur_time: End timestamp.
        :param dest_folder: (Optional) Destination folder for the video.
        :param save_path: (Optional) Specific name/path for the output video.
        """

        if not save_path:
            if not dest_folder:
                dest_folder = self.camera_folder
            save_path = os.path.join(dest_folder, f"{self.camera_name}_{start_time}_{cur_time}")

        frames = self.frame_queue.get_past_n_minutes_frames(start_time, cur_time)
        threading.Thread(
            target=self.save_video,
            args=(frames, save_path)
        ).start()
        # self.save_video(frames, save_path)

    def save_next_n_minutes(self, minutes, dest_folder=None, save_path=None):
        """
        Saves video frames for the next specified number of minutes.
        Not recommend to use this function as it will block the main thread.

        :param minutes: Number of minutes for which frames should be saved.
        :param dest_folder: (Optional) Destination folder for the video.
        :param save_path: (Optional) Specific name/path for the output video.
        """
        cur_time = int(time.time() * 1000)
        end_time = cur_time + (minutes * 60 * 1000)
        # Wait for the specified number of minutes
        time.sleep(minutes * 60)
        # Save the frames
        if not save_path:
            if not dest_folder:
                dest_folder = self.camera_folder
            save_path = os.path.join(dest_folder, f"{self.camera_name}_{cur_time}_{end_time}")
        frames = self.frame_queue.get_next_n_minutes_frames(cur_time, end_time)
        self.save_video(frames, save_path)

    def start_recording(self):
        """
        Starts the recording process by setting the recording flag and capturing
        the current timestamp as the starting time of recording.
        """
        self.recording = True
        self.start_recorded_time = int(time.time() * 1000)

    def stop_recording(self):
        """
        Stops the recording process and saves the recorded frames from the start time
        up to the current time into a video file.
        """

        self.recording = False
        end_time = int(time.time() * 1000)

        self.save_past(self.start_recorded_time, end_time)

    def start(self):
        """
        Starts the process of receiving and segmenting the JPEG stream.
        Initializes and starts a new thread dedicated to stream processing.
        """
        self.is_running = True
        self.save_thread = Thread(target=self.start_service_for)
        self.save_thread.start()

    def stop(self):
        """
        Stops the process of receiving and segmenting the JPEG stream.
        Also ensures that the associated thread is properly terminated.
        """
        self.is_running = False
        if self.save_thread:
            self.save_thread.join()

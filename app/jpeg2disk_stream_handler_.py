import subprocess
import time

import os
import cv2
import numpy as np
import requests
from threading import Thread

TRUNKS_DIR = '../temp_trunks'
VIDEO_DIR = '../videos'


class StreamReceiver:
    """
    Warning: This class has never been used in the final implementation.
    Might not work as expected.
    """
    def __init__(self, url, camera_name, save_time=15):
        """
        Initializes the StreamReceiver with a stream URL, camera name, and optional save time.

        :param url: Stream URL to fetch data from.
        :param camera_name: Unique name for the camera for storage differentiation.
        :param save_time: Duration for which segments are to be saved (default: 15 minutes).
        """

        self.url = url
        self.save_time = save_time
        self.camera_name = camera_name
        self.save_thread = None
        self.cleanup_thread = None
        self.is_running = False
        self.recording = False
        self.start_recorded_time = None

        # Create camera-specific directory to store segments
        self.frames_dir = os.path.join(TRUNKS_DIR, self.camera_name)
        if not os.path.exists(self.frames_dir):
            os.makedirs(self.frames_dir)

    def _run(self):
        """
        Internal method to continuously fetch JPEG frames from the stream and save them.
        Designed to be run as a separate thread.
        """
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
                    frame_path = os.path.join(self.frames_dir, f"{timestamp}.jpg")
                    with open(frame_path, 'wb') as f:
                        f.write(frame)
                    frame_data = b''

                if not self.is_running:
                    break

    def clean_old_segments(self):
        """
        Cleans old JPEG segments stored on the disk that exceed the `save_time` duration.
        """
        while self.is_running:
            current_time = time.time()
            for filename in os.listdir(self.frames_dir):
                file_path = os.path.join(self.frames_dir, filename)
                file_age = current_time - os.path.getctime(file_path)
                if file_age > self.save_time * 60:  # 15min default
                    os.remove(file_path)
                    print("Removed", file_path)
            # Check for old files every 1 minutes
            time.sleep(60)

    def start(self):
        """
        Starts the service, initializing and commencing both the save and cleanup threads.
        """
        self.is_running = True
        self.save_thread = Thread(target=self._run)
        self.cleanup_thread = Thread(target=self.clean_old_segments)

        self.cleanup_thread.start()
        self.save_thread.start()

    def stop(self):
        """
        Stops the service and all running threads gracefully.
        """
        self.is_running = False
        if self.save_thread:
            self.save_thread.join()
        if self.cleanup_thread:
            self.cleanup_thread.join()

    def save_video_ffmpeg(self, start_time, end_time, dest_folder=None, output_file=None):
        """
        Save segments between start_time and end_time as a single MP4 video using FFmpeg.

        :param start_time: Timestamp indicating the start of the video segment.
        :param end_time: Timestamp indicating the end of the video segment.
        :param dest_folder: Optional folder location for video saving (uses a default if not provided).
        :param output_file: Optional output filename (uses a default naming scheme if not provided).
        :return: Path to the saved video.
        """
        files_to_concatenate = []

        for filename in os.listdir(self.frames_dir):
            filepath = os.path.join(self.frames_dir, filename)

            file_ts_str = filename.split('.')[0]
            file_timestamp = int(file_ts_str)

            if start_time <= file_timestamp <= end_time:
                files_to_concatenate.append(filepath)

        files_to_concatenate.sort()  # Ensure files are in order

        if not files_to_concatenate:
            return ValueError("No files found for the given time range")

        # Output filename format: cameraName_startTime_endTime.mp4
        if not output_file:
            start_str = start_time
            end_str = end_time
            if not dest_folder:
                dest_folder = VIDEO_DIR

            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            output_file = os.path.join(dest_folder, f"{self.camera_name}_{start_str}_{end_str}.mp4")

        # Create a text file listing all the files to concatenate
        list_file_path = 'concat_list.txt'
        with open(list_file_path, 'w') as f:
            for file in files_to_concatenate:
                f.write(f"file '{file}'\n")

        # Using FFmpeg's concat demuxer
        command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file_path,
            '-c', 'copy',
            output_file
        ]
        subprocess.call(command)

        # Delete the concat_list.txt file
        os.remove(list_file_path)

        return output_file

    def start_recording(self):
        """
        Start recording video segments. Marks the start time.
        """
        self.recording = True
        self.start_recorded_time = int(time.time() * 1000)

    def stop_recording(self):
        """
        Stop recording video segments. Combines recorded segments into a single video.
        """
        self.recording = False
        start_time = self.start_recorded_time
        end_time = int(time.time() * 1000)
        # Convert recorded segments to MP4

        self.save_video_ffmpeg(start_time, end_time)

    def save_video_cv2(self, frames, save_path, rate=30):
        """
        Save given frames as a single MP4 video using OpenCV. Also saves associated timestamps to a text file.

        :param frames: List of tuples containing frame data and timestamps.
        :param save_path: Path (without extension) to save the video and timestamps.
        :param rate: Frame rate for the output video (default: 30 fps).
        """
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        first_frame = cv2.imdecode(np.frombuffer(frames[0][0], np.uint8), cv2.IMREAD_COLOR)
        height, width, layers = first_frame.shape
        size = (width, height)
        out = cv2.VideoWriter(f"{save_path}.mp4", fourcc, rate, size)  # Assuming frame size of 640x480
        print(len(frames))
        with open(f"{save_path}.txt", 'w') as ts_file:
            for frame_data, timestamp in frames:
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                out.write(frame)
                ts_file.write(f"{timestamp}\n")
        print(len(frames))
        out.release()

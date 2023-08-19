import os
import subprocess
import time
from datetime import datetime
import threading


class StreamSegmenter:

    def __init__(self, url, camera_name, segment_duration=2, segment_format="mp4"):
        self.url = url
        self.camera_name = camera_name
        self.segment_duration = segment_duration
        self.segment_format = segment_format
        self.proc = None
        self.cleanup_thread = None
        self.running = True
        self.recording = False
        self.start_recorded_time = None

        # Create camera-specific directory to store segments
        self.camera_folder = os.path.join('../temp_trunks', self.camera_name)
        if not os.path.exists(self.camera_folder):
            os.makedirs(self.camera_folder)

    def start(self):
        cmd = [
            'ffmpeg',
            '-i', self.url,
            '-c', 'copy',
            '-copyts',  # Copy timestamps
            '-bufsize', '64k',  # Increase buffer size, adjust as needed
            '-f', 'segment',
            '-segment_time', str(self.segment_duration),
            '-reset_timestamps', '1',
            '-strftime', '1',
            os.path.join(self.camera_folder, 'stream-%Y-%m-%d_%H-%M-%S.' + self.segment_format)
        ]
        self.proc = subprocess.Popen(cmd)
        print("start pushing")
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self.clean_old_segments)
        self.cleanup_thread.start()

    def stop(self):
        self.running = False  # Signal to the cleanup thread to stop

        if not self.proc:
            print("Process not started!")
            return

        # Terminate the subprocess
        self.proc.terminate()

        # Wait for the process to terminate
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it's not terminating, kill it
            self.proc.kill()

        # Join the cleanup thread
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join()


    def clean_old_segments(self):
        while self.running:
            current_time = time.time()
            for filename in os.listdir(self.camera_folder):
                file_path = os.path.join(self.camera_folder, filename)
                file_age = current_time - os.path.getctime(file_path)
                if file_age > 1 * 60 * 60:  # 1 hour in seconds
                    os.remove(file_path)
                    print("Removed", file_path)
            # Check for old files every 10 minutes
            time.sleep(10 * 60)

    def reconstruct_files(self, start_time, end_time, dest_folder=None, output_file=None):
        files_to_concatenate = []

        for filename in os.listdir(self.camera_folder):
            filepath = os.path.join(self.camera_folder, filename)

            # Extract timestamp from filename format: stream-%Y-%m-%d_%H-%M-%S.ts
            file_datetime_str = filename.split('.')[0].split('stream-')[-1]
            file_datetime = datetime.strptime(file_datetime_str, "%Y-%m-%d_%H-%M-%S")
            file_timestamp = int(file_datetime.timestamp())

            if start_time <= file_timestamp <= end_time:
                files_to_concatenate.append(filepath)

        files_to_concatenate.sort()  # Ensure files are in order

        if not files_to_concatenate:
            return ValueError("No files found for the given time range")


        # Output filename format: cameraName_startTime_endTime.mp4
        if not output_file:
            start_str = datetime.fromtimestamp(start_time).strftime("%Y%m%d%H%M%S")
            end_str = datetime.fromtimestamp(end_time).strftime("%Y%m%d%H%M%S")
            if not dest_folder:
                dest_folder = "../videos"

            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            output_file = os.path.join(dest_folder, f"{self.camera_name}_{start_str}_{end_str}.{self.segment_format}")

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

    # ... (rest of the class remains unchanged)

    def start_recording(self):
        self.recording = True
        self.start_recorded_time = int(time.time())

    def stop_recording(self):
        self.recording = False
        start_time = self.start_recorded_time
        end_time = int(time.time())
        # Convert recorded segments to MP4

        self.reconstruct_files(start_time, end_time)

    def __del__(self):
        self.stop()

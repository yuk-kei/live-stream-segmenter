import os
import subprocess
import time
from datetime import datetime
import threading

TRUNKS_DIR = '../temp_trunks'
VIDEO_DIR = '../videos'


class StreamSegmenter:
    """
    This class handles segmenting of video streams using ffmpeg.
    It can start and stop the segmenting process, clean up old segments,
    and reconstruct a video from the segments.
    """

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
        self.segments_dir = os.path.join(TRUNKS_DIR, self.camera_name)
        if not os.path.exists(self.segments_dir):
            os.makedirs(self.segments_dir)

    def start(self):
        """
        Starts segmenting the video stream.
        """
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
            os.path.join(self.segments_dir, 'stream-%Y-%m-%d_%H-%M-%S.' + self.segment_format)
        ]
        self.proc = subprocess.Popen(cmd)
        print("start pushing")
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self.clean_old_segments)
        self.cleanup_thread.start()

    def stop(self):
        """
        Stops the segmenting process and any associated threads.
        """
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
        """
        Periodically checks and removes segments that are older than 1 hour.
        Runs in a separate thread.
        """
        while self.running:
            current_time = time.time()
            for filename in os.listdir(self.segments_dir):
                file_path = os.path.join(self.segments_dir, filename)
                file_age = current_time - os.path.getctime(file_path)
                if file_age > 1 * 60 * 60:  # 1 hour in seconds
                    os.remove(file_path)
                    print("Removed", file_path)
            # Check for old files every 10 minutes
            time.sleep(10 * 60)

    def reconstruct_files(self, start_time, end_time, dest_folder=None, output_file=None):
        """
        Reconstructs a video from segments for the given time range.

        :param start_time: Start timestamp.
        :param end_time: End timestamp.
        :param dest_folder: (Optional) Destination folder for the output file.
        :param output_file: (Optional) Specific name for the output file.

        :return: Path to the reconstructed video.
        """
        files_to_concatenate = []

        for filename in os.listdir(self.segments_dir):
            filepath = os.path.join(self.segments_dir, filename)

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
                dest_folder = VIDEO_DIR

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
        """
        Flags the start recording videos in future.
        """
        self.recording = True
        self.start_recorded_time = int(time.time())

    def stop_recording(self):
        """
        Flags the end of a recording session and triggers the reconstruction of
        the recorded video segments.
        """
        self.recording = False
        start_time = self.start_recorded_time
        end_time = int(time.time())
        # Convert recorded segments to MP4

        self.reconstruct_files(start_time, end_time)

    def __del__(self):
        """
        Destructor for the class. Ensures segmenting process and threads are stopped.
        """
        self.stop()

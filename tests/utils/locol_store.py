import subprocess
import time
import os

RTMP_URL = "rtmp://128.195.151.170:1935/live"
RTSP_URL = "rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main"
SEGMENT_DURATION = 1  # 1 second
OUTPUT_FOLDER = "temp_trunks"

# Ensure the directory exists or create it
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def segment_stream():
    output_file_pattern = os.path.join(OUTPUT_FOLDER, "stream-%Y-%m-%d_%H-%M-%S.mp4")

    command = [
        'ffmpeg',
        '-i', RTSP_URL,
        '-c', 'copy',
        '-map', '0',
        '-f', 'segment',
        '-segment_time', str(SEGMENT_DURATION),
        '-segment_format', 'mp4',
        '-reset_timestamps', '1',
        '-strftime', '1',
        output_file_pattern
    ]

    subprocess.call(command)


if __name__ == '__main__':
    segment_stream()
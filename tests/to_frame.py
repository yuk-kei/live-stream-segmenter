import subprocess
import redis
import time
import os

RTSP_URL = "rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main"
BUFFER_TIME = 2 * 60 * 60  # 2 hours in seconds
REDIS_HOST = '128.195.151.182'
REDIS_PORT = 6379
REDIS_DB = 0
FRAME_DIR = "frames"  # Directory to save frames

# Set up Redis connection
r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def extract_frames_and_internal_timestamps():
    os.makedirs(FRAME_DIR, exist_ok=True)

    ffmpeg_command = [
        'ffmpeg',
        '-i', RTSP_URL,
        '-vf', 'showinfo',  # This will output frame details including pts_time (internal timestamp)
        f'{FRAME_DIR}/frame_%09d.jpg'
    ]

    with subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, universal_newlines=True) as process:
        frame_count = 0
        for line in process.stderr:
            if "showinfo" in line and 'pts_time:' in line:
                frame_count += 1
                pts_time = line.split('pts_time:')[1].split(' ')[0]  # Extract internal timestamp
                print(pts_time)
                frame_filename = f"frame_{frame_count:09d}.jpg"

                # Store frame filename with its internal timestamp
                r.hset('frames', frame_filename, pts_time)


def reconstruct_frames_to_mp4(start_timestamp, end_timestamp):
    # Filter frames based on the provided timestamp range
    relevant_frames = [
        key.decode() for key, ts in r.hgetall('frames').items()
        if start_timestamp <= float(ts.decode()) <= end_timestamp
    ]

    if not relevant_frames:
        print("No frames found for the provided timestamp range.")
        return

    # Create a list file for FFmpeg
    with open("framelist.txt", "w") as f:
        for frame in relevant_frames:
            f.write(f"file '{FRAME_DIR}/{frame}'\n")

    output_file = f"output_{start_timestamp}_{end_timestamp}.mp4"
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'framelist.txt',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-r', '24',
        output_file
    ]

    subprocess.run(ffmpeg_command)


if __name__ == "__main__":
    # For demonstration, run the extractor for a while, then get the past 30 minutes
    extract_frames_and_internal_timestamps()

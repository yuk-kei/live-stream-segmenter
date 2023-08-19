import os
import subprocess
import redis
import time
# Constants
RTSP_URL = 'rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main'
FFMPEG_PATH = "ffmpeg"
SEGMENT_DURATION = 1  # 1 second
REDIS_HOST = '128.195.151.182'
REDIS_PORT = 6379
BUFFER_SIZE = 60 * 60  # 1 hour in seconds
REDIS_LIST_KEY = "video_buffer"
SEGMENT_PREFIX = "temp_segment"



redis_host = "128.195.151.182"
redis_port = 6379
redis_password = ""

def cut_stream():
    r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
    pipe = r.pipeline()
    pipe.multi()
    pipe.delete("stream")
    pipe.execute()
    cmd = "ffmpeg -i rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main -c copy -map 0 -f segment -segment_time 1 -segment_format mp4 -reset_timestamps 1 -strftime 1 /tmp/stream-%Y-%m-%d_%H-%M-%S.mp4"
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    while True:
        line = p.stdout.readline()
        if not line:
            break
        print(line)
        pipe.rpush("stream", line)
        pipe.execute()
        if r.llen("stream") > 3600:
            r.lpop("stream")
        time.sleep(0.01)


if __name__ == '__main__':
    cut_stream()


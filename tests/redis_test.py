import redis
import subprocess
import time
import os

redis_host = "localhost"
redis_port = 6379
redis_password = ""

def get_past_segments(start_time, end_time):
    r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
    pipe = r.pipeline()
    pipe.multi()
    pipe.delete("output.mp4")
    pipe.execute()
    print("start_time: " + str(start_time) + " end_time: " + str(end_time))
    for i in range(start_time, end_time):
        print("done " + str(i))
        segment_name = "/tmp/segment-" + str(i) + ".mp4"
        if not os.path.exists(segment_name):
            continue
        cmd = "ffmpeg -i " + segment_name + " -c copy -map 0 -f mp4 -reset_timestamps 1 -strftime 1 /tmp/output-%Y-%m-%d_%H-%M-%S.mp4"
        subprocess.call(cmd.split())
        pipe.rpush("output.mp4",
                   "/tmp/output-" + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time() - i)) + ".mp4")
        pipe.execute()



if __name__ == '__main__':
    get_past_segments(60, 10)

import subprocess
import time

from flask import Flask, request, send_file
import ffmpeg
from confluent_kafka import Consumer, Producer
import os

app = Flask(__name__)

KAFKA_TOPIC = "rtsp_buffer"
KAFKA_SERVER = "128.195.151.182:9392"
CONSUMER_GROUP = "video_retrieval_group"

consumer_conf = {
    'bootstrap.servers': KAFKA_SERVER,
    'group.id': CONSUMER_GROUP,
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])


@app.route('/video', methods=['GET'])
def get_video(duration=5):
    # duration = request.args.get('duration', default=5, type=int)
    segments = retrieve_from_kafka(duration)

    output_file = f'video_{duration}_mins.mp4'
    construct_video(segments, output_file)

    return "Stored video in current directory"
    # return send_file(output_file, as_attachment=True)


def retrieve_from_kafka(minutes):
    # Assuming each segment's timestamp is the key in Kafka, stored as a float (seconds since epoch)
    current_time = time.time()
    start_time = current_time - (minutes * 60)

    segments = []

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            break
        if msg.error():
            print(f"Consumer error: {msg.error()}")
        else:
            timestamp = float(msg.key().decode('utf-8'))
            if timestamp >= start_time:
                segments.append(msg.value())

    return segments


def construct_video(segments, output_file):
    command = ['ffmpeg', '-f', 'mpegts', '-i', 'pipe:', output_file]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for segment in segments:
        process.stdin.write(segment)

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(stderr.decode())
        raise Exception("FFmpeg failed")


if __name__ == '__main__':
    get_video(1)
    # app.run(host='0.0.0.0', port=5000)

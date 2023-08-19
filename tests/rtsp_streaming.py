import subprocess
from confluent_kafka import Producer
import re

RTSP_URL = "rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main"
FFMPEG_PATH = "ffmpeg"
KAFKA_TOPIC = "rtsp_buffer"
KAFKA_SERVER = "128.195.151.182:9392"
CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB
# Note: -show_packets extracts packet information which contains PTS (presentation timestamp).
FFMPEG_CMD = [
    FFMPEG_PATH,
    '-i', RTSP_URL,
    '-c', 'copy',
    '-f', 'mpegts',
    '-y',
    '-an',
    '-loglevel', 'info',
    '-show_packets',
    'pipe:1'
]

conf = {
    'bootstrap.servers': KAFKA_SERVER
}

producer = Producer(conf)


def delivery_report(err, msg):
    """Called once for each message produced to indicate delivery result."""
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def extract_timestamp_from_ffmpeg_output(line):
    # This regex captures PTS from ffmpeg packet info
    pts_pattern = re.compile(r'pts:(\d+)')
    match = pts_pattern.search(line)
    if match:
        return match.group(1)
    return None


def start_kafka_producer():
    process = subprocess.Popen(FFMPEG_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    current_timestamp = None

    for line in process.stderr:  # Read ffmpeg's stderr line by line
        timestamp = extract_timestamp_from_ffmpeg_output(line)

        if timestamp:
            current_timestamp = timestamp

        # If we find a line that starts with a packet (indicating data), we read that data and send it to Kafka
        if line.startswith('[PACKET]'):
            ts_chunk = process.stdout.read(4096)
            if not ts_chunk:
                break

            if current_timestamp:
                producer.produce(KAFKA_TOPIC, key=current_timestamp, value=ts_chunk, callback=delivery_report)
                producer.poll(0)

    producer.flush()


if __name__ == '__main__':
    start_kafka_producer()

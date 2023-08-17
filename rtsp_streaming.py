import ffmpeg
import numpy as np
from confluent_kafka import Producer

# Configuration
RTSP_URL = "rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main"
KAFKA_TOPIC = "rtsp_buffer"
KAFKA_SERVER = "128.195.151.182:9392"
CHUNK_SIZE = 4096

# Kafka configuration
conf = {
    'bootstrap.servers': KAFKA_SERVER
}

producer = Producer(conf)


def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


def start_kafka_producer():
    print("in use")
    # Step 1: Use ffmpeg-python to capture RTSP stream
    process = (
        ffmpeg
        .input(RTSP_URL)
        .output('pipe:', format='mpegts')
        .run(capture_stdout=True, capture_stderr=True)
    )
    # Split the stream into chunks and send each to Kafka
    for i in range(0, len(process[0]), CHUNK_SIZE):
        print("here")
        chunk = process[0][i:i + CHUNK_SIZE]

        # Using numpy to find the timestamp in the MPEG-TS packet header
        # Note: This is a basic way of extracting the timestamp, and may need further refinement
        print("here")
        arr = np.frombuffer(chunk, dtype=np.uint8)
        print("there")
        pts_index = np.where(arr == 71)[0][1]  # Find the second occurrence of 0x47 (MPEG-TS sync byte)
        print("everywhere")
        timestamp = int.from_bytes(chunk[pts_index + 4:pts_index + 8], "big")
        print("somewhere")
        # Step 4: Publish each chunk as a message to a Kafka topic
        producer.produce(KAFKA_TOPIC, key=str(timestamp), value=chunk, callback=delivery_report)
        print("goes here")
        producer.poll(0)

    producer.flush()


if __name__ == '__main__':
    start_kafka_producer()

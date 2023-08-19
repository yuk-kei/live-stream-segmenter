import time

from app.stream_handler import StreamSegmenter

RTMP_URL = "rtmp://128.195.151.170:1935/live"
RTSP_URL = "rtsp://admin:Calit2@128.195.151.231:554/h264Preview_01_main"


def test_start(segmenter):
    segmenter.start()
    time.sleep(60)
    segmenter.stop()


def test_reconstruct(segmenter: StreamSegmenter, past_start, past_stop=0):
    # segmenter.start()

    current_timestamp = int(time.time())
    output_file = segmenter.reconstruct_files(current_timestamp - past_start, current_timestamp - past_stop)
    print(f"Reconstructed file saved as {output_file}")
    segmenter.stop()


def test_recording(segmenter: StreamSegmenter):
    segmenter.start()
    time.sleep(100)
    segmenter.start_recording()
    time.sleep(60)
    segmenter.stop_recording()
    segmenter.stop()


if __name__ == '__main__':
    test_segment = StreamSegmenter(RTSP_URL, "camera_1")
    # test_segment
    test_recording(test_segment)
    # test_recording(test_segment)
# Using numpy to find the timestamp in the MPEG-TS packet header
# Note: This is a basic way of extracting the timestamp, and may need further refinement
# arr = np.frombuffer(chunk, dtype=np.uint8)
# pts_index = np.where(arr == 71)[0][1]  # Find the second occurrence of 0x47 (MPEG-TS sync byte)
# timestamp = int.from_bytes(chunk[pts_index + 4:pts_index + 8], "big")
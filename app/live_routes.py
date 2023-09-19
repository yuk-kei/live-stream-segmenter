import time

from flask import Blueprint, request, jsonify
from .stream_handler import StreamSegmenter

video_blueprint = Blueprint('video', __name__, url_prefix="/api/v1/video_stream")

stream_sources = {}


@video_blueprint.route('/test', methods=['POST'])
def test():
    """
    Endpoint to test the service is online or not.

    @return: JSON response containing a test message.
    @return_code: 200 if successful, 400 if request is not JSON.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400
    test_message = request.get_json()
    message = test_message['test_message']
    print(message)
    return jsonify({'message': 'test'}), 200


@video_blueprint.route('/start_service', methods=['POST'])
def start_service_for():
    """
    Starts the video streaming service for a given source, the source could be rtsp, rtmp, hls or other type of stream.

    @param: JSON body should include 'source_name', 'stream_url' and optionally 'segment_time'.
    @return: JSON response indicating the status of the operation.
    @return_code:
        - 200 if source is started successfully.
        - 400 if request is missing required parameters or the source is already started.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.get_json()

    if 'source_name' not in data:
        return jsonify({'message': 'source not found'}), 400

    if 'stream_url' not in data:
        return jsonify({'message': 'stream_url not found'}), 400

    segment_time = 2
    if data['segment_time']:
        segment_time = data['segment_time']
    source_name = data['source_name']
    stream_url = data['stream_url']

    if source_name in stream_sources:
        return jsonify({'message': 'camera already started'}), 400

    stream_sources[source_name] = StreamSegmenter(url=stream_url, camera_name=source_name, segment_duration=segment_time)
    stream_sources[source_name].start()

    return jsonify({'message': 'source started'}), 200


@video_blueprint.route('/stop_service_for/<string:source_name>', methods=['GET'])
def stop_service_for(source_name):
    """
    Stops the video streaming service for a given source.

    @param source_name: The name of the source to stop.
    @return: JSON response indicating the status of the operation.
    @return_code:
      - 200 if source is stopped successfully.
      - 404 if the specified source is not found.
    """
    if source_name not in stream_sources:
        return jsonify({'message': 'source not found'}), 404

    stream_sources[source_name].stop()
    del stream_sources[source_name]
    return jsonify({'message': 'source stopped'}), 200


@video_blueprint.route('/store_past', methods=['POST'])
def store_past_video():
    """
    Stores a past segment of the video stream.

    @param: JSON body should include 'source_name', 'start_time' and optionally 'end_time'.
    @return: JSON response indicating the status of the operation.
    @return_code:
      - 200 if successful.
      - 400 if request is missing required parameters.
      - 404 if the specified source is not found.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.get_json()
    end_time = 0

    if 'source_name' not in data:
        return jsonify({'message': 'source not found'}), 400

    if 'start_time' not in data:
        return jsonify({'message': 'start_time not found'}), 400

    if 'end_time' in data:
        end_time = data['end_time']

    source_name = data['source_name']
    current_timestamp = int(time.time())

    start_time = current_timestamp - data['start_time']
    end_time = current_timestamp - end_time

    if source_name not in stream_sources:
        return jsonify({'message': 'camera not found'}), 404

    message = stream_sources[source_name].reconstruct_files(start_time=start_time, end_time=end_time)

    return jsonify({'message': message}), 200


@video_blueprint.route('/start_recording', methods=['POST'])
def start_recording():
    """
    Starts recording for a specific video source.

    @param: JSON body should include 'source_name'.
    @return: JSON response indicating the status of the operation.
    @return_code:
      - 200 if recording is started successfully.
      - 400 if request is missing required parameters or the source is already recording.
      - 404 if the specified source is not found.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.get_json()

    if 'source_name' not in data:
        return jsonify({'message': 'camera_id not found'}), 400

    source_name = data['source_name']

    if source_name not in stream_sources:
        return jsonify({'message': 'camera not found'}), 404

    source = stream_sources[source_name]

    if source.recording:
        return jsonify({'message': 'camera already recording'}), 400

    message = source.start_recording()

    return jsonify({'message': message}), 200


@video_blueprint.route('/stop_recording', methods=['POST'])
def stop_recording():
    """
    Stops recording for a specific video source.

    @param: JSON body should include 'source_name'.
    @return: JSON response indicating the status of the operation.
    @return_code:
        - 200 if recording is stopped successfully.
        - 400 if request is missing required parameters.
        - 404 if the specified source is not found.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.get_json()

    if 'source_name' not in data:
        return jsonify({'message': 'source not found'}), 400

    source_name = data['source_name']

    if source_name not in stream_sources:
        return jsonify({'message': 'source not found'}), 404

    message = stream_sources[source_name].stop_recording()

    return jsonify({'message': message}), 200










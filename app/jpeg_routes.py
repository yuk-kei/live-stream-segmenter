import time

from flask import Blueprint, request, jsonify
from app.jpeg2mem_stream_handler import JpegStreamSegmenter

jpeg_blueprint = Blueprint('jpeg', __name__, url_prefix="/api/v1/web_stream")

stream_sources = {}


@jpeg_blueprint.route('/start_service', methods=['POST'])
def start_service():
    """
    Start receiving streams for a given camera.
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.json
    camera_name = data.get('camera_name')
    stream_url = data.get('stream_url')
    retention = data.get('retention', 15)
    cam_type = data.get('cam_type', 'pi')

    # Validate required parameters
    if 'stream_url' not in data:
        return jsonify({'message': 'stream_url not found'}), 400
    if not camera_name:
        return jsonify(error="Camera name not provided"), 400

    if camera_name not in stream_sources:
        stream_sources[camera_name] = JpegStreamSegmenter(url=stream_url, camera_name=camera_name, retention=retention,
                                                          cam_type=cam_type)
    stream_sources[camera_name].start()
    return jsonify(status=f"Stream for {camera_name} started")


@jpeg_blueprint.route('/stop_service', methods=['POST'])
def stop_service():
    """
    Stop the receiving streams for a given camera.
    """
    data = request.json
    camera_name = data.get('camera_name')

    if not camera_name:
        return jsonify(error="Camera name not provided"), 400

    if camera_name in stream_sources:
        stream_sources[camera_name].stop()
        return jsonify(status=f"Stream for {camera_name} stopped")
    else:
        return jsonify(error="Camera name not found"), 404


@jpeg_blueprint.route('/save_past', methods=['POST'])
def save_past():
    """
    Save a segment of past video and timestamps for a given camera.

    :return message corresponding message
    """
    if not request.is_json:
        return jsonify({'message': 'request is not json'}), 400

    data = request.json
    camera_name = data.get('camera_name')
    start_time = data.get('start_time', 180)  # default to 180 seconds (3 min)
    stop_time = data.get('stop_time', 0)  # default to current time

    dest_folder = data.get('dest_folder')  # default to None if not provided
    save_path = data.get('save_path')  # default to None if not provided

    is_timestamps = data.get('is_timestamps', False)  # default to False if not provided

    if not camera_name:
        return jsonify(error="Camera name not provided"), 400
    if is_timestamps:
        stream_sources[camera_name].save_past(start_time, stop_time, dest_folder, save_path)
        return jsonify(status=f"video from {start_time} to {stop_time} for {camera_name} is saved!")

    if camera_name in stream_sources:
        current_time_ms = int(time.time() * 1000)
        start_time_ms = current_time_ms - (start_time * 1000)
        stop_time_ms = current_time_ms - (stop_time * 1000)

        stream_sources[camera_name].save_past(start_time_ms, stop_time_ms, dest_folder, save_path)
        return jsonify(status=f"Past {start_time} seconds video for {camera_name} is saved!")
    else:
        return jsonify(error="Camera name not found"), 404


@jpeg_blueprint.route('/save_next', methods=['POST'])
def save_next():
    """
    Schedule saving of the next period of time segment of video for a given camera.
    """
    data = request.json
    camera_name = data.get('camera_name')
    minutes = data.get('minutes', 15)  # default to 15 minutes

    if not camera_name:
        return jsonify(error="Camera name not provided"), 400

    if camera_name in stream_sources:
        stream_sources[camera_name].save_next_n_minutes(minutes)
        return jsonify(status=f"Next {minutes} minutes for {camera_name} will be saved after they elapse")
    else:
        return jsonify(error="Camera name not found"), 404


@jpeg_blueprint.route('/start_recording', methods=['POST'])
def start_rec():
    """
    Begin recording the video stream for a specified camera.
    """
    data = request.json
    camera_name = data.get('camera_name')

    if not camera_name:
        return jsonify(error="Camera name not provided"), 400

    if camera_name in stream_sources:
        stream_sources[camera_name].start_recording()
        return jsonify(status=f"Recording started for {camera_name}")
    else:
        return jsonify(error="Camera name not found"), 404


@jpeg_blueprint.route('/stop_recording', methods=['POST'])
def stop_rec():
    """
    Stop recording the video stream for a specified camera and save the recording.
    """
    data = request.json
    camera_name = data.get('camera_name')

    if not camera_name:
        return jsonify(error="Camera name not provided"), 400

    if camera_name in stream_sources:
        stream_sources[camera_name].stop_recording()
        return jsonify(status=f"Recording stopped and saved for {camera_name}")
    else:
        return jsonify(error="Camera name not found"), 404


@jpeg_blueprint.route('/check', methods=['GET'])
def check_status():
    """
    Check and return the status of all active camera streams.
    """
    alive_streams = {}
    for camera_name in stream_sources:

        alive_streams[camera_name] = stream_sources[camera_name].is_running

    return jsonify(alive_streams)

#Video streams segmenter



The **Video streams segmenter** is a tool to manage and record video streams of varied types. It offers two segmenter modules to save the video from streams:

1. **Traditional Video Stream Segmenter**:

   - **Supported Formats**: For standard video streams such as `RTSP`, `RTMP`, `HLS`, etc.

   - **Storage Mechanism**: Using `ffmpeg` to segments streams into defined chunks stored on disk. It maintains a fixed duration of video segments.

   - **Video Reconstruction**: Reconstruct a video with specific intervals from the stored segments.

     

2. **JPEG Stream Segmenter**:

   - **Design**: Crafted for streams that relay individual JPEG frames alongside their timestamps.

     ``` python
     timestamp_bytes = str(timestamp).encode('utf-8')
     delimiter = b'---timestamp---'
     
     b'Content-Type: image/jpeg\r\n\r\n' + frame + delimiter + timestamp_bytes + b'\r\n--frame\r\n'
     ```

     

   - **Storage Mechanism**: This segmenter caches JPEG frames and their timestamps in an in-memory queue. 

   - **Video Reconstruction**: It offers the capability to concatenate a designated time range of JPEG frames from the queue into a video. Alongside, it saves the associated timestamps to a `.txt` file.

## Features

- **Past Recoding**: Save video and timestamps from stream segments/frames from a past specified timeframe.
- **Future Recording**: Save video and timestamps from stream segments/frames from a future specified timeframe.

## Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

### Running the Service

```shell
gunicorn -c guni_config.py run:app
```




import os
import subprocess
import time
from datetime import datetime

OUTPUT_FOLDER = "temp_trunks"


def reconstruct_files(start_time, end_time, output_file="output.mp4"):
    files_to_concatenate = []

    for filename in os.listdir(OUTPUT_FOLDER):
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        # Extract timestamp from filename format: stream-%Y-%m-%d_%H-%M-%S.ts
        file_datetime_str = filename.split('.')[0].split('stream-')[-1]
        file_datetime = datetime.strptime(file_datetime_str, "%Y-%m-%d_%H-%M-%S")
        file_timestamp = int(file_datetime.timestamp())

        if start_time <= file_timestamp <= end_time:
            files_to_concatenate.append(filepath)

    files_to_concatenate.sort()  # Ensure files are in order

    if not files_to_concatenate:
        raise ValueError("No files found for the given time range")

    # Create a text file listing all the files to concatenate
    list_file_path = 'concat_list.txt'
    with open(list_file_path, 'w') as f:
        for file in files_to_concatenate:
            f.write(f"file '{file}'\n")

    # Using FFmpeg's concat demuxer
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file_path,
        '-c', 'copy',
        output_file
    ]
    subprocess.call(command)

    # Delete the concat_list.txt file
    os.remove(list_file_path)

    return output_file


# Example usage, if you want to test:
if __name__ == "__main__":
    current_timestamp = int(time.time())
    output_file = reconstruct_files(current_timestamp - 10, current_timestamp, "reconstructed_output.mp4")
    print(f"Reconstructed file saved as {output_file}")

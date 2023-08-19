import os
import subprocess

DIRECTORY_NAME = "trunks"
OUTPUT_FILE = "output.mp4"
TEMP_LIST_FILE = "temp_list.txt"


def concatenate_chunks():
    # Get a list of all the .ts files sorted by their names (which contain timestamps)
    chunks = sorted([f for f in os.listdir(DIRECTORY_NAME) if f.endswith(".ts")])

    # Write the list to the temporary list file
    with open(TEMP_LIST_FILE, "w") as file:
        for chunk in chunks:
            file.write(f"file '{os.path.join(DIRECTORY_NAME, chunk)}'\n")

    # Use ffmpeg to concatenate them into a single mp4 video
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", TEMP_LIST_FILE,
        "-c", "copy",
        OUTPUT_FILE
    ]

    subprocess.run(command)

    # Optionally: remove the temporary list file
    os.remove(TEMP_LIST_FILE)


concatenate_chunks()
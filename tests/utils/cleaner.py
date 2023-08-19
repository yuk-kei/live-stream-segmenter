# cleaner.py
import os
import time

OUTPUT_FOLDER = "temp_trunks"

while True:
    current_time = time.time()

    for filename in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        file_age = current_time - os.path.getctime(file_path)
        if file_age > 10 * 60:  # 2 hours in seconds
            os.remove(file_path)
            print("Removed", file_path)
    print("waiting...")
    # Check for old files every 10 minutes
    time.sleep(10 * 60)


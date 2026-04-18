import logging
import os
import time

from run_preprocessor.save_reader import CurrentSaveReader, SaveFileListener

# Configure logging to see the listener's internal logs
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load path from environment variable or a local untracked file
SAVE_PATH = os.getenv("STS_SAVE_PATH")
if not SAVE_PATH:
    try:
        with open("save_path.txt", "r") as f:
            SAVE_PATH = f.read().strip()
    except FileNotFoundError:
        SAVE_PATH = "current_run.save"  # Default fallback


def my_callback(file_path: str):
    """This function runs every time the file is updated."""
    reader = CurrentSaveReader.from_file(file_path)

    print("\n" + "=" * 30)
    print("🔔 SAVE FILE UPDATE DETECTED!")
    print(f"Current Act Index: {reader.current_act_index}")
    print(f"Total Acts Loaded: {len(reader.acts)}")
    act_index = reader.current_act_index
    print(f"Next Elite is:  {reader.acts[act_index].next_elite()}")
    print(f"Next Normal encounter is: {reader.acts[act_index].next_normal_encounter()}")
    print("=" * 30 + "\n")


if __name__ == "__main__":
    if not os.path.exists(SAVE_PATH):
        print(f"⚠️ Warning: File not found at {SAVE_PATH}")
        print("The listener will wait for it to be created.")

    print(f"🚀 Starting listener on: {SAVE_PATH}")
    print("Press Ctrl+C to stop.")

    # Initialize and start the listener
    listener = SaveFileListener(SAVE_PATH, my_callback, SAVE_PATH, interval=1.0)
    listener.start()

    try:
        # Keep the main thread alive so the background listener thread can work
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping listener...")
        listener.stop()
        print("Done.")

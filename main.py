import logging
import os
import time

from run_preprocessor.save_reader import CurrentSaveReader, SaveFileListener
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load path from environment variable or a local untracked file
SAVE_PATH = os.getenv("STS_SAVE_PATH")
if not SAVE_PATH:
    try:
        with open("save_path.txt", "r") as f:
            SAVE_PATH = f.read().strip()
    except FileNotFoundError:
        SAVE_PATH = "current_run.save"  # Default fallback


def callback(file_path: str, eval: Evaluator):
    reader = CurrentSaveReader.from_file(file_path)
    logger.info("\n" + "=" * 30)
    logger.info(
        "🔔 SAVE FILE UPDATE DETECTED! Time: " + time.strftime("%Y-%m-%d %H:%M:%S")
    )
    if len(reader.map_point_history.map_point_history) == 0:
        logger.warning("No map point history found in save file. Assume still at Neow.")
        return

    snapshot = PlayerSnapshot(reader)
    logger.info(
        f"Current Act: {snapshot.current_act} at floor {snapshot.current_act_floor}"
    )
    eval.predict_damage_taken(reader)
    logger.info("=" * 30 + "\n")


def main():
    try:
        with open("run_preprocessor/tests/save_path.txt", "r") as f:
            SAVE_PATH = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(
            "Save path not found. Please set the STS_SAVE_PATH environment variable or create a save_path.txt file with the path to your current_run.save."
        )
    logger.info(f"🚀 Starting listener")
    evaluator = Evaluator("testfiles/xgb_model.joblib", SAVE_PATH)
    listener = SaveFileListener(SAVE_PATH, callback, SAVE_PATH, evaluator, interval=1.0)
    listener.start()
    try:
        # Keep the main thread alive so the background listener thread can work
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping listener...")
        listener.stop()
        print("Done.")


if __name__ == "__main__":
    main()

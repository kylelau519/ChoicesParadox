import argparse
import logging
import os
import readline
import time

import config
import temp_UI.cli as cli
from run_preprocessor.save_reader import CurrentSaveReader, SaveFileListener
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SAVE_PATH = config.current_run_path


class GlobalState:
    def __init__(self):
        self.reader = None
        self.evaluator = None
        self.last_update = 0


state = GlobalState()


def callback(file_path: str, eval_obj: Evaluator):
    try:
        reader = CurrentSaveReader.from_file(file_path)

        state.reader = reader
        state.evaluator = eval_obj
        state.last_update = time.time()

        logger.info("\n" + "=" * 30)
        logger.info(
            "🔔 SAVE FILE UPDATE DETECTED! Time: " + time.strftime("%Y-%m-%d %H:%M:%S")
        )
        if len(reader.map_point_history.map_point_history) == 0:
            logger.warning(
                "No map point history found in save file. Assume still at Neow."
            )
            return

        snapshot = PlayerSnapshot(reader)
        snapshot.run()
        logger.info(
            f"Current Act: {snapshot.current_act} at floor {snapshot.current_act_floor}"
        )

        eval_obj.predict_damage_taken(reader)
        logger.info(
            "Type 'eval', 'relic', 'remove' or 'upgrade' to enter choices or 'help' for commands."
        )
        logger.info("=" * 30 + "\n")
    except Exception as e:
        logger.error(f"Error in callback: {e}")


def main():
    parser = argparse.ArgumentParser(description="Choices Paradox CLI")
    parser.add_argument(
        "--char",
        type=str,
        choices=list(config.CHARACTER_CONFIGS.keys()),
        help="Override character (e.g., ironclad, silent, defect, necrobinder, regent)",
    )
    args = parser.parse_args()

    if args.char:
        config.CHARACTER = args.char
        logger.info(f"👤 Character overridden to: {config.CHARACTER}")

    global SAVE_PATH
    logger.info(f"🚀 Starting listener on {SAVE_PATH}")

    model_path = config.get_model_path()
    logger.info(f"Using model: {model_path}")
    evaluator = Evaluator.from_file(model_path)

    # Start the background listener
    listener = SaveFileListener(SAVE_PATH, callback, SAVE_PATH, evaluator, interval=1.0)
    listener.start()

    print("Welcome to Choices Paradox! The listener is active in the background.")
    cli.show_help()

    try:
        while True:
            # Set up default completer for main commands
            commands = ["eval", "relic", "remove", "upgrade", "help", "quit", "exit"]

            def cmd_completer(text, state_idx):
                options = [c for c in commands if c.startswith(text)]
                try:
                    return options[state_idx]
                except IndexError:
                    return None

            readline.set_completer(cmd_completer)
            readline.parse_and_bind("tab: complete")

            cmd = input("> ").strip().lower()
            if not cmd:
                continue
            if cmd == "eval":
                cli.take_card_choices(state)
            elif cmd == "relic":
                cli.take_relic_choices(state)
            elif cmd == "remove":
                cli.take_removal_choices(state)
            elif cmd == "upgrade":
                cli.take_upgrade_choices(state)
            elif cmd == "_debug":
                cli.debug(state)
            elif cmd == "help":
                cli.show_help()
            elif cmd in ["quit", "exit"]:
                print("Stopping listener...")
                listener.stop()
                break
            else:
                print(f"Unknown command: {cmd}. Type 'help' for available commands.")

    except KeyboardInterrupt:
        print("\nStopping listener...")
        listener.stop()
        print("Done.")


if __name__ == "__main__":
    main()

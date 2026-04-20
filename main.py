import logging
import os
import readline
import time

import temp_UI.cli as cli
from run_preprocessor.save_reader import CurrentSaveReader, SaveFileListener
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator

# Configure logging
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
        try:
            with open("run_preprocessor/tests/save_path.txt", "r") as f:
                SAVE_PATH = f.read().strip()
        except FileNotFoundError:
            SAVE_PATH = "current_run.save"  # Default fallback


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
    global SAVE_PATH
    logger.info(f"🚀 Starting listener on {SAVE_PATH}")

    # Change model path here to choose which model to use.
    model_path = os.getenv("MODEL_PATH", "models/hurdle_model_multi_version.joblib")
    # model_path = os.getenv("MODEL_PATH", "models/hurdle_model_testfile.joblib")

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
            elif cmd == "_deck":
                if state.reader:
                    from stat_analysis.preprocess import CURSE_CARDS, EXPERIMENT_PANEL

                    snapshot = PlayerSnapshot(state.reader)
                    snapshot.run()
                    print("\n--- DEBUG: Current Deck ---")

                    # Manual feature engineering for display
                    display_cards = snapshot.deck.cards.copy()
                    total_curses = 0
                    total_upgrades = 0

                    if EXPERIMENT_PANEL["group_all_curses"]:
                        for card_id in list(display_cards.keys()):
                            if card_id in CURSE_CARDS:
                                total_curses += display_cards.pop(card_id)

                    if EXPERIMENT_PANEL["correlate_upgrades"]:
                        for card_id in list(display_cards.keys()):
                            if card_id.endswith("+"):
                                count = display_cards.get(card_id, 0)
                                total_upgrades += count
                                base_id = card_id.removesuffix("+")
                                display_cards[base_id] = (
                                    display_cards.get(base_id, 0) + count
                                )
                                # Note: we don't necessarily want to remove the upgraded one from display
                                # if we want to see the original deck, but the user asked for features.
                                # Let's show the "engineered" features.

                    active_cards = sorted(
                        [(k, v) for k, v in display_cards.items() if v > 0]
                    )
                    for card_id, count in active_cards:
                        print(f"  {card_id:.<35} {count}")

                    print("-" * 40)
                    if EXPERIMENT_PANEL["group_all_curses"]:
                        print(f"  {'TOTAL_CURSES':.<35} {total_curses}")
                    if EXPERIMENT_PANEL["correlate_upgrades"]:
                        print(f"  {'TOTAL_UPGRADES':.<35} {total_upgrades}")

                    if EXPERIMENT_PANEL["starter_ratio"]:
                        starter_ids = {
                            "CARD.STRIKE_IRONCLAD",
                            "CARD.DEFEND_IRONCLAD",
                            "CARD.STRIKE_SILENT",
                            "CARD.DEFEND_SILENT",
                            "CARD.STRIKE_DEFECT",
                            "CARD.DEFEND_DEFECT",
                            "CARD.STRIKE_REGENT",
                            "CARD.DEFEND_REGENT",
                            "CARD.STRIKE_NECROBINDER",
                            "CARD.DEFEND_NECROBINDER",
                        }
                        total_starter = 0
                        for card_id, count in snapshot.deck.cards.items():
                            base_id = card_id.rstrip("+")
                            if base_id in starter_ids:
                                total_starter += count
                        total_cards = sum(snapshot.deck.cards.values())
                        ratio = total_starter / total_cards if total_cards > 0 else 0.0
                        print(f"  {'STARTER_RATIO':.<35} {ratio:.4f}")

                    print(
                        f"\nTotal Unique: {len(active_cards)} | Total Cards: {sum(v for _, v in snapshot.deck.cards.items())}"
                    )

                    print("---------------------------\n")
                else:
                    print("No save file loaded yet.")
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

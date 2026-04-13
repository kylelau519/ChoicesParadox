import logging
import os
import readline
import time

from item_scrapper.items import ALL_CARDS, validate_relic_id
from run_preprocessor.deck import validate_card_id
from run_preprocessor.save_reader import CurrentSaveReader, SaveFileListener
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.state_vectorizer import TestCaseGenerator

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

        eval_obj.predict_damage_taken(reader)
        logger.info("Type 'eval' to enter card choices or 'help' for commands.")
        logger.info("=" * 30 + "\n")
    except Exception as e:
        logger.error(f"Error in callback: {e}")


class CardCompleter:
    def __init__(self, card_ids):
        self.card_ids = sorted(card_ids)
        self.short_ids = sorted(
            [cid[5:] for cid in self.card_ids if cid.startswith("CARD.")]
        )
        self.all_options = sorted(list(set(self.card_ids + self.short_ids)))

    def complete(self, text, state_idx):
        if state_idx == 0:
            if text:
                upper_text = text.upper()
                self.matches = [
                    s for s in self.all_options if s.upper().startswith(upper_text)
                ]
            else:
                self.matches = []
        try:
            return self.matches[state_idx]
        except (IndexError, AttributeError):
            return None


def take_card_choices():
    if not state.reader or not state.evaluator:
        print(
            "No save file loaded. Please wait for the listener to detect a save file."
        )
        return

    reader = state.reader
    eval_obj = state.evaluator

    # Set up readline for card autocomplete
    completer = CardCompleter(ALL_CARDS.keys())
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    print("\n--- Card Choice Evaluation ---")
    print("Enter card choices one by one. Press Enter on an empty line to finish.")
    card_ids = []
    while True:
        try:
            prompt = f"Card {len(card_ids) + 1} (TAB to autocomplete): "
            card_id_input = input(prompt).strip()
            if not card_id_input:
                break
            try:
                validated_id = validate_card_id(card_id_input)
                card_ids.append(validated_id)
            except ValueError:
                # Error already logged in validate_card_id
                continue
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nCancelled.")
            return

    if not card_ids:
        print("No cards entered. Skipping evaluation.")
        return

    current_act = reader.current_act()
    snapshot = PlayerSnapshot(reader)
    generator = TestCaseGenerator(snapshot)

    # Elite Encounter Prediction
    generator.set_encounter(current_act.next_elite())
    elite_cases, elite_labels = generator.test_adding_cards(card_ids)
    elite_pred = eval_obj.predict(elite_cases)

    # Normal Encounter Prediction
    generator.set_encounter(current_act.next_normal_encounter())
    normal_cases, labels = generator.test_adding_cards(card_ids)
    normal_pred = eval_obj.predict(normal_cases)

    print("\nResults:")
    for idx, label in enumerate(labels):
        logger.info(f"Predicted damage taken after taking {label}:")
        logger.info(
            f"  {current_act.next_normal_encounter().removeprefix('ENCOUNTER.').lower()}: {normal_pred[idx]:.2f}\t {current_act.next_elite().removeprefix('ENCOUNTER.').lower()}: {elite_pred[idx]:.2f}"
        )
        # We use a simple heuristic: sum of damage in next normal and next elite
        #
    remaining_combats = list(
        set(
            current_act.remaining_normal_encounters()
            + current_act.remaining_elite_encounters()
        )
    )
    min_dmg = 100000
    card_dmg_dict = {}
    suggested_card = "Skip"
    for combat in remaining_combats:
        generator.set_encounter(combat)
        cases, _ = generator.test_adding_cards(card_ids)
        preds = eval_obj.predict(cases)
        for idx, label in enumerate(labels):
            card_dmg_dict[label] = card_dmg_dict.get(label, 0) + preds[idx]
    logger.info("\nTotal predicted damage for remaining combats with each card choice:")
    for label, total_dmg in card_dmg_dict.items():
        logger.info(f"  {label}: {total_dmg:.2f}")
        if total_dmg < min_dmg:
            min_dmg = total_dmg
            suggested_card = label
    if suggested_card == "Original":
        suggested_card = "Skip"
    logger.info(f"\nSuggested card choice: {suggested_card}")
    print("-----------------------------\n")


# confirm when 3 relics choices are out, the map is loaded and map index is right
def take_relic_choices():
    if not state.reader or not state.evaluator:
        print(
            "No save file loaded. Please wait for the listener to detect a save file."
        )
        return
    print("\n--- Relic Choice Evaluation ---")
    reader = state.reader
    eval_obj = state.evaluator
    print("Enter relic choices one by one. Press Enter on an empty line to finish.")
    relic_ids = []
    while True:
        try:
            prompt = f"Relic {len(relic_ids) + 1} (TAB to autocomplete): "
            relic_id_input = input(prompt).strip()
            if not relic_id_input:
                break
            # Similar validation for relics as cards
            validated_id = validate_relic_id(relic_id_input)
            relic_ids.append(validated_id)
        except ValueError:
            # Error already logged in validate_relic_id
            continue
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
    current_act = reader.current_act()
    snapshot = PlayerSnapshot(reader)
    generator = TestCaseGenerator(snapshot)
    suggested_relic = "Should Not See This"
    min_dmg = 100000
    relic_dmg_dict = {}
    remaining_combats = list(
        set(
            current_act.remaining_normal_encounters()
            + current_act.remaining_elite_encounters()
        )
    )
    for combat in remaining_combats:
        generator.set_encounter(combat)
        cases, _ = generator.test_adding_relics(relic_ids)
        preds = eval_obj.predict(cases)
        for idx, label in enumerate(relic_ids):
            relic_dmg_dict[label] = relic_dmg_dict.get(label, 0) + preds[idx]
    logger.info(
        "\nTotal predicted damage for remaining combats with each relic choice:"
    )
    for label, total_dmg in relic_dmg_dict.items():
        logger.info(f"  {label}: {total_dmg:.2f}")
        if total_dmg < min_dmg:
            min_dmg = total_dmg
            suggested_relic = label
    logger.info(f"\nSuggested relic choice: {suggested_relic}")


def show_help():
    print("\nAvailable commands:")
    print("  eval   - Enter card choices to evaluate")
    print("  help   - Show this help message")
    print("  quit   - Exit the application")
    print("")


def main():
    global SAVE_PATH
    try:
        with open("run_preprocessor/tests/save_path.txt", "r") as f:
            SAVE_PATH = f.read().strip()
    except FileNotFoundError:
        pass  # Keep default or env var

    logger.info(f"🚀 Starting listener on {SAVE_PATH}")
    evaluator = Evaluator("testfiles/xgb_model.joblib", SAVE_PATH)

    # Start the background listener
    listener = SaveFileListener(SAVE_PATH, callback, SAVE_PATH, evaluator, interval=1.0)
    listener.start()

    print("Welcome to Choices Paradox! The listener is active in the background.")
    show_help()

    try:
        while True:
            # Set up default completer for main commands
            commands = ["eval", "help", "quit", "exit"]

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
                take_card_choices()
            elif cmd == "help":
                show_help()
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

import logging
import os
import readline
import time

from item_scrapper.items import ALL_CARDS, RELICS, validate_relic_id
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
        logger.info(
            "Type 'eval', 'relic', 'remove' or 'upgrade' to enter choices or 'help' for commands."
        )
        logger.info("=" * 30 + "\n")
    except Exception as e:
        logger.error(f"Error in callback: {e}")


class IdCompleter:
    def __init__(self, ids, prefix):
        self.ids = sorted(ids)
        self.short_ids = sorted(
            [cid[len(prefix) :] for cid in self.ids if cid.startswith(prefix)]
        )
        self.all_options = sorted(list(set(self.ids + self.short_ids)))

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
    completer = IdCompleter(ALL_CARDS.keys(), "CARD.")
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
    snapshot.run()
    generator = TestCaseGenerator(snapshot)
    print(snapshot.deck.cards)

    remaining_combats = set(
        current_act.remaining_normal_encounters()
        + current_act.remaining_elite_encounters()
    )
    if current_act.boss():
        remaining_combats.add(current_act.boss())
    if current_act.second_boss():
        remaining_combats.add(current_act.second_boss())

    unique_combats = sorted([c for c in remaining_combats if c])

    print(f"\nEvaluating against {len(unique_combats)} unique remaining combats...")

    total_damages = {}  # label -> total_damage

    # Get labels from generator
    generator.set_encounter(unique_combats[0])
    _, labels = generator.test_adding_cards(card_ids)
    for label in labels:
        total_damages[label] = 0.0

    for combat in unique_combats:
        generator.set_encounter(combat)
        cases, _ = generator.test_adding_cards(card_ids)
        preds = eval_obj.predict(cases)
        for idx, label in enumerate(labels):
            total_damages[label] += preds[idx]

    min_dmg = 1000000
    suggested_card = "Skip"

    logger.info("\nTotal predicted damage for remaining combats with each card choice:")
    for label, total_dmg in total_damages.items():
        logger.info(f"  {label}: {total_dmg:.2f}")
        if total_dmg < min_dmg:
            min_dmg = total_dmg
            suggested_card = label

    if suggested_card == "Original":
        suggested_card = "Skip"

    logger.info(f"\nSuggested card choice: {suggested_card}")
    print("-----------------------------\n")


def take_relic_choices():
    if not state.reader or not state.evaluator:
        print(
            "No save file loaded. Please wait for the listener to detect a save file."
        )
        return

    reader = state.reader
    eval_obj = state.evaluator

    # Set up readline for relic autocomplete
    completer = IdCompleter(RELICS.keys(), "RELIC.")
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    print("\n--- Relic Choice Evaluation ---")
    print("Enter relic choices one by one. Press Enter on an empty line to finish.")
    relic_ids = []
    while True:
        try:
            prompt = f"Relic {len(relic_ids) + 1} (TAB to autocomplete): "
            relic_id_input = input(prompt).strip()
            if not relic_id_input:
                break
            try:
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

    if not relic_ids:
        print("No relics entered. Skipping evaluation.")
        return

    current_act = reader.current_act()
    snapshot = PlayerSnapshot(reader)
    snapshot.run()
    generator = TestCaseGenerator(snapshot)

    remaining_combats = set(
        current_act.remaining_normal_encounters()
        + current_act.remaining_elite_encounters()
    )
    if current_act.boss():
        remaining_combats.add(current_act.boss())
    if current_act.second_boss():
        remaining_combats.add(current_act.second_boss())

    unique_combats = sorted([c for c in remaining_combats if c])

    print(f"\nEvaluating against {len(unique_combats)} unique remaining combats...")

    total_damages = {}  # label -> total_damage

    # Get labels from generator
    generator.set_encounter(unique_combats[0])
    _, labels = generator.test_adding_relics(relic_ids)
    for label in labels:
        total_damages[label] = 0.0

    for combat in unique_combats:
        generator.set_encounter(combat)
        cases, _ = generator.test_adding_relics(relic_ids)
        preds = eval_obj.predict(cases)
        for idx, label in enumerate(labels):
            total_damages[label] += preds[idx]

    min_dmg = 1000000
    suggested_relic = "Skip"

    logger.info(
        "\nTotal predicted damage for remaining combats with each relic choice:"
    )
    for label, total_dmg in total_damages.items():
        logger.info(f"  {label}: {total_dmg:.2f}")
        if total_dmg < min_dmg:
            min_dmg = total_dmg
            suggested_relic = label

    if suggested_relic == "Original":
        suggested_relic = "Skip"

    logger.info(f"\nSuggested relic choice: {suggested_relic}")
    print("-----------------------------\n")


def take_removal_choices():
    if not state.reader or not state.evaluator:
        print(
            "No save file loaded. Please wait for the listener to detect a save file."
        )
        return

    reader = state.reader
    eval_obj = state.evaluator

    current_act = reader.current_act()
    snapshot = PlayerSnapshot(reader)
    snapshot.run()
    generator = TestCaseGenerator(snapshot)

    deck_cards = sorted(list(snapshot.deck.cards.keys()))
    if not deck_cards:
        print("Deck is empty. Nothing to remove.")
        return

    remaining_combats = set(
        current_act.remaining_normal_encounters()
        + current_act.remaining_elite_encounters()
    )
    if current_act.boss():
        remaining_combats.add(current_act.boss())
    if current_act.second_boss():
        remaining_combats.add(current_act.second_boss())

    unique_combats = sorted([c for c in remaining_combats if c])

    print(
        f"\nEvaluating removals against {len(unique_combats)} unique remaining combats..."
    )

    total_damages = {}  # label -> total_damage

    # Labels: "Original" + "Removed CardName"
    labels = ["Original"] + [f"Removed {c.replace('CARD.', '')}" for c in deck_cards]
    for label in labels:
        total_damages[label] = 0.0

    for combat in unique_combats:
        generator.set_encounter(combat)

        # Original damage
        orig_case = generator.vectorize()
        total_damages["Original"] += eval_obj.predict(orig_case)[0]

        # Damage for each removal
        for card_id in deck_cards:
            case, label = generator.test_remove_card(card_id)
            total_damages[label] += eval_obj.predict(case)[0]

    min_dmg = 1000000
    suggested_removal = "None"

    # Sort removals by total damage (ascending)
    sorted_removals = sorted(total_damages.items(), key=lambda x: x[1])

    logger.info("\nTop 3 Best removals (including Original):")
    for i in range(min(3, len(sorted_removals))):
        label, total_dmg = sorted_removals[i]
        logger.info(f"  {i + 1}. {label}: {total_dmg:.2f}")

    if len(sorted_removals) > 3:
        logger.info("\nLast 2 Worst removals:")
        for i in range(max(3, len(sorted_removals) - 2), len(sorted_removals)):
            label, total_dmg = sorted_removals[i]
            logger.info(f"  {label}: {total_dmg:.2f}")

    suggested_removal = sorted_removals[0][0]
    logger.info(f"\nSuggested removal: {suggested_removal}")
    print("-----------------------------\n")


def take_upgrade_choices():
    if not state.reader or not state.evaluator:
        print(
            "No save file loaded. Please wait for the listener to detect a save file."
        )
        return

    reader = state.reader
    eval_obj = state.evaluator

    current_act = reader.current_act()
    snapshot = PlayerSnapshot(reader)
    snapshot.run()
    generator = TestCaseGenerator(snapshot)

    deck_cards = sorted(list(snapshot.deck.cards.keys()))
    if not deck_cards:
        print("Deck is empty. Nothing to upgrade.")
        return

    remaining_combats = set(
        current_act.remaining_normal_encounters()
        + current_act.remaining_elite_encounters()
    )
    if current_act.boss():
        remaining_combats.add(current_act.boss())
    if current_act.second_boss():
        remaining_combats.add(current_act.second_boss())

    unique_combats = sorted([c for c in remaining_combats if c])

    print(
        f"\nEvaluating upgrades against {len(unique_combats)} unique remaining combats..."
    )

    total_damages = {}  # label -> total_damage
    total_damages["Original"] = 0.0

    valid_upgrades = []
    for card_id in deck_cards:
        if not card_id.endswith("+"):
            valid_upgrades.append(card_id)
            label = f"Upgraded {card_id.replace('CARD.', '')}"
            total_damages[label] = 0.0

    if not valid_upgrades:
        print("No cards available to upgrade (all cards might be already upgraded).")
        return

    for combat in unique_combats:
        generator.set_encounter(combat)

        # Original damage
        orig_case = generator.vectorize()
        total_damages["Original"] += eval_obj.predict(orig_case)[0]

        # Damage for each upgrade
        for card_id in valid_upgrades:
            case, label = generator.test_upgrade_card(card_id)
            if case is not None:
                total_damages[label] += eval_obj.predict(case)[0]

    # Sort upgrades by total damage (ascending)
    sorted_upgrades = sorted(total_damages.items(), key=lambda x: x[1])

    logger.info("\nTop 3 Best upgrades (including Original):")
    for i in range(min(3, len(sorted_upgrades))):
        label, total_dmg = sorted_upgrades[i]
        logger.info(f"  {i + 1}. {label}: {total_dmg:.2f}")

    if len(sorted_upgrades) > 3:
        logger.info("\nLast 2 Worst upgrades:")
        for i in range(max(3, len(sorted_upgrades) - 2), len(sorted_upgrades)):
            label, total_dmg = sorted_upgrades[i]
            logger.info(f"  {label}: {total_dmg:.2f}")

    suggested_upgrade = sorted_upgrades[0][0]
    logger.info(f"\nSuggested upgrade: {suggested_upgrade}")
    print("-----------------------------\n")


def show_help():
    print("\nAvailable commands:")
    print("  eval   - Enter card choices to evaluate")
    print("  relic  - Enter relic choices to evaluate")
    print("  remove - Evaluate which card is best to remove from current deck")
    print("  upgrade - Evaluate which card is best to upgrade in current deck")
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
                take_card_choices()
            elif cmd == "relic":
                take_relic_choices()
            elif cmd == "remove":
                take_removal_choices()
            elif cmd == "upgrade":
                take_upgrade_choices()
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

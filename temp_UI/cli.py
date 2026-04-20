import logging
import readline

from item_scrapper.items import ALL_CARDS, RELICS, validate_card_id, validate_relic_id
from run_preprocessor.snapshot import PlayerSnapshot

logger = logging.getLogger(__name__)


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


def evaluate_and_print_results(eval_obj, state_reader, test_func, items, title):
    print(f"\n--- {title} Evaluation ---")
    results = eval_obj.evaluate_game_options(state_reader, test_func, items)
    if not results:
        print("No combats to evaluate against.")
        return

    # Check if results are dicts (mean, low, high)
    sorted_results = sorted(results.items(), key=lambda x: x[1]["mean"])

    print(f"\nWeighted damage score for remaining combats ({title}):")
    header = f"{'Rank':<5} | {'Option':<35} | {'Mean':<8} | {'80% CL Range':<20}"

    print(header)
    print("-" * len(header))

    for i, (label, val) in enumerate(sorted_results, 1):
        # Format label for better display
        display_label = label
        if display_label == "Original":
            display_label = "Skip / No Change"

        cl_range = f"[{val['low']:>6.2f}, {val['high']:>6.2f}]"
        print(f"{i:<5} | {display_label:<35} | {val['mean']:>8.2f} | {cl_range:<20}")

    suggested = sorted_results[0][0]
    if suggested == "Original":
        suggested = "Skip"
    print(f"\nSuggested {title.lower()} choice: {suggested}")
    print("-----------------------------\n")


def take_card_choices(state):
    if not state.reader or not state.evaluator:
        print("No save file loaded.")
        return

    completer = IdCompleter(ALL_CARDS.keys(), "CARD.")
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    print("\n--- Card Choice Input ---")
    card_ids = []
    while True:
        try:
            card_id_input = input(f"Card {len(card_ids) + 1} (TAB/Enter): ").strip()
            if not card_id_input:
                break
            card_ids.append(validate_card_id(card_id_input))
        except ValueError:
            continue
        except (EOFError, KeyboardInterrupt):
            return

    if not card_ids:
        return

    def test_func(generator, items):
        return generator.test_adding_cards(items)

    evaluate_and_print_results(
        state.evaluator, state.reader, test_func, card_ids, "Card"
    )


def take_relic_choices(state):
    if not state.reader or not state.evaluator:
        print("No save file loaded.")
        return

    completer = IdCompleter(RELICS.keys(), "RELIC.")
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    print("\n--- Relic Choice Input ---")
    relic_ids = []
    while True:
        try:
            relic_id_input = input(f"Relic {len(relic_ids) + 1} (TAB/Enter): ").strip()
            if not relic_id_input:
                break
            relic_ids.append(validate_relic_id(relic_id_input))
        except ValueError:
            continue
        except (EOFError, KeyboardInterrupt):
            return

    if not relic_ids:
        return

    def test_func(generator, items):
        return generator.test_adding_relics(items)

    evaluate_and_print_results(
        state.evaluator, state.reader, test_func, relic_ids, "Relic"
    )


def take_removal_choices(state):
    if not state.reader or not state.evaluator:
        print("No save file loaded.")
        return

    snapshot = PlayerSnapshot(state.reader)
    snapshot.run()
    deck_cards = sorted([c for c in snapshot.deck.cards if snapshot.deck.cards[c] > 0])
    if not deck_cards:
        print("Deck is empty.")
        return

    def test_func(generator, cards):
        return generator.test_removals(cards)

    evaluate_and_print_results(
        state.evaluator, state.reader, test_func, deck_cards, "Removal"
    )


def take_upgrade_choices(state):
    if not state.reader or not state.evaluator:
        print("No save file loaded.")
        return

    snapshot = PlayerSnapshot(state.reader)
    snapshot.run()
    valid_upgrades = [
        c
        for c in snapshot.deck.cards
        if snapshot.deck.cards[c] > 0 and not c.endswith("+") and f"{c}+" in ALL_CARDS
    ]
    if not valid_upgrades:
        print("No cards to upgrade.")
        return

    def test_func(generator, cards):
        return generator.test_upgrades(cards)

    evaluate_and_print_results(
        state.evaluator, state.reader, test_func, valid_upgrades, "Upgrade"
    )


def debug(state):
    if state.reader:
        from stat_analysis.preprocess import CURSE_CARDS, EXPERIMENT_PANEL

        snapshot = PlayerSnapshot(state.reader)
        snapshot.run()
        print("\n--- DEBUG: Current Deck ---")

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
                    display_cards[base_id] = display_cards.get(base_id, 0) + count

        active_cards = sorted([(k, v) for k, v in display_cards.items() if v > 0])
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


def show_help():
    print("\nAvailable commands:")
    print("  eval   - Enter card choices to evaluate")
    print("  relic  - Enter relic choices to evaluate")
    print("  remove - Best card to remove")
    print("  upgrade - Best card to upgrade")
    print("  help   - Show help")
    print("  quit   - Exit")
    print("")

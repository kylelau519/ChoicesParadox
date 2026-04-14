import logging
import readline
import time

from item_scrapper.items import ALL_CARDS, RELICS, validate_relic_id
from run_preprocessor.deck import validate_card_id
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.state_vectorizer import TestCaseGenerator

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
    total_damages = eval_obj.evaluate_game_options(state_reader, test_func, items)
    if not total_damages:
        print("No combats to evaluate against.")
        return

    sorted_results = sorted(total_damages.items(), key=lambda x: x[1])

    logger.info(f"\nTotal predicted damage for remaining combats ({title}):")
    for label, total_dmg in sorted_results[:3]:  # Top 3
        logger.info(f"  {label}: {total_dmg:.2f}")

    if len(sorted_results) > 3:
        if len(sorted_results) > 4:
            logger.info("  ...")
        for label, total_dmg in sorted_results[-1:]:  # Worst 1
            logger.info(f"  {label}: {total_dmg:.2f}")

    suggested = sorted_results[0][0]
    if suggested == "Original":
        suggested = "Skip"
    logger.info(f"\nSuggested {title.lower()} choice: {suggested}")
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


def show_help():
    print("\nAvailable commands:")
    print("  eval   - Enter card choices to evaluate")
    print("  relic  - Enter relic choices to evaluate")
    print("  remove - Best card to remove")
    print("  upgrade - Best card to upgrade")
    print("  help   - Show help")
    print("  quit   - Exit")
    print("")

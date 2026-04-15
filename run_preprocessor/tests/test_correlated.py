import os
import unittest

from run_preprocessor.card import Card
from run_preprocessor.deck import Deck
from run_preprocessor.run_reader import RawData
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot


class TestReader(unittest.TestCase):
    def test_deck_correlated(self):
        # Test Normal
        deck = Deck([], correlated=False)
        deck.add("CARD.BASH+")
        print(f"Normal Deck: {deck.cards}")
        self.assertEqual(deck.cards.get("CARD.BASH+"), 1)
        self.assertEqual(
            deck.cards.get("CARD.BASH"), None
        )  # Should be None since we don't add the base card in non-correlated mode

        # Test Correlated
        deck_corr = Deck([], correlated=True)
        deck_corr.add("CARD.BASH+")
        print(f"Correlated Deck: {deck_corr.cards}")
        self.assertEqual(deck_corr.cards.get("CARD.BASH+"), 1)
        self.assertEqual(
            deck_corr.cards.get("CARD.BASH"), 1
        )  # Should be 1 since we add the base card in correlated mode

        # Test Remove Correlated
        deck_corr.remove("CARD.BASH+")
        print(f"Correlated Deck after remove: {deck_corr.cards}")
        self.assertEqual(deck_corr.cards.get("CARD.BASH+"), 0)
        self.assertEqual(deck_corr.cards.get("CARD.BASH"), 0)

    def test_upgrade_correlated(self):
        deck = Deck([], correlated=True)
        deck.add("CARD.BASH")  # Initial BASH
        print(f"Initial: {deck.cards}")

        # Simulate Upgrade: only add BASH+, don't remove BASH
        deck.add("CARD.BASH+")
        print(f"After Upgrade (only add BASH+): {deck.cards}")
        self.assertEqual(deck.cards.get("CARD.BASH+"), 1)
        self.assertEqual(deck.cards.get("CARD.BASH"), 2)


if __name__ == "__main__":
    _ = unittest.main()

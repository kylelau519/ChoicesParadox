import logging

from item_scrapper.items import validate_card_id
from run_preprocessor.card import Card

logger = logging.getLogger(__name__)


class Deck:
    def __init__(self, cards: list[Card], correlated: bool = False):
        self.correlated = correlated
        self.cards: dict[str, int] = {}  # card id to count
        for card in cards:
            # card.id is usually already formatted like CARD.BASH
            # but we can validate it just in case
            deck_key = card.id
            upgrade_lv = card.current_upgrade_level
            if upgrade_lv is not None and upgrade_lv == 1:
                deck_key += "+"
            self.add(deck_key)

    def get(self, card_id: str):
        # We don't necessarily want to validate on get, but we can normalize
        card_id = card_id.strip().upper()
        if not card_id.startswith("CARD."):
            card_id = "CARD." + card_id
        return self.cards.get(card_id)

    def _increment(self, card_id: str):
        prev_num_card = self.get(card_id)
        if prev_num_card is None:
            prev_num_card = 0
        new_num_card = prev_num_card + 1
        self.cards[card_id] = new_num_card

    def _decrement(self, card_id: str):
        prev_num_card = self.get(card_id)
        if prev_num_card is None or prev_num_card <= 0:
            logger.error(
                f"Attempted to remove card {card_id} which does not exist in deck."
            )
            # We don't necessarily want to crash in all cases, but for now we keep it
            raise Exception(f"deck.remove tried to remove {card_id} that doesn't exist")
        new_num_card = prev_num_card - 1
        self.cards[card_id] = new_num_card

    def add(self, card_id: str):
        card_id = validate_card_id(card_id)
        self._increment(card_id)
        if self.correlated and card_id.endswith("+"):
            base_id = card_id.removesuffix("+")
            self._increment(base_id)

    def remove(self, card_id: str):
        card_id = validate_card_id(card_id)
        self._decrement(card_id)
        if self.correlated and card_id.endswith("+"):
            base_id = card_id.removesuffix("+")
            self._decrement(base_id)

    def add_card(self, card: Card):
        deck_key = card.id
        upgrade_lv = card.current_upgrade_level
        if upgrade_lv is not None and upgrade_lv == 1:
            deck_key += "+"
        self.add(deck_key)

    def remove_card(self, card: Card):
        deck_key = card.id
        upgrade_lv = card.current_upgrade_level
        if upgrade_lv is not None and upgrade_lv == 1:
            deck_key += "+"
        self.remove(deck_key)

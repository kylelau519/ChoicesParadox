import logging

from item_scrapper.items import validate_card_id
from run_preprocessor.card import Card

logger = logging.getLogger(__name__)


class Deck:
    def __init__(self, cards: list[Card]):
        self.cards: dict[str, int] = {}  # card id to count
        for card in cards:
            # card.id is usually already formatted like CARD.BASH
            # but we can validate it just in case
            card_id = validate_card_id(card.id)
            prev_num_card = self.cards.get(card_id)
            new_num_card = (prev_num_card or 0) + 1
            self.cards[card_id] = new_num_card

    def get(self, card_id: str):
        # We don't necessarily want to validate on get, but we can normalize
        card_id = card_id.strip().upper()
        if not card_id.startswith("CARD."):
            card_id = "CARD." + card_id
        return self.cards.get(card_id)

    def add(self, card_id: str):
        card_id = validate_card_id(card_id)
        prev_num_card = self.get(card_id)
        if prev_num_card is None:
            prev_num_card = 0
        new_num_card = prev_num_card + 1
        self.cards[card_id] = new_num_card

    def remove(self, card_id: str):
        card_id = validate_card_id(card_id)
        prev_num_card = self.get(card_id)
        if prev_num_card is None or prev_num_card <= 0:
            logger.error(
                f"Attempted to remove card {card_id} which does not exist in deck."
            )
            raise Exception(f"deck.remove tried to remove {card_id} that doesn't exist")
        new_num_card = prev_num_card - 1
        self.cards[card_id] = new_num_card

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

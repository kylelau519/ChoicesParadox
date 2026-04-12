import logging

from run_preprocessor.card import Card

logger = logging.getLogger(__name__)


class Deck:
    def __init__(self, cards: list[Card]):
        self.cards: dict[str, int] = {}  # card id to count
        for card in cards:
            prev_num_card = self.cards.get(card.id)
            new_num_card = (prev_num_card or 0) + 1
            self.cards[card.id] = new_num_card

    def get(self, card_id: str):
        return self.cards.get(card_id)

    def add(self, card_id: str):
        prev_num_card = self.get(card_id)
        if prev_num_card is None:
            prev_num_card = 0
        new_num_card = prev_num_card + 1
        self.cards[card_id] = new_num_card

    def remove(self, card_id: str):
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

from run_preprocessor.card import RawCard
from run_preprocessor.types import Card


class Deck:
    def __init__(self, cards: list[RawCard]):
        self.cards: dict[str, int] = {}  # card id to count
        for card in cards:
            prev_num_card = self.cards.get(card.id)
            new_num_card = prev_num_card + 1 if prev_num_card is not None else 1
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
            raise Exception(f"deck.remove tried to remove {card_id} that doesn't exist")
        new_num_card = prev_num_card - 1
        self.cards[card_id] = new_num_card

    def add_card(self, card: Card):
        deck_key = card["id"]
        upgrade_lv = card.get("current_upgrade_level")
        if upgrade_lv != None and upgrade_lv == 1:
            deck_key += "+"
        self.add(deck_key)

    def remove_card(self, card: Card):
        deck_key = card["id"]
        upgrade_lv = card.get("current_upgrade_level")
        if upgrade_lv != None and upgrade_lv == 1:
            deck_key += "+"
        self.remove(deck_key)

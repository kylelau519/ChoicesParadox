import json
import os
import requests

def save_items(url, path):
    res = requests.get(url)
    items = res.json()
    with open(path, "w") as f:
        json.dump(items, f, indent=4)

def main():
    cards_url = "https://spire-codex.com/api/cards"
    encounters_url = "https://spire-codex.com/api/encounters"
    potions_url = "https://spire-codex.com/api/potions"
    relics_url = "https://spire-codex.com/api/relics"

    os.makedirs("data/items", exist_ok=True)

    save_items(cards_url, "data/items/cards.json")
    save_items(encounters_url, "data/items/encounters.json")
    save_items(potions_url, "data/items/potions.json")
    save_items(relics_url, "data/items/relics.json")

if __name__ == "__main__":
    main()

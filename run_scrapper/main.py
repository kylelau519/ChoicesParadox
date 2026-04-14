import json
import os
from typing import Any

from scraper import STS2RunsScraper, SpireCodexScraper


def save_data(runs: list[dict[str, Any]]):
    for run in runs:
        players = run.get("players")
        if players is None:
            continue
        if len(players) != 1:
            continue

        player = players[0]
        ascension = f"a{str(run['ascension'])}"  # 0 -> a0
        character = (
            player["character"].split(".")[-1].lower()
        )  # "CHARACTER.REGENT" -> "regent"
        build_id = run["build_id"]
        dir = f"data/runs/{build_id}/{character}/{ascension}"
        os.makedirs(dir, exist_ok=True)

        seed = run["seed"]
        start_time = run["start_time"]
        path = f"{dir}/{seed}_{start_time}.run"
        with open(path, "w") as f:
            print(f"Saving {path}")
            json.dump(run, f, indent=4)

def main():
    codex = SpireCodexScraper()
    codex.scrape()
    s = STS2RunsScraper()
    s.scrape()

    save_data(s.data)
    save_data(codex.data)

    print(f"Succssfully scraped {len(codex.data)} runs from spire-codex.")
    print(f"Succssfully scraped {len(s.data)} runs from sts2runs.")


if __name__ == "__main__":
    main()

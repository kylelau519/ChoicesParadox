import json
import os

from scraper import STS2RunsScraper, SpireCodexScraper


def main():
    codex = SpireCodexScraper()
    codex.scrape()
    s = STS2RunsScraper()
    s.scrape()

    for r in s.data:
        run = r["run"]

        # skip multi-player games
        players = run["players"]
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

    for run in codex.data:
        # skip multi-player games
        players = run.get("players")
        if players == None:
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

    print(f"Succssfully scraped {len(codex.data)} runs from spire-codex.")
    print(f"Succssfully scraped {len(s.data)} runs from sts2runs.")


if __name__ == "__main__":
    main()

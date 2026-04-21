import json
import os
from pathlib import Path

from scraper import STS2ReplaysScraper, SpireCodexScraper, STS2RunsScraper


def save_data(runs):
    for run in runs:
        save_run(run)

def save_run(run):
    players = run.get("players")
    if players is None:
        print(f"fail to read run, skipping it...")
        return
    if len(players) != 1:
        print(f"co-op run detected, skipping it...")
        return

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
    file_path = Path(path)
    if file_path.is_file():
        print(f"{seed}_{start_time}.run already exists, skipping it...")
    else:
        with open(file_path, "w") as f:
            print(f"Saving {path}...")
            json.dump(run, f, indent=4)

def main():
    replays = STS2ReplaysScraper()
    replays.scrape(callback=save_run)
    s = STS2RunsScraper()
    s.scrape(callback=save_run)
    codex = SpireCodexScraper()
    codex.scrape(callback=save_run)

if __name__ == "__main__":
    main()

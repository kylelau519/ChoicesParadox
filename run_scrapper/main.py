import os
import json
from scraper import STS2RunsScraper

def main():
    s = STS2RunsScraper()
    s.scrape()
    print(f"Succssfully scraped {len(s.data)} runs.")

    for r in s.data:
        run = r["run"]

        # skip multi-player games
        players = run["players"]
        if len(players) != 1:
            continue

        player = players[0]
        ascension = f"a{str(run["ascension"])}" # 0 -> a0
        character = player["character"].split(".")[-1].lower() # "CHARACTER.REGENT" -> "regent"

        dir = f"data/runs/{character}/{ascension}"
        os.makedirs(dir, exist_ok=True)

        seed = run["seed"]
        start_time = run["start_time"]
        path = f"{dir}/{seed}_{start_time}.run"
        with open(path, "w") as f:
            print(f"Saving {path}")
            json.dump(run, f, indent=4)

    print(f"Succssfully scraped {len(s.data)} runs.")

if __name__ == "__main__":
    main()

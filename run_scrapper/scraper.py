import re

from curl_cffi import requests
from bs4 import BeautifulSoup


class BaseScraper:
    def __init__(self, runs_url: str, run_base_url: str, pagination: dict[str, int]):
        self.runs_url: str = runs_url
        self.run_base_url: str = run_base_url
        self.data = []
        self.pagination: dict[str, int] = pagination

    def scrape(self, callback=None) -> None:
        raise NotImplemented("Not implemented")

class SpireCodexScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "https://spire-codex.com/api/runs/list",
            "https://spire-codex.com/api/runs/shared",
            {
                "total": 0,
                "page": 1,
                "per_page": 50,
                "total_pages": 1,
            }
        )

    def scrape(self, callback=None):
        while self.pagination["page"] <= self.pagination["total_pages"]:
            r = requests.get(self.runs_url, params={"page": self.pagination["page"]})
            resp = r.json()

            for run in resp["runs"]:
                id = run["run_hash"]
                url = self.run_base_url + "/" + id
                print(f"Scraping from {url}...")
                r = requests.get(url)
                if callback is not None:
                    callback(r.json())
                else:
                    self.data.append(r.json())

            self.pagination["total"] = resp["total"]
            self.pagination["page"] = resp["page"]
            self.pagination["per_page"] = resp["per_page"]
            self.pagination["total_pages"] = resp["total_pages"]
            self.pagination["page"] += 1

class STS2RunsScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "https://sts2runs.com/api/runs/community",
            "https://sts2runs.com/api/runs",
            {
                "page": 1,
                "limit": 25,
                "total": 0,
                "totalPages": 1,
            }
        )

    def scrape(self, callback=None):
        while self.pagination["page"] <= self.pagination["totalPages"]:
            r = requests.get(self.runs_url, params={"page": self.pagination["page"]})
            resp = r.json()

            for run in resp["runs"]:
                id = run["id"]
                url = self.run_base_url + "/" + str(id)
                print(f"Scraping from {url}...")
                r = requests.get(url)
                if callback is not None:
                    callback(r.json()["run"])
                else:
                    self.data.append(r.json()["run"])

            self.pagination = resp["pagination"]
            self.pagination["page"] += 1

class STS2ReplaysScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "https://www.sts2replays.com/runs",
            "https://www.sts2replays.com/runs",
            {
                "page": 0, # 0 base index
                "total_pages": 1,
            }
        )

    def scrape(self, callback=None):
        while self.pagination["page"] < self.pagination["total_pages"]:
            r = requests.get(
                self.runs_url,
                impersonate="chrome120",
                params={"page": self.pagination["page"]}
            )
            print(f"visiting page {self.pagination['page']} / {self.pagination['total_pages'] - 1}")
            soup = BeautifulSoup(r.text, "html.parser")
            next_link = soup.find("a", text=re.compile("^Next"))
            if self.pagination["total_pages"] == 1:
                max_page_link = next_link.find_previous_sibling("a")
                max_page = max_page_link.text
                if max_page.isdigit():
                    self.pagination["total_pages"] = int(max_page)
                else:
                    print("The max page is not numeric.")
                    return

            # for run in resp["runs"]:
            #     id = run["id"]
            #     url = self.run_base_url + "/" + str(id)
            #     print(f"Scraping from {url}...")
            #     r = requests.get(url)
            #     if callback is not None:
            #         callback(r.json()["run"])
            #     else:
            #         self.data.append(r.json()["run"])

            self.pagination["page"] += 1

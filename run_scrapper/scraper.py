from typing import Any
import requests


class BaseScraper:
    def __init__(self, runs_url: str, run_base_url: str, pagination: dict[str, int]):
        self.runs_url: str = runs_url
        self.run_base_url: str = run_base_url
        self.data: list[Any] = []
        self.pagination: dict[str, int] = pagination

    def scrape(self):
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

    def get_run(self, id: str):
        url = self.run_base_url + "/" + id
        print(url)
        r = requests.get(url)
        resp = r.json()
        return resp

    def scrape(self):
        while self.pagination["page"] <= self.pagination["total_pages"]:
            r = requests.get(self.runs_url, params={"page": self.pagination["page"]})
            resp = r.json()

            for run in resp["runs"]:
                run = self.get_run(run["run_hash"])
                self.data.append(run)

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

    def get_run(self, id):
        url = self.run_base_url + "/" + str(id)
        print(url)
        r = requests.get(url)
        resp = r.json()
        return resp

    def scrape(self):
        while self.pagination["page"] <= self.pagination["totalPages"]:
            r = requests.get(self.runs_url, params={"page": self.pagination["page"]})
            resp = r.json()

            for run in resp["runs"]:
                run = self.get_run(run["id"])
                self.data.append(run)

            self.pagination = resp["pagination"]
            self.pagination["page"] += 1

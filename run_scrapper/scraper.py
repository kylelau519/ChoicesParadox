import requests


class STS2RunsScraper:
    runs_url = "https://sts2runs.com/api/runs/community"
    run_base_url = "https://sts2runs.com/api/runs"
    data = []
    pagination = {
        "page": 1,
        "limit": 25,
        "total": 0,
        "totalPages": 1,
    }

    def __init__(self):
        return

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

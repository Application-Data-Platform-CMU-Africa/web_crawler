
import requests
import json
import csv


class FetchOpenSource():
    GITHUB_API_URL = "https://api.github.com/search/repositories"

    def __init__(self, topic, *args, **kwargs) -> None:
        self.topic = topic
        # Define the query parameters
        self.params = {
            "q": f"topic:{topic}",
            "sort": "stars",
            "order": "desc",
            "per_page": 100
        }

        # token = "your_personal_access_token"
        self.headers = {
            # 'Authorization': f'token {token}'
        }

        # Keys to retain when fetching

        self.keys_to_keep = [
            "id", "name", "full_name", "private", "html_url", "description",
            "forks_count", "disabled", "allow_forking", "is_template",
            "topics", "visibility", "forks"
        ]

        self.owner_keys_to_keep = [
            "login", "id", "avatar_url", "url", "html_url", "organizations_url"
        ]
        self.license_keys_to_keep = [
            "key", "name", "spdx_id", "url", "node_id"
        ]

    def fetch_repositories(self, ):
        response = requests.get(self.GITHUB_API_URL,
                                headers=self.headers, params=self.params)
        if response.status_code == 200:
            data = response.json()
            return data['items']
        else:
            print(f"Failed to fetch repositories: {response.status_code}")
            return []

    def filter_repo_data(self, repo):
        filtered_repo = {key: repo[key]
                         for key in self.keys_to_keep if key in repo}
        if 'owner' in repo:
            for key in self.owner_keys_to_keep:
                filtered_repo[f'owner_{key}'] = repo['owner'].get(key, None)
        if 'license' in repo and repo['license'] is not None:
            for key in self.license_keys_to_keep:
                filtered_repo[f'license_{key}'] = repo['license'].get(
                    key, None)
        return filtered_repo

    def save_to_json(self, data, file_path):
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)

    def save_to_csv(self, data, file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for repo in data:
                writer.writerow(repo)

    def crawl(self):
        repos = self.fetch_repositories()

        if not repos:
            print("No repositories found.")
            return

        # Filter repository data
        filtered_repos = [self.filter_repo_data(repo) for repo in repos]

        self.save_to_json(filtered_repos, './data/fetched_repos_all_info.json')

        urls = [repo['html_url'] for repo in repos]
        self.save_to_json(urls, './configs/fetched_repos.json')

        self.save_to_csv(
            filtered_repos, f'./data/{self.topic}-opensource-repos.csv')

        print("Data saved to files.")

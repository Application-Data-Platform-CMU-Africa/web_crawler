import requests
from bs4 import BeautifulSoup
import json
import os

from utils.util import cprint


class LicenceAnalyser():
    def __init__(self, CONFIGS, CONFIG_FILE, TEST=True, *args, **kwargs) -> None:
        self.CONFIGS = CONFIGS
        self.CONFIG_FILE = CONFIG_FILE
        self.data = {}
        self.TEST = TEST
        self.url_list = []

    def fetch_license_from_github(self, repo_url):
        # Ensure the URL is for a GitHub repository
        if not repo_url.startswith("https://github.com/"):
            raise ValueError("URL must be a GitHub repository URL")

        # Extract repository details
        repo_parts = repo_url.rstrip('/').split('/')
        user, repo_name = repo_parts[-2], repo_parts[-1]

        # Common branches and license filenames to check
        branches = ['main', 'master']
        license_filenames = ['LICENSE', 'LICENSE.txt', 'LICENSE.md']

        # Try to find the LICENSE file in common branches and filenames
        for branch in branches:
            for file_name in license_filenames:
                # Construct URL to LICENSE file
                license_url = f"{repo_url}/blob/{branch}/{file_name}"

                # Fetch the LICENSE file page
                response = requests.get(license_url)
                if response.status_code == 200:
                    # Parse the page using BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Locate the raw LICENSE file URL
                    license_file_url = license_url.replace("/blob/", "/raw/")

                    # Fetch the raw LICENSE file content
                    license_response = requests.get(license_file_url)
                    if license_response.status_code != 200:
                        return {"status": 500, "message": "Could not fetch LICENSE file"}

                    license_content = license_response.text

                    # Prepare the JSON entry
                    json_entry = {
                        "status": 200,
                        "url": repo_url,
                        "appname": repo_name,
                        "licence": license_content
                    }

                    return json_entry

        return {"status": 500, "message": "Could not fetch LICENSE file"}

    def update_or_append_to_json_file(self, data, filename='licenses.json'):
        # Read existing data from JSON file
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        # Check if the repository URL already exists
        url_exists = False
        for entry in existing_data:
            if entry["url"] == data["url"]:
                entry["licence"] = data["licence"]
                url_exists = True
                break

        # Append new entry if URL does not exist
        if not url_exists:
            existing_data.append(data)

        # Write updated data back to JSON file
        with open(filename, 'w') as file:
            json.dump(existing_data, file, indent=4)

    def get_repos_from_github(self, ):
        pass

    def crawl(self,):
        # github_repo_url = self.CONFIGS.get('repo_url')

        try:
            for github_repo_url in self.CONFIGS:
                license_data = self.fetch_license_from_github(github_repo_url)
                if license_data.get('status') == 500:
                    # Replace this a proper log system
                    cprint(f"{github_repo_url} >> {license_data.get('message')}")
                file_name = self.CONFIG_FILE if self.CONFIG_FILE else "licenses.json"
                self.update_or_append_to_json_file(license_data, file_name)
                print(
                    f"License data for {github_repo_url} updated or appended successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

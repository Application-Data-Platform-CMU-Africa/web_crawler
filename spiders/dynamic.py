# UNDER DEVELOPMENT

import multiprocessing
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from utils.util import SpiderStore
from bs4 import BeautifulSoup
import requests
import concurrent.futures
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


class DynamicSpider():
    wait_timeout = 16

    def __init__(self, CONFIGS, DB, TEST=True, *args, **kwargs) -> None:
        self.CONFIGS = CONFIGS
        self.db = DB
        self.data = {}
        self.TEST = TEST
        self.url_list = []
        chrome_options = Options()
        # Set headless mode
        # chrome_options.add_argument("--headless")
        # Optional: Disable GPU acceleration to potentially avoid certain issues in headless mode
        # chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=chrome_options)

    def crawl(self):
        # Get links first
        self._get_links()
        # Visit each one of them to collect details
        is_semidynamic = self.CONFIGS["is_semidynamic"]
        if is_semidynamic:
            self.driver.quit()
            data = self._get_links_details_static()
        else:
            data = self._get_links_details()
            self.driver.quit()

        # Store the results in a JSON file and DB if necessary(TEST=True)
        if data is not None:
            for d in data:
                SpiderStore(d, self.db, self.CONFIGS,
                            self.TEST).store_records()
        # Close the driver

    def _get_links(self):
        self.driver.get(url=self.CONFIGS['start_url'])
        sleep(2)

        try:
            accept = self.driver.find_element(
                By.CSS_SELECTOR, self.CONFIGS["cookies_button"])

            accept.click()
            sleep(2)
        except:
            pass
        last_page = self.CONFIGS["pages"]

        for i in range(int(last_page)):
            sleep(1)
            try:
                # Wait until the element with the specified CSS selector is present on the page
                element_present = EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CONFIGS["links_selector"]))
                WebDriverWait(self.driver, self.wait_timeout).until(
                    element_present)
                # element = self.driver.find_element(By.CSS_SELECTOR, self.CONFIGS["links_selector"])
                results = self.driver.find_elements(
                    By.CSS_SELECTOR, self.CONFIGS["links_selector"])
                for a in results:
                    # print(a.get_property('href'))
                    self.url_list.append(f"{a.get_property('href')}")
            except Exception as e:
                print(f"Element not found ----: {e}")

            try:
                # //*[@id="content"]/div[3]/div/div/div/div/div/div/section/div[2]/ul/li[6]/a
                next = self.driver.find_element(
                    By.CSS_SELECTOR, self.CONFIGS["next_button"])
                # next = self.driver.find_element(By.XPATH, self.CONFIGS["next_button"])
                # print(f"This can not go next {next}")

                if i < int(last_page)-1:
                    next.click()
            except Exception as e:

                try:
                    self.driver.get(
                        url=f"{self.CONFIGS['start_url']}&page={i+2}")
                except:
                    break

    def fetch_link_details(self, link):

        response = requests.get(link)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        title = ""
        title_element = soup.select(self.CONFIGS["title_selector"])
        if title_element:
            title = title_element[0].text

        description = ""
        if self.CONFIGS["source_name"] == "DATA.WORLDBANK.ORG":
            description = self._get_data_description_worldbank()
        else:
            description_element = soup.select(
                self.CONFIGS["description_selector"])
            if description_element:
                description = description_element[0].text

        tags = []
        tags_list = soup.select(self.CONFIGS["tags_selector"])

        for tag in tags_list:
            tags.append(tag.text.split(" ")[0])

        print(title)
        return {
            "name": title,
            "data": link,
            "description": description,
            "category": "OTHER",
            "type": "link",
            "tags": tags,
            "isPrivate": False,
            "organization": self.CONFIGS["source_name"],
            # "html":f"{soup}",
            "text": soup.get_text()
        }

    def _get_links_details_static(self):
        data = []
        print(f"Links {len(self.url_list)}")
        max_ = multiprocessing.cpu_count()
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            data = list(executor.map(self.fetch_link_details, self.url_list))

        return data

    def filter_links(self):
        filtered_links = [link for link in self.url_list if link != ""]
        return filtered_links

    def _get_links_details(self):
        data = []
        # print(self.url_list)

        for link in self.filter_links():
            print("This is the title ......")
            print(link)
            self.driver.get(url=link)
            sleep(1)
            # PAG_READY = False
            try:
                # Wait until the element with the specified CSS selector is present on the page
                element_present = EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CONFIGS["title_selector"]))
                WebDriverWait(self.driver, self.wait_timeout).until(
                    element_present)
                PAG_READY = True
            except Exception as e:
                print(f"Element not found: {e}")
                break

            tags = []
            # check if drop down
            try:
                dp = self.driver.find_element(
                    By.CSS_SELECTOR, self.CONFIGS["tags_dropdown_selector"])
                # If the button exist click it and wait ....
                if dp:
                    dp.click()
                    sleep(0.5)
                #  select tags
                tags_list = self.driver.find_elements(
                    By.CSS_SELECTOR,  self.CONFIGS["tags_selector"])
                for tag in tags_list:
                    tags.append(tag.text.split(" ")[0])
            except Exception as e:
                print(f"Message : (On Tags - dynamic.py 165-177) {e}")

            # Select the title and description
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            plain_text = soup.get_text()
            title = ""
            title_element = soup.select(self.CONFIGS["title_selector"])

            if title_element:
                title = title_element[0].text

            description = ""
            if self.CONFIGS["source_name"] == "DATA.WORLDBANK.ORG":
                description = self._get_data_description_worldbank()
            else:
                description_element = soup.select(
                    self.CONFIGS["description_selector"])
                if description_element:
                    description = description_element[0].text

            data.append({
                "name": title,
                "data": link,
                "description": description,
                "category": "OTHER",
                "type": "link",
                "tags": tags,
                "isPrivate": False,
                "organization": self.CONFIGS["source_name"],
                # "html":f"{plain_text}"
            })

            # else:
            #     return None

        return data

    # Specifically made for worldbank
    def _get_data_description_worldbank(self):
        description = ""
        try:
            details_btn = self.driver.find_element(
                By.CSS_SELECTOR, self.CONFIGS["details_btn_setector"])
            # print(dp)
            if details_btn:
                details_btn.click()
                sleep(0.5)
                description = self.driver.find_element(
                    By.CSS_SELECTOR, self.CONFIGS["description_selector"]).text
        except Exception as e:
            print(f"Error in world bank selector {e}")

        return description

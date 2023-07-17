from bs4 import BeautifulSoup
import scrapy
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from LinkModel import Link
from util import Utils


class StaticSpider(CrawlSpider):
    name = "static"
    configurations = {}
    def __init__(self, CONFIGS, DB, TEST=True, *args, **kwargs):

        self.allowed_domains = [CONFIGS["domain"],]
        self.start_urls = [CONFIGS["start_url"],]
        self.configurations = CONFIGS
        self.db = DB
        self.is_test = TEST
        self.rules = (
            Rule(LinkExtractor(allow=(CONFIGS["rules"][0]["allow"],), )),
            Rule(LinkExtractor(allow=(CONFIGS["rules"][1]["allow"],), deny=(CONFIGS["rules"][1]["deny"],)), callback=self.parse_items),
        )
        super(StaticSpider, self).__init__(*args, **kwargs)
       

    def parse_items(self, response):
        # print(f"+++++++++++++ {self.configurations['title_selector']} +++++++++++")
        title = response.css(f'{self.configurations["title_selector"]}').get()
        description = response.css(f'{self.configurations["description_selector"]}').get()
        tags_list = []
        # The page has tags
        if self.configurations["tags_selector"] is not None:
            tags = response.css(f'{self.configurations["tags_selector"]}')
            # Parssing html using beautiful soup for better html extraction
            # soup = BeautifulSoup(tags, 'html.parser')
            c = 0
            for tag in tags:
                if len(tag.get()) <20: 
                    # print(tag.get())
                    tags_list.append(tag.get())
                    c+=1
                # NOt more than 4 tags (We can change this if the API allows it)
                if c > 4:
                    break
        data = {
                "name":title,
                "data": response.request.url,
                "description":description,
                "category":"OTHER",
                "type":"link",
                "tags": tags_list,
                "isPrivate":False,
                "organization":self.configurations["source_name"]
        }
        # pass the collected data in our util factory for tranformation and sanity check
        u = Utils(data)
       
        # If the link has no title skip it
        if u.has_null_title():
            pass
        else:
            # Strip the text and set the description=title if there is no description
            u.nomalize_text()
            data = u.data
            # Create a Link object to get the hashvalue 
            link = Link(
                data=data.get('data'),
                category=data.get('category'),
                description=data.get('description'),
                name=data.get('name'),
                organization=data.get('organization'),
                tags=data.get('tags')
            )

            # Use the sql database only in a none test mode
            if self.is_test is False:
                # If the link was recorded before, skip it
                if self.db.check_if_exist(link.hash_value):
                    pass
                else:
                    self.db.add_link(link.data, link.name, link.hash_value, description, link.type, link.organization, link.tags, link.isPrivate, link.category)
                    # print(soup.text)
                
            # Save the data to a JSON file for quick visualization and testing in case TEST is True
            with open(f'{self.configurations["file_name"]}.json', 'a') as f:
                json.dump(data, f)
                f.write(',\n')


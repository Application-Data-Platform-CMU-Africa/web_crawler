from bs4 import BeautifulSoup
import scrapy
import json
import logging
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from storage.LinkModel import Link
from utils.util import DataProcessor

# Configure logging
logger = logging.getLogger(__name__)


class StaticSpider(CrawlSpider):
    """
    Static HTML spider using Scrapy for efficient crawling.

    Features:
    - Rule-based link following
    - Duplicate detection via hash values
    - Database and JSON output
    - Comprehensive error handling
    - Respects robots.txt
    """
    name = "static"
    CONFIGS = {}

    # Import Scrapy settings
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 30,
        'AUTOTHROTTLE_ENABLED': True,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, CONFIGS, DB, TEST=True, *args, **kwargs):
        """
        Initialize the static spider.

        Args:
            CONFIGS (dict): Website configuration (URL, selectors, rules)
            DB: Database connection object
            TEST (bool): If True, skip database writes
        """
        self.allowed_domains = [CONFIGS["domain"],]
        self.start_urls = [CONFIGS["start_url"],]
        self.CONFIGS = CONFIGS
        self.db = DB
        self.is_test = TEST

        logger.info(f"Initializing StaticSpider for {CONFIGS['source_name']}")
        logger.info(f"Start URL: {CONFIGS['start_url']}")
        logger.info(f"Test mode: {TEST}")

        self.rules = (
            Rule(LinkExtractor(allow=(CONFIGS["rules"][0]["allow"],), )),
            Rule(LinkExtractor(allow=(CONFIGS["rules"][1]["allow"],), deny=(
                CONFIGS["rules"][1]["deny"],)), callback=self.parse_items),
        )
        super(StaticSpider, self).__init__(*args, **kwargs)

    def parse_items(self, response):
        """
        Parse individual dataset pages and extract metadata.

        Args:
            response: Scrapy response object

        Returns:
            None (stores data in database/JSON file)
        """
        try:
            logger.info(f"Parsing: {response.url}")

            # Extract title with error handling
            title = response.css(f'{self.CONFIGS["title_selector"]}').get()
            if not title:
                logger.warning(f"No title found for {response.url}")

            # Extract description with error handling
            description = response.css(
                f'{self.CONFIGS["description_selector"]}').get()
            if not description:
                logger.debug(f"No description found for {response.url}")

            tags_list = []
            # The page has tags
            if self.CONFIGS["tags_selector"] is not None:
                try:
                    tags = response.css(f'{self.CONFIGS["tags_selector"]}')
                    c = 0
                    for tag in tags:
                        tag_value = tag.get()
                        if tag_value and len(tag_value) < 20:
                            tags_list.append(tag_value)
                            c += 1
                        # Not more than 4 tags (We can change this if the API allows it)
                        if c > 4:
                            break
                except Exception as e:
                    logger.error(f"Error extracting tags from {response.url}: {e}")
            else:
                logger.debug(f"No tags selector configured")

            # Build data object
            data = {
                "name": title,
                "data": response.request.url,
                "description": description,
                "category": "OTHER",
                "type": "link",
                "tags": tags_list,
                "isPrivate": False,
                "organization": self.CONFIGS["source_name"],
                "html": f"{response}",
                "text": response.css("p::text")
            }

            # Pass the collected data to DataProcessor for transformation and validation
            processed_data = DataProcessor(data)

            # If the link has no title, skip it
            if processed_data.has_null_title():
                logger.warning(f"Skipping {response.url} - null title")
                return

            # Get processed data
            data = processed_data.data

            # Create a Link object to generate hash value
            link = Link(
                data=data.get('data'),
                category=data.get('category'),
                description=data.get('description'),
                name=data.get('name'),
                organization=data.get('organization'),
                tags=data.get('tags')
            )

            # Store in database only in non-test mode
            if self.is_test is False:
                try:
                    # Check if link already exists to avoid duplicates
                    if self.db.check_if_exist(link.hash_value):
                        logger.info(f"Duplicate found, skipping: {response.url}")
                    else:
                        self.db.add_link(
                            link.data, link.name, link.hash_value, description,
                            link.type, link.organization, link.tags,
                            link.isPrivate, link.category
                        )
                        logger.info(f"Successfully stored: {link.name}")
                except Exception as e:
                    logger.error(f"Database error for {response.url}: {e}")

            # Save to JSON file for quick visualization and testing
            try:
                with open(f'{self.CONFIGS["file_name"]}.json', 'a') as f:
                    json.dump(data, f)
                    f.write(',\n')
            except Exception as e:
                logger.error(f"Error writing to JSON file: {e}")

        except Exception as e:
            logger.error(f"Fatal error parsing {response.url}: {e}", exc_info=True)

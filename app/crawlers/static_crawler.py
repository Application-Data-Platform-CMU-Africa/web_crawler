"""
Static Crawler
Scrapy-based crawler for static HTML websites
"""
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from typing import Dict, Optional
import logging
import json

from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class StaticSpider(CrawlSpider):
    """
    Scrapy spider for crawling static HTML sites
    """
    name = "static_spider"

    def __init__(self, config: Dict, processor: DataProcessor, callback_handler, *args, **kwargs):
        """
        Initialize spider

        Args:
            config: Site configuration
            processor: DataProcessor instance
            callback_handler: Handler for callbacks
        """
        self.site_config = config
        self.processor = processor
        self.handler = callback_handler

        # Set spider properties
        self.allowed_domains = [config['domain']]
        self.start_urls = [config['start_url']]

        # Build crawl rules
        rules_config = config.get('rules', [])
        self.rules = self._build_rules(rules_config)

        super().__init__(*args, **kwargs)

        logger.info(
            f"Initialized StaticSpider for {config.get('source_name')}")

    def _build_rules(self, rules_config):
        """Build Scrapy rules from configuration"""
        rules = []

        for rule_config in rules_config:
            allow = rule_config.get('allow', '')
            deny = rule_config.get('deny', '')

            # First rule: pagination (follow but don't parse)
            if rule_config.get('id') == 1:
                rules.append(
                    Rule(LinkExtractor(allow=allow, deny=deny))
                )
            # Second rule: dataset pages (follow and parse)
            else:
                rules.append(
                    Rule(
                        LinkExtractor(allow=allow, deny=deny),
                        callback='parse_dataset',
                        follow=True
                    )
                )

        return tuple(rules)

    def parse_dataset(self, response):
        """
        Parse individual dataset page

        Args:
            response: Scrapy response object
        """
        try:
            # Update stats
            self.handler.increment_pages_crawled()

            logger.info(f"Parsing: {response.url}")

            # Extract data using selectors from config
            title = self._extract_field(response, 'title_selector')
            description = self._extract_field(response, 'description_selector')
            tags = self._extract_tags(response)

            # Skip if no title
            if not title:
                logger.warning(f"No title found for {response.url}")
                return

            # Build dataset
            dataset = self.processor.build_dataset(
                title=title,
                url=response.url,
                description=description,
                tags=tags,
                source=self.site_config.get('source_name', 'Unknown'),
                crawl_job_id=self.handler.job_id
            )

            # Validate dataset
            if not self.processor.validate_dataset(dataset):
                logger.warning(f"Invalid dataset: {response.url}")
                return

            # Report dataset found
            self.handler.on_dataset_found(dataset)

        except Exception as e:
            logger.error(f"Error parsing {response.url}: {e}", exc_info=True)
            self.handler.on_error(e, {'url': response.url})

    def _extract_field(self, response, selector_key: str) -> Optional[str]:
        """
        Extract field using CSS selector from config

        Args:
            response: Scrapy response
            selector_key: Key in config (e.g., 'title_selector')

        Returns:
            Extracted text or None
        """
        try:
            selector = self.site_config.get(selector_key)
            if not selector:
                return None

            value = response.css(selector).get()
            return self.processor.clean_text(value) if value else None

        except Exception as e:
            logger.debug(f"Error extracting {selector_key}: {e}")
            return None

    def _extract_tags(self, response) -> list:
        """Extract tags from page"""
        try:
            selector = self.site_config.get('tags_selector')
            if not selector:
                return []

            tags = response.css(selector).getall()
            return self.processor.process_tags(tags) if tags else []

        except Exception as e:
            logger.debug(f"Error extracting tags: {e}")
            return []


class CallbackHandler:
    """Handles callbacks from Scrapy spider"""

    def __init__(self, crawler_instance):
        self.crawler = crawler_instance
        self.job_id = crawler_instance.job_id

    def increment_pages_crawled(self):
        """Increment pages crawled counter"""
        self.crawler.stats['pages_crawled'] += 1
        self.crawler.update_progress()

    def on_dataset_found(self, dataset: Dict):
        """Called when dataset is found"""
        self.crawler.stats['datasets_found'] += 1
        self.crawler.report_dataset(dataset)

    def on_error(self, error: Exception, context: Dict):
        """Called when error occurs"""
        self.crawler.report_error(error, context)


class StaticCrawler(BaseCrawler):
    """
    Crawler for static HTML websites using Scrapy
    """

    def __init__(self, config: Dict, job_id: str, options: Optional[Dict] = None):
        super().__init__(config, job_id, options)
        self.processor = DataProcessor()

    def crawl(self) -> Dict:
        """
        Execute crawl

        Returns:
            Crawl statistics
        """
        logger.info(
            f"Starting static crawl for {self.config.get('source_name')}")

        try:
            # Create callback handler
            handler = CallbackHandler(self)

            # Configure Scrapy settings
            scrapy_settings = {
                'LOG_LEVEL': 'INFO',
                'ROBOTSTXT_OBEY': True,
                'DOWNLOAD_DELAY': 2,
                'RANDOMIZE_DOWNLOAD_DELAY': True,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
                'RETRY_TIMES': 3,
                'DOWNLOAD_TIMEOUT': 30,
                'AUTOTHROTTLE_ENABLED': True,
                'USER_AGENT': 'Mozilla/5.0 (compatible; DatasetCrawler/1.0)'
            }

            # Create crawler process
            process = CrawlerProcess(settings=scrapy_settings)

            # Add spider to process
            process.crawl(
                StaticSpider,
                config=self.config,
                processor=self.processor,
                callback_handler=handler
            )

            # Start crawling (blocking)
            process.start()

            logger.info(f"Crawl completed. Stats: {self.stats}")

            return self.get_stats()

        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            self.report_error(e)
            raise

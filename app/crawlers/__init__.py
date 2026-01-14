"""
Crawler Implementations
Web scraping logic
"""
from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.static_crawler import StaticCrawler
from app.crawlers.data_processor import DataProcessor

__all__ = ['BaseCrawler', 'StaticCrawler', 'DataProcessor']

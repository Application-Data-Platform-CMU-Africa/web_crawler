"""
Base Crawler
Abstract base class for all crawlers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    Abstract base class for web crawlers

    All crawlers must implement the crawl() method
    """

    def __init__(self, config: Dict, job_id: str, options: Optional[Dict] = None):
        """
        Initialize crawler

        Args:
            config: Site configuration from configs/config.json
            job_id: CrawlJob UUID for tracking
            options: Optional crawl options (test_mode, max_pages, etc.)
        """
        self.config = config
        self.job_id = job_id
        self.options = options or {}

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'datasets_found': 0,
            'datasets_saved': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

        # Callbacks for progress reporting
        self.on_progress: Optional[Callable] = None
        self.on_dataset_found: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        logger.info(
            f"Initialized {self.__class__.__name__} for {config.get('source_name')}")

    @abstractmethod
    def crawl(self) -> Dict:
        """
        Main crawl method - must be implemented by subclasses

        Returns:
            Dict with crawl statistics
        """
        pass

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.on_progress = callback

    def set_dataset_callback(self, callback: Callable):
        """Set callback when dataset is found"""
        self.on_dataset_found = callback

    def set_error_callback(self, callback: Callable):
        """Set callback when error occurs"""
        self.on_error = callback

    def update_progress(self, **kwargs):
        """Report progress to callback"""
        if self.on_progress:
            self.on_progress(self.stats, **kwargs)

    def report_dataset(self, dataset: Dict):
        """Report found dataset to callback"""
        if self.on_dataset_found:
            self.on_dataset_found(dataset)

    def report_error(self, error: Exception, context: Dict = None):
        """Report error to callback"""
        self.stats['errors'] += 1
        if self.on_error:
            self.on_error(error, context or {})
        logger.error(f"Crawler error: {error}", exc_info=True)

    def get_stats(self) -> Dict:
        """Get current crawl statistics"""
        return self.stats.copy()

    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.options.get('test_mode', False)

    def get_max_pages(self) -> Optional[int]:
        """Get max pages limit if set"""
        return self.options.get('max_pages')

    def should_continue(self) -> bool:
        """Check if crawler should continue"""
        max_pages = self.get_max_pages()
        if max_pages and self.stats['pages_crawled'] >= max_pages:
            logger.info(f"Reached max pages limit: {max_pages}")
            return False
        return True

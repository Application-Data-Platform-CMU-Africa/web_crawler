"""
Crawler Service
Manages crawl operations and coordinates between crawlers and database
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from app.crawlers.static_crawler import StaticCrawler
from app.crawlers.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Service layer for managing crawl operations
    """

    def __init__(self, db_session=None):
        """
        Initialize crawler service

        Args:
            db_session: SQLAlchemy database session (optional for now)
        """
        self.db = db_session
        self.processor = DataProcessor()

    def load_site_config(self, site_id: str) -> Optional[Dict]:
        """
        Load site configuration from configs/config.json

        Args:
            site_id: Site identifier or ID

        Returns:
            Site configuration dict or None
        """
        try:
            with open('configs/config.json', 'r') as f:
                configs = json.load(f)

            # Find config by ID or name
            for config in configs:
                if str(config.get('id')) == str(site_id) or config.get('source_name') == site_id:
                    return config

            logger.warning(f"Site config not found: {site_id}")
            return None

        except Exception as e:
            logger.error(f"Error loading site config: {e}")
            return None

    def validate_crawl_request(self, site_config: Dict, options: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate crawl request

        Args:
            site_config: Site configuration
            options: Crawl options

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required config fields
        required_fields = ['start_url', 'domain', 'source_name', 'rules']
        for field in required_fields:
            if field not in site_config:
                return False, f"Missing required config field: {field}"

        # Validate options
        max_pages = options.get('max_pages')
        if max_pages and (not isinstance(max_pages, int) or max_pages <= 0):
            return False, "max_pages must be a positive integer"

        return True, None

    def start_crawl(self, site_id: str, job_id: str, options: Optional[Dict] = None) -> Dict:
        """
        Start a crawl operation

        Args:
            site_id: Site configuration ID
            job_id: CrawlJob UUID
            options: Optional crawl options

        Returns:
            Crawl results/statistics
        """
        options = options or {}

        logger.info(f"Starting crawl for site: {site_id}, job: {job_id}")

        # Load site configuration
        site_config = self.load_site_config(site_id)
        if not site_config:
            raise ValueError(f"Site configuration not found: {site_id}")

        # Validate request
        is_valid, error_msg = self.validate_crawl_request(site_config, options)
        if not is_valid:
            raise ValueError(error_msg)

        # Determine crawler type
        is_dynamic = site_config.get('is_dynamic', False)

        if is_dynamic:
            # TODO: Implement dynamic crawler later
            raise NotImplementedError("Dynamic crawler not yet implemented")
        else:
            crawler = StaticCrawler(site_config, job_id, options)

        # Set up callbacks
        crawler.set_progress_callback(self._on_progress)
        crawler.set_dataset_callback(self._on_dataset_found)
        crawler.set_error_callback(self._on_error)

        # Store context for callbacks
        self.current_job_id = job_id
        self.test_mode = options.get('test_mode', False)
        self.datasets_buffer = []

        # Execute crawl
        try:
            stats = crawler.crawl()

            # Save all buffered datasets
            if not self.test_mode:
                self._save_datasets(self.datasets_buffer)

            logger.info(f"Crawl completed successfully. Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            raise

    def _on_progress(self, stats: Dict, **kwargs):
        """
        Callback for progress updates

        Args:
            stats: Current crawl statistics
        """
        logger.info(f"Progress: Pages={stats['pages_crawled']}, "
                    f"Found={stats['datasets_found']}, "
                    f"Saved={stats['datasets_saved']}")

        # Update CrawlJob in database
        if self.db:
            try:
                from app.models.crawl_job import CrawlJob
                job = CrawlJob.find_by_job_id(self.current_job_id)
                if job:
                    job.update_stats(stats)
                    self.db.commit()
            except Exception as e:
                logger.error(f"Error updating job progress in database: {e}")
                self.db.rollback()

    def _on_dataset_found(self, dataset: Dict):
        """
        Callback when dataset is found

        Args:
            dataset: Dataset dictionary
        """
        logger.info(f"Dataset found: {dataset.get('title')}")

        # In test mode, just log
        if self.test_mode:
            self._save_to_json(dataset)
            return

        # Check for duplicates
        is_duplicate = self._check_duplicate(dataset)

        if is_duplicate:
            logger.info(f"Duplicate skipped: {dataset.get('title')}")
            return

        # Buffer dataset for batch save
        self.datasets_buffer.append(dataset)

        # Save in batches of 10
        if len(self.datasets_buffer) >= 10:
            self._save_datasets(self.datasets_buffer)
            self.datasets_buffer = []

    def _on_error(self, error: Exception, context: Dict):
        """
        Callback when error occurs

        Args:
            error: Exception that occurred
            context: Error context
        """
        logger.error(f"Crawl error: {error}", extra=context)

        # TODO: Log error to database
        # if self.db:
        #     error_log = ErrorLog(
        #         job_id=self.current_job_id,
        #         error_message=str(error),
        #         context=context
        #     )
        #     self.db.add(error_log)
        #     self.db.commit()

    def _check_duplicate(self, dataset: Dict) -> bool:
        """
        Check if dataset already exists

        Args:
            dataset: Dataset to check

        Returns:
            True if duplicate, False otherwise
        """
        # Check for duplicates in database
        if self.db and 'hash' in dataset:
            try:
                from app.models.dataset import Dataset
                existing = Dataset.query.filter_by(
                    content_hash=dataset['hash']
                ).first()
                return existing is not None
            except Exception as e:
                logger.error(f"Error checking for duplicate: {e}")
                return False

        return False

    def _save_datasets(self, datasets: List[Dict]):
        """
        Save datasets to database

        Args:
            datasets: List of dataset dictionaries
        """
        if not datasets:
            return

        logger.info(f"Saving {len(datasets)} datasets to database")

        # Save to database
        if self.db:
            try:
                from app.models.dataset import Dataset
                from app.models.crawl_job import CrawlJob

                # Get the crawl job
                crawl_job = CrawlJob.find_by_job_id(self.current_job_id)

                for dataset_data in datasets:
                    # Create dataset model instance
                    dataset = Dataset(
                        title=dataset_data.get('title'),
                        description=dataset_data.get('description'),
                        url=dataset_data.get('url'),
                        source=dataset_data.get('source'),
                        content_hash=dataset_data.get('hash'),
                        tags=dataset_data.get('tags', []),
                        metadata=dataset_data.get('metadata', {}),
                        crawl_job_id=crawl_job.id if crawl_job else None
                    )
                    self.db.add(dataset)

                self.db.commit()
                logger.info(f"Successfully saved {len(datasets)} datasets to database")

            except Exception as e:
                logger.error(f"Error saving datasets to database: {e}", exc_info=True)
                self.db.rollback()
                # Fallback to JSON
                for dataset in datasets:
                    self._save_to_json(dataset)
        else:
            # No database session, save to JSON for testing
            for dataset in datasets:
                self._save_to_json(dataset)

    def _save_to_json(self, dataset: Dict):
        """
        Save dataset to JSON file (for testing)

        Args:
            dataset: Dataset to save
        """
        try:
            filename = f'data/{self.current_job_id}.json'

            # Create data directory if needed
            import os
            os.makedirs('data', exist_ok=True)

            # Append to file
            with open(filename, 'a') as f:
                json.dump(dataset, f, indent=2)
                f.write(',\n')

            logger.debug(f"Saved to JSON: {filename}")

        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

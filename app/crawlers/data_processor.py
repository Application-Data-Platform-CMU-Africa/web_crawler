"""
Data Processor
Utilities for processing and transforming crawled data
"""
import hashlib
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and transform raw crawled data"""

    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text

        Args:
            text: Raw text string

        Returns:
            Cleaned text or None
        """
        if not text:
            return None

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common unwanted characters
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        return text if text else None

    @staticmethod
    def extract_extension(url: str) -> Optional[str]:
        """
        Extract file extension from URL

        Args:
            url: Dataset URL

        Returns:
            File extension (without dot) or None

        Examples:
            "http://example.com/data.csv" → "csv"
            "http://example.com/download?file=data.xlsx" → "xlsx"
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            path = parsed.path

            # Get extension from path
            if '.' in path:
                extension = path.split('.')[-1].lower()

                # Validate extension (common data formats)
                valid_extensions = [
                    'csv', 'json', 'xml', 'xlsx', 'xls', 'pdf',
                    'zip', 'txt', 'geojson', 'shp',  'kml', 'tsv'
                ]

                if extension in valid_extensions:
                    return extension

            # Try to extract from query parameters
            if 'format=' in url.lower():
                match = re.search(r'format=(\w+)', url.lower())
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            logger.warning(f"Could not extract extension from {url}: {e}")
            return None

    @staticmethod
    def generate_hash(url: str) -> str:
        """
        Generate unique hash for dataset identification (primary key)

        This hash is based on URL only, allowing metadata updates
        without creating duplicate records.

        Args:
            url: Dataset URL (the stable identifier)

        Returns:
            SHA-256 hash string

        Example:
            >>> generate_hash("http://example.com/dataset/population")
            'a3f4b2c1d5e6f7a8b9c0d1e2f3a4b5c6...'
        """
        hash_input = url.lower().strip()
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_content_hash(title: str, description: str = None, tags: List[str] = None) -> str:
        """
        Generate content hash for change detection

        This hash changes when metadata changes, allowing us to detect
        when a dataset has been updated.

        Args:
            title: Dataset title
            description: Dataset description
            tags: List of tags

        Returns:
            SHA-256 hash string

        Example:
            >>> generate_content_hash("Rwanda Pop 2024", "Population data", ["pop"])
            'b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9...'
        """
        # Normalize inputs
        title = (title or "").lower().strip()
        description = (description or "").lower().strip()
        tags_str = ",".join(sorted(tags or [])).lower()

        # Combine for hash
        hash_input = f"{title}|{description}|{tags_str}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def validate_title(title: str) -> bool:
        """
        Validate dataset title

        Args:
            title: Title to validate

        Returns:
            True if valid, False otherwise
        """
        if not title:
            return False

        # Title should be at least 3 characters
        cleaned = DataProcessor.clean_text(title)
        return bool(cleaned and len(cleaned) >= 3)

    @staticmethod
    def process_tags(tags: List[str]) -> List[str]:
        """
        Process and clean tags

        Args:
            tags: List of raw tag strings

        Returns:
            List of cleaned tags
        """
        if not tags:
            return []

        processed = []
        for tag in tags:
            cleaned = DataProcessor.clean_text(tag)
            if cleaned and len(cleaned) <= 50:  # Max tag length
                processed.append(cleaned.lower())

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in processed:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    @staticmethod
    def build_dataset(
        title: str,
        url: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: str = "Unknown",
        crawl_job_id: Optional[str] = None
    ) -> Dict:
        """
        Build standardized dataset object

        Args:
            title: Dataset title
            url: Dataset URL
            description: Dataset description
            tags: List of tags
            source: Data source name
            crawl_job_id: CrawlJob UUID

        Returns:
            Standardized dataset dictionary
        """
        # Clean and validate
        title = DataProcessor.clean_text(title)
        description = DataProcessor.clean_text(description)
        url = url.strip() if url else None
        tags = DataProcessor.process_tags(tags or [])

        if not DataProcessor.validate_title(title):
            raise ValueError(f"Invalid title: {title}")

        if not DataProcessor.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")

        # Extract extension
        extension = DataProcessor.extract_extension(url)

        # Generate hashes
        hash_value = DataProcessor.generate_hash(
            url)  # URL only - for uniqueness
        content_hash = DataProcessor.generate_content_hash(
            title, description, tags)  # For change detection

        # Build dataset
        dataset = {
            'title': title,
            'description': description,
            'extension': extension,
            'original_file_name': title,  # Use title as filename
            'file_references': [url],  # Array of URLs
            'file_size_mb': None,  # Will be set later if needed
            'source': source,
            'tags': tags,
            'is_link': True,  # We're storing external links
            'is_private': False,
            'is_active': True,
            'is_deleted': False,
            'hash': hash_value,  # Primary identifier (URL-based)
            'content_hash': content_hash,  # For detecting content changes
            'crawl_job_id': crawl_job_id
        }

        return dataset

    @staticmethod
    def validate_dataset(dataset: Dict) -> bool:
        """
        Validate dataset object

        Args:
            dataset: Dataset dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'file_references', 'hash', 'source']

        for field in required_fields:
            if field not in dataset or not dataset[field]:
                logger.warning(f"Missing required field: {field}")
                return False

        return True

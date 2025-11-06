"""
Caching utilities for document conversion.

Provides optional caching to speed up repeated conversions of the same documents.
"""

import hashlib
import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from pdf2markdown.core.models import ConversionResult

logger = logging.getLogger(__name__)


class ConversionCache:
    """
    Simple file-based cache for conversion results.

    Caches conversion results based on file hash and configuration hash.
    Useful for repeated conversions of the same documents.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_age_hours: int = 24,
        enabled: bool = True,
    ):
        """
        Initialize conversion cache.

        Args:
            cache_dir: Directory for cache storage (default: system temp)
            max_age_hours: Maximum age of cached results in hours (default: 24)
            enabled: Enable or disable caching (default: True)
        """
        self.enabled = enabled
        self.max_age_hours = max_age_hours

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "pdf2md_cache"

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache initialized at {self.cache_dir}")

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in 64k chunks for large files
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _compute_config_hash(self, config_dict: Dict) -> str:
        """Compute hash of configuration."""
        # Sort keys for consistent hashing
        config_json = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()[:16]

    def _get_cache_key(self, file_path: Path, config_dict: Dict) -> str:
        """Generate cache key from file and configuration."""
        file_hash = self._compute_file_hash(file_path)
        config_hash = self._compute_config_hash(config_dict)
        return f"{file_hash}_{config_hash}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cached result."""
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached result is still valid."""
        if not cache_path.exists():
            return False

        # Check age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        max_age = timedelta(hours=self.max_age_hours)

        if datetime.now() - mtime > max_age:
            logger.debug(f"Cache expired: {cache_path}")
            return False

        return True

    def get(self, file_path: Path, config_dict: Dict) -> Optional[ConversionResult]:
        """
        Get cached conversion result.

        Args:
            file_path: Path to the document file
            config_dict: Configuration dictionary

        Returns:
            Cached ConversionResult or None if not found/expired
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._get_cache_key(file_path, config_dict)
            cache_path = self._get_cache_path(cache_key)

            if not self._is_cache_valid(cache_path):
                return None

            # Load cached result
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct ConversionResult from JSON
            result = ConversionResult.model_validate(data)

            logger.info(f"Cache hit for {file_path.name}")
            return result

        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            return None

    def set(
        self, file_path: Path, config_dict: Dict, result: ConversionResult
    ) -> None:
        """
        Cache conversion result.

        Args:
            file_path: Path to the document file
            config_dict: Configuration dictionary
            result: Conversion result to cache
        """
        if not self.enabled:
            return

        try:
            cache_key = self._get_cache_key(file_path, config_dict)
            cache_path = self._get_cache_path(cache_key)

            # Serialize result to JSON
            data = result.model_dump(mode="json")

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached result for {file_path.name}")

        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    def clear(self) -> int:
        """
        Clear all cached results.

        Returns:
            Number of files deleted
        """
        if not self.enabled:
            return 0

        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1

            logger.info(f"Cleared {count} cached results")
            return count

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        if not self.enabled:
            return 0

        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if not self._is_cache_valid(cache_file):
                    cache_file.unlink()
                    count += 1

            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")

            return count

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return count

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "enabled": True,
                "cache_dir": str(self.cache_dir),
                "num_entries": len(cache_files),
                "total_size_mb": total_size / (1024 * 1024),
                "max_age_hours": self.max_age_hours,
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}

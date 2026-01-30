"""
Caching Module for Knowledge Graph and LLM Responses

Implements in-memory and disk-based caching to improve performance.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached item with metadata."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int


class LRUCache:
    """Thread-safe Least Recently Used cache with TTL support."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: Optional[int] = None):
        """
        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time-to-live in seconds (None = no expiration)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if it exists and is not expired."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # Check expiration
            if self._ttl and (datetime.now() - entry.created_at) > self._ttl:
                logger.debug(f"Cache entry expired: {key}")
                del self._cache[key]
                self._misses += 1
                return None
            
            # Update access metadata
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self._hits += 1
            
            logger.debug(f"Cache hit: {key} (hits={self._hits}, misses={self._misses})")
            return entry.value
    
    def set(self, key: str, value: Any):
        """Add or update a cached value."""
        with self._lock:
            # Calculate size (rough estimate)
            size = len(str(value).encode('utf-8'))
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=0,
                size_bytes=size
            )
            
            # Evict if necessary
            if key not in self._cache and len(self._cache) >= self._max_size:
                self._evict_lru()
            
            self._cache[key] = entry
            logger.debug(f"Cache set: {key} ({size} bytes)")
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._cache:
            return
        
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].accessed_at
        )
        
        logger.debug(f"Evicting LRU entry: {lru_key}")
        del self._cache[lru_key]
    
    def clear(self):
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Cache cleared")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            total_size = sum(e.size_bytes for e in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_size_bytes": total_size,
                "ttl_seconds": self._ttl.total_seconds() if self._ttl else None
            }


class KnowledgeGraphCache:
    """Specialized cache for knowledge graphs."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Args:
            cache_dir: Directory for disk cache (None = memory only)
        """
        self._memory_cache = LRUCache(max_size=10, ttl_seconds=3600)  # 1 hour TTL
        self._cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _compute_key(self, kg_path: str) -> str:
        """Compute cache key from KG path and file mtime."""
        path = Path(kg_path)
        if not path.exists():
            return hashlib.sha256(kg_path.encode()).hexdigest()
        
        # Include modification time to invalidate cache on file changes
        mtime = path.stat().st_mtime
        key_str = f"{kg_path}:{mtime}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, kg_path: str) -> Optional[Any]:
        """Get cached knowledge graph."""
        key = self._compute_key(kg_path)
        
        # Try memory cache first
        cached = self._memory_cache.get(key)
        if cached:
            logger.info(f"KG cache hit (memory): {kg_path}")
            return cached
        
        # Try disk cache
        if self._cache_dir:
            cache_file = self._cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    logger.info(f"KG cache hit (disk): {kg_path}")
                    # Store in memory for faster access
                    self._memory_cache.set(key, data)
                    return data
                except Exception as e:
                    logger.error(f"Failed to load from disk cache: {e}")
        
        logger.info(f"KG cache miss: {kg_path}")
        return None
    
    def set(self, kg_path: str, value: Any):
        """Cache knowledge graph."""
        key = self._compute_key(kg_path)
        
        # Always store in memory
        self._memory_cache.set(key, value)
        
        # Store on disk if enabled
        if self._cache_dir:
            cache_file = self._cache_dir / f"{key}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump(value, f, indent=2)
                logger.info(f"KG cached to disk: {cache_file}")
            except Exception as e:
                logger.error(f"Failed to write disk cache: {e}")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return self._memory_cache.stats()


class LLMResponseCache:
    """Cache for LLM responses to avoid repeated API calls."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 86400):
        """
        Args:
            max_size: Maximum number of cached responses
            ttl_seconds: Time-to-live (default 24 hours)
        """
        self._cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
    
    def _compute_key(self, prompt: str, state: dict, model: str) -> str:
        """Compute cache key from prompt, state, and model."""
        # Create deterministic string representation
        state_str = json.dumps(state, sort_keys=True)
        key_str = f"{prompt}:{state_str}:{model}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, prompt: str, state: dict, model: str) -> Optional[dict]:
        """Get cached LLM response."""
        key = self._compute_key(prompt, state, model)
        cached = self._cache.get(key)
        
        if cached:
            logger.info(f"LLM response cache hit for prompt: {prompt}")
        
        return cached
    
    def set(self, prompt: str, state: dict, model: str, response: dict):
        """Cache LLM response."""
        key = self._compute_key(prompt, state, model)
        self._cache.set(key, response)
        logger.debug(f"Cached LLM response for prompt: {prompt}")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return self._cache.stats()


# Global cache instances
_kg_cache: Optional[KnowledgeGraphCache] = None
_llm_cache: Optional[LLMResponseCache] = None


def get_kg_cache(cache_dir: Optional[Path] = None) -> KnowledgeGraphCache:
    """Get the global KG cache instance."""
    global _kg_cache
    if _kg_cache is None:
        _kg_cache = KnowledgeGraphCache(cache_dir)
    return _kg_cache


def get_llm_cache() -> LLMResponseCache:
    """Get the global LLM response cache instance."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMResponseCache()
    return _llm_cache


def clear_all_caches():
    """Clear all caches."""
    global _kg_cache, _llm_cache
    
    if _kg_cache:
        _kg_cache._memory_cache.clear()
    
    if _llm_cache:
        _llm_cache._cache.clear()
    
    logger.info("All caches cleared")

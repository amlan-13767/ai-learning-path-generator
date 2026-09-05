"""
Resource Validator Module
Validates external resource URLs (YouTube videos, articles, courses, etc.)
to ensure they are accessible before presenting them to users.

Features:
- Async HTTP validation with retry logic
- Platform-specific validators (YouTube, Coursera, etc.)
- Confidence scoring
- Caching to avoid redundant checks
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class ResourceValidator:
    """
    Validates external resource URLs with platform-specific logic.
    """
    
    def __init__(self, cache_ttl_hours: int = 24, max_retries: int = 2):
        """
        Initialize the resource validator.
        
        Args:
            cache_ttl_hours: How long to cache validation results (default: 24 hours)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.cache_ttl_hours = cache_ttl_hours
        self.max_retries = max_retries
        self.validation_cache: Dict[str, Dict] = {}
        
        # Platform-specific patterns
        self.youtube_pattern = re.compile(
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
        )
        self.coursera_pattern = re.compile(r'coursera\.org/learn/([^/]+)')
        self.udemy_pattern = re.compile(r'udemy\.com/course/([^/]+)')
        
    async def validate_url(
        self, 
        url: str, 
        timeout: int = 10
    ) -> Dict[str, any]:
        """
        Validate a single URL with platform-specific logic.
        
        Args:
            url: The URL to validate
            timeout: Request timeout in seconds
            
        Returns:
            Dict with validation results:
            {
                'url': str,
                'valid': bool,
                'status_code': int,
                'platform': str,
                'checked_at': str (ISO format),
                'error': Optional[str],
                'confidence': float (0.0 to 1.0)
            }
        """
        # Check cache first
        cached = self._get_from_cache(url)
        if cached:
            logger.info(f"Using cached validation for: {url}")
            return cached
        
        # Determine platform
        platform = self._detect_platform(url)
        
        # Use platform-specific validator if available
        if platform == 'youtube':
            result = await self._validate_youtube(url, timeout)
        elif platform == 'coursera':
            result = await self._validate_coursera(url, timeout)
        elif platform == 'udemy':
            result = await self._validate_udemy(url, timeout)
        else:
            result = await self._validate_generic(url, timeout)
        
        # Cache the result
        self._add_to_cache(url, result)
        
        return result
    
    async def validate_resources(
        self, 
        resources: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """
        Validate multiple resources concurrently.
        
        Args:
            resources: List of resource dicts with 'url' and 'title' keys
            
        Returns:
            List of validation results with original resource info
        """
        tasks = []
        for resource in resources:
            url = resource.get('url', '')
            if url:
                tasks.append(self.validate_url(url))
        
        # Run all validations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine with original resource info
        validated_resources = []
        for i, resource in enumerate(resources):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"Validation error for {resource.get('url')}: {result}")
                    result = {
                        'url': resource.get('url'),
                        'valid': False,
                        'error': str(result),
                        'confidence': 0.0,
                        'checked_at': datetime.utcnow().isoformat()
                    }
                
                validated_resources.append({
                    **resource,
                    'validation': result
                })
            else:
                validated_resources.append(resource)
        
        return validated_resources
    
    async def _validate_youtube(
        self, 
        url: str, 
        timeout: int
    ) -> Dict[str, any]:
        """
        Validate YouTube video using oEmbed API.
        
        Args:
            url: YouTube video URL
            timeout: Request timeout
            
        Returns:
            Validation result dict
        """
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return {
                'url': url,
                'valid': False,
                'platform': 'youtube',
                'error': 'Invalid YouTube URL format',
                'confidence': 0.0,
                'checked_at': datetime.utcnow().isoformat()
            }
        
        # Use YouTube oEmbed API (no API key required)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(oembed_url, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'url': url,
                            'valid': True,
                            'status_code': 200,
                            'platform': 'youtube',
                            'video_id': video_id,
                            'title': data.get('title'),
                            'author': data.get('author_name'),
                            'confidence': 1.0,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 404:
                        return {
                            'url': url,
                            'valid': False,
                            'status_code': 404,
                            'platform': 'youtube',
                            'error': 'Video not found or unavailable',
                            'confidence': 0.0,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'url': url,
                            'valid': False,
                            'status_code': response.status,
                            'platform': 'youtube',
                            'error': f'Unexpected status: {response.status}',
                            'confidence': 0.3,
                            'checked_at': datetime.utcnow().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'url': url,
                'valid': False,
                'platform': 'youtube',
                'error': 'Request timeout',
                'confidence': 0.5,  # Might be temporary
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"YouTube validation error for {url}: {e}")
            return {
                'url': url,
                'valid': False,
                'platform': 'youtube',
                'error': str(e),
                'confidence': 0.3,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def _validate_coursera(
        self, 
        url: str, 
        timeout: int
    ) -> Dict[str, any]:
        """
        Validate Coursera course URL.
        
        Args:
            url: Coursera course URL
            timeout: Request timeout
            
        Returns:
            Validation result dict
        """
        return await self._validate_generic(url, timeout, platform='coursera')
    
    async def _validate_udemy(
        self, 
        url: str, 
        timeout: int
    ) -> Dict[str, any]:
        """
        Validate Udemy course URL.
        
        Args:
            url: Udemy course URL
            timeout: Request timeout
            
        Returns:
            Validation result dict
        """
        return await self._validate_generic(url, timeout, platform='udemy')
    
    async def _validate_generic(
        self, 
        url: str, 
        timeout: int,
        platform: str = 'generic'
    ) -> Dict[str, any]:
        """
        Generic URL validation using HEAD request with fallback to GET.
        
        Args:
            url: URL to validate
            timeout: Request timeout
            platform: Platform identifier
            
        Returns:
            Validation result dict
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    # Try HEAD first (faster)
                    async with session.head(
                        url, 
                        timeout=timeout,
                        allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            return {
                                'url': url,
                                'valid': True,
                                'status_code': 200,
                                'platform': platform,
                                'confidence': 1.0,
                                'checked_at': datetime.utcnow().isoformat()
                            }
                        elif response.status == 405:  # Method not allowed, try GET
                            async with session.get(
                                url, 
                                timeout=timeout,
                                allow_redirects=True
                            ) as get_response:
                                valid = 200 <= get_response.status < 400
                                return {
                                    'url': url,
                                    'valid': valid,
                                    'status_code': get_response.status,
                                    'platform': platform,
                                    'confidence': 1.0 if valid else 0.0,
                                    'checked_at': datetime.utcnow().isoformat(),
                                    'error': None if valid else f'HTTP {get_response.status}'
                                }
                        elif response.status == 429:  # Rate limited
                            retries += 1
                            await asyncio.sleep(2 ** retries)  # Exponential backoff
                            continue
                        else:
                            return {
                                'url': url,
                                'valid': False,
                                'status_code': response.status,
                                'platform': platform,
                                'error': f'HTTP {response.status}',
                                'confidence': 0.0,
                                'checked_at': datetime.utcnow().isoformat()
                            }
            except asyncio.TimeoutError:
                last_error = 'Request timeout'
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                last_error = f'Client error: {str(e)}'
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(1)
            except Exception as e:
                last_error = str(e)
                break
        
        # All retries exhausted
        return {
            'url': url,
            'valid': False,
            'platform': platform,
            'error': last_error or 'Unknown error',
            'confidence': 0.3,  # Might be temporary
            'checked_at': datetime.utcnow().isoformat()
        }
    
    def _detect_platform(self, url: str) -> str:
        """
        Detect the platform from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Platform identifier string
        """
        if self.youtube_pattern.search(url):
            return 'youtube'
        elif self.coursera_pattern.search(url):
            return 'coursera'
        elif self.udemy_pattern.search(url):
            return 'udemy'
        else:
            return 'generic'
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None
        """
        match = self.youtube_pattern.search(url)
        return match.group(1) if match else None
    
    def _get_from_cache(self, url: str) -> Optional[Dict]:
        """
        Get validation result from cache if not expired.
        
        Args:
            url: URL to check
            
        Returns:
            Cached result or None
        """
        if url in self.validation_cache:
            cached = self.validation_cache[url]
            checked_at = datetime.fromisoformat(cached['checked_at'])
            age = datetime.utcnow() - checked_at
            
            if age < timedelta(hours=self.cache_ttl_hours):
                return cached
            else:
                # Expired, remove from cache
                del self.validation_cache[url]
        
        return None
    
    def _add_to_cache(self, url: str, result: Dict):
        """
        Add validation result to cache.
        
        Args:
            url: URL key
            result: Validation result
        """
        self.validation_cache[url] = result
    
    def get_validation_stats(self) -> Dict[str, any]:
        """
        Get statistics about validation results.
        
        Returns:
            Dict with validation statistics
        """
        total = len(self.validation_cache)
        if total == 0:
            return {
                'total_checked': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'success_rate': 0.0
            }
        
        valid_count = sum(1 for v in self.validation_cache.values() if v.get('valid'))
        invalid_count = total - valid_count
        
        return {
            'total_checked': total,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'success_rate': round(valid_count / total * 100, 2)
        }


# Synchronous wrapper for easy integration
def validate_resources_sync(resources: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """
    Synchronous wrapper for validate_resources.
    
    Args:
        resources: List of resource dicts with 'url' and 'title' keys
        
    Returns:
        List of validated resources
    """
    validator = ResourceValidator()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(validator.validate_resources(resources))

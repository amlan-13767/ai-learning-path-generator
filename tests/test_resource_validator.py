"""
Unit tests for the Resource Validator module.
Tests validation logic with mocked HTTP responses.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.utils.resource_validator import ResourceValidator


@pytest.fixture
def validator():
    """Create a ResourceValidator instance for testing."""
    return ResourceValidator(cache_ttl_hours=1, max_retries=1)


@pytest.mark.asyncio
async def test_validate_youtube_valid(validator):
    """Test YouTube validation with a valid video."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        'title': 'Test Video',
        'author_name': 'Test Author'
    })
    
    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        result = await validator.validate_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        
        assert result['valid'] is True
        assert result['platform'] == 'youtube'
        assert result['confidence'] == 1.0
        assert 'title' in result


@pytest.mark.asyncio
async def test_validate_youtube_invalid(validator):
    """Test YouTube validation with an invalid/deleted video."""
    mock_response = AsyncMock()
    mock_response.status = 404
    
    with patch('aiohttp.ClientSession.get', return_value=mock_response):
        result = await validator.validate_url('https://www.youtube.com/watch?v=invalid123')
        
        assert result['valid'] is False
        assert result['platform'] == 'youtube'
        assert result['confidence'] == 0.0
        assert 'error' in result


@pytest.mark.asyncio
async def test_validate_generic_url_valid(validator):
    """Test generic URL validation with a valid response."""
    mock_response = AsyncMock()
    mock_response.status = 200
    
    with patch('aiohttp.ClientSession.head', return_value=mock_response):
        result = await validator.validate_url('https://example.com/article')
        
        assert result['valid'] is True
        assert result['status_code'] == 200
        assert result['confidence'] == 1.0


@pytest.mark.asyncio
async def test_validate_generic_url_404(validator):
    """Test generic URL validation with a 404 response."""
    mock_response = AsyncMock()
    mock_response.status = 404
    
    with patch('aiohttp.ClientSession.head', return_value=mock_response):
        result = await validator.validate_url('https://example.com/notfound')
        
        assert result['valid'] is False
        assert result['status_code'] == 404
        assert result['confidence'] == 0.0


@pytest.mark.asyncio
async def test_validate_generic_url_redirect(validator):
    """Test generic URL validation with redirects."""
    mock_response = AsyncMock()
    mock_response.status = 200
    
    with patch('aiohttp.ClientSession.head', return_value=mock_response):
        result = await validator.validate_url('https://bit.ly/shortened')
        
        assert result['valid'] is True
        assert result['status_code'] == 200


@pytest.mark.asyncio
async def test_validate_url_timeout(validator):
    """Test URL validation with timeout."""
    with patch('aiohttp.ClientSession.head', side_effect=asyncio.TimeoutError):
        result = await validator.validate_url('https://slow-site.com')
        
        assert result['valid'] is False
        assert 'timeout' in result['error'].lower()
        assert result['confidence'] == 0.3


@pytest.mark.asyncio
async def test_validate_url_rate_limit_retry(validator):
    """Test URL validation with rate limiting and retry."""
    # First call returns 429, second call returns 200
    mock_response_429 = AsyncMock()
    mock_response_429.status = 429
    
    mock_response_200 = AsyncMock()
    mock_response_200.status = 200
    
    with patch('aiohttp.ClientSession.head', side_effect=[mock_response_429, mock_response_200]):
        result = await validator.validate_url('https://rate-limited.com')
        
        # Should succeed after retry
        assert result['valid'] is True
        assert result['status_code'] == 200


@pytest.mark.asyncio
async def test_validate_multiple_resources(validator):
    """Test validating multiple resources concurrently."""
    resources = [
        {'url': 'https://example.com/1', 'title': 'Resource 1'},
        {'url': 'https://example.com/2', 'title': 'Resource 2'},
        {'url': 'https://example.com/3', 'title': 'Resource 3'},
    ]
    
    mock_response = AsyncMock()
    mock_response.status = 200
    
    with patch('aiohttp.ClientSession.head', return_value=mock_response):
        results = await validator.validate_resources(resources)
        
        assert len(results) == 3
        for result in results:
            assert 'validation' in result
            assert result['validation']['valid'] is True


@pytest.mark.asyncio
async def test_cache_functionality(validator):
    """Test that validation results are cached."""
    url = 'https://example.com/cached'
    
    mock_response = AsyncMock()
    mock_response.status = 200
    
    with patch('aiohttp.ClientSession.head', return_value=mock_response) as mock_head:
        # First call - should hit the network
        result1 = await validator.validate_url(url)
        assert mock_head.call_count == 1
        
        # Second call - should use cache
        result2 = await validator.validate_url(url)
        assert mock_head.call_count == 1  # No additional call
        
        # Results should be identical
        assert result1 == result2


def test_detect_platform(validator):
    """Test platform detection from URLs."""
    assert validator._detect_platform('https://www.youtube.com/watch?v=abc123') == 'youtube'
    assert validator._detect_platform('https://youtu.be/abc123') == 'youtube'
    assert validator._detect_platform('https://www.coursera.org/learn/machine-learning') == 'coursera'
    assert validator._detect_platform('https://www.udemy.com/course/python-bootcamp') == 'udemy'
    assert validator._detect_platform('https://example.com/article') == 'generic'


def test_extract_youtube_id(validator):
    """Test YouTube video ID extraction."""
    assert validator._extract_youtube_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ') == 'dQw4w9WgXcQ'
    assert validator._extract_youtube_id('https://youtu.be/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'
    assert validator._extract_youtube_id('https://www.youtube.com/embed/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'
    assert validator._extract_youtube_id('https://example.com') is None


def test_validation_stats(validator):
    """Test validation statistics calculation."""
    # Add some mock data to cache
    validator.validation_cache = {
        'url1': {'valid': True, 'checked_at': '2024-01-01T00:00:00'},
        'url2': {'valid': True, 'checked_at': '2024-01-01T00:00:00'},
        'url3': {'valid': False, 'checked_at': '2024-01-01T00:00:00'},
    }
    
    stats = validator.get_validation_stats()
    
    assert stats['total_checked'] == 3
    assert stats['valid_count'] == 2
    assert stats['invalid_count'] == 1
    assert stats['success_rate'] == 66.67


@pytest.mark.asyncio
async def test_validate_url_with_exception(validator):
    """Test URL validation when an exception occurs."""
    with patch('aiohttp.ClientSession.head', side_effect=Exception('Network error')):
        result = await validator.validate_url('https://error-site.com')
        
        assert result['valid'] is False
        assert 'error' in result
        assert result['confidence'] == 0.3


@pytest.mark.asyncio
async def test_validate_resources_with_exception(validator):
    """Test validating resources when one fails with exception."""
    resources = [
        {'url': 'https://good.com', 'title': 'Good Resource'},
        {'url': 'https://bad.com', 'title': 'Bad Resource'},
    ]
    
    async def mock_validate(url):
        if 'bad' in url:
            raise Exception('Validation failed')
        return {'url': url, 'valid': True, 'confidence': 1.0}
    
    with patch.object(validator, 'validate_url', side_effect=mock_validate):
        results = await validator.validate_resources(resources)
        
        assert len(results) == 2
        assert results[0]['validation']['valid'] is True
        assert results[1]['validation']['valid'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

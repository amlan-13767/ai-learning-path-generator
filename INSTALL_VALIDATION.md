# Quick Installation Guide - Resource Validation System

## Step 1: Install Dependencies

```bash
pip install aiohttp>=3.9.0 pytest-asyncio>=0.21.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 2: Verify Installation

Test the validator:

```python
python -c "from src.utils.resource_validator import ResourceValidator; print('✅ Validator installed successfully')"
```

## Step 3: Test with a Sample URL

```bash
python -m tools.validate_resources --url https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Expected output:
```
============================================================
🔍 Validating URL
============================================================

URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Valid: ✅ Yes
Status Code: 200
Platform: youtube
Confidence: 1.00
Title: Rick Astley - Never Gonna Give You Up (Official Video)
Author: Rick Astley

============================================================
```

## Step 4: Run Tests

```bash
pytest tests/test_resource_validator.py -v
```

Expected output:
```
tests/test_resource_validator.py::test_validate_youtube_valid PASSED
tests/test_resource_validator.py::test_validate_youtube_invalid PASSED
tests/test_resource_validator.py::test_validate_generic_url_valid PASSED
...
============ 15 passed in 2.34s ============
```

## Step 5: Generate a Learning Path (with validation)

```python
from src.learning_path import LearningPathGenerator

generator = LearningPathGenerator()
path = generator.generate_path(
    topic="Python Programming",
    expertise_level="beginner",
    learning_style="hands-on",
    time_commitment="moderate"
)

print(f"Generated path with {len(path.milestones)} milestones")
print(f"All resources validated automatically!")
```

## Step 6: Validate an Existing Learning Path

```bash
# Find a learning path JSON file
python -m tools.validate_resources learning_paths/your_path.json
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'aiohttp'`

**Solution:**
```bash
pip install aiohttp
```

### Issue: `ImportError: cannot import name 'ResourceValidator'`

**Solution:** Make sure you're running from the project root directory.

### Issue: Tests fail with async errors

**Solution:**
```bash
pip install pytest-asyncio
```

## Quick Reference

### Validate a single URL
```bash
python -m tools.validate_resources --url <URL>
```

### Validate a learning path
```bash
python -m tools.validate_resources <path_to_json>
```

### Validate multiple URLs
```bash
# Create urls.txt with one URL per line
python -m tools.validate_resources --batch urls.txt
```

### Run tests
```bash
pytest tests/test_resource_validator.py -v
```

## Configuration

Edit `src/utils/resource_validator.py` to adjust:

- `cache_ttl_hours`: How long to cache results (default: 24)
- `max_retries`: Retry attempts for failed requests (default: 2)
- `timeout`: Request timeout in seconds (default: 10)

## Next Steps

1. ✅ Generate a learning path and verify resources are validated
2. ✅ Run the CLI tool on existing learning paths
3. ✅ Review validation reports
4. ✅ Monitor validation stats in logs

## Support

See full documentation: `docs/RESOURCE_VALIDATION.md`

---

**Status**: ✅ Ready to Use

# Curated Sources Integration - Fixed

## Problem
The system was using Perplexity to search for resources, but it was:
1. Hallucinating fake YouTube URLs that returned 404s
2. Finding articles behind paywalls (HTTP 403 errors)
3. Not strictly adhering to the curated sources database

## Solution Implemented

### 1. Enhanced Prompt Instructions (`src/ml/resource_search.py`)
- Made the prompt **much more explicit** about using ONLY curated sources
- Added clear forbidden/required rules
- Emphasized that URLs must be REAL and from approved channels only

### 2. Better Logging (`src/learning_path.py`)
- Now shows which curated sources are being used for each topic
- Displays YouTube channels and websites being searched
- Warns when no curated sources are found

### 3. How It Works Now

When you generate a learning path for "Natural Language Processing":

1. **Lookup**: System checks `src/data/skills_database.py` for "Natural Language Processing"
2. **Extract Sources**: Gets curated sources based on expertise level:
   - **Beginner**: Sentdex, freeCodeCamp.org, Krish Naik (YouTube) + Coursera, NLTK.org, Spacy.io (Websites)
   - **Intermediate**: DeepLearningAI, Stanford NLP, Jay Alammar + HuggingFace.co, TowardsDataScience
   - **Advanced**: Yannic Kilcher, AI Coffee Break, Stanford CS224N + ArXiv.org, ACL Anthology

3. **Search**: Perplexity is instructed to search ONLY within those channels/websites
4. **Validate**: URLs are validated to ensure they're real and accessible

## Expected Logs

You should now see:
```
📚 Using curated sources:
   YouTube: DeepLearningAI, Stanford NLP, Jay Alammar
   Websites: HuggingFace.co, TowardsDataScience, Papers with Code
🔍 Searching with Perplexity...
✓ Found 5 specific resources from trusted sources
```

## Database Structure

The curated sources are in `src/data/skills_database.py`:

```python
"Natural Language Processing": {
    "resources": {
        "beginner": {
            "youtube": ["Sentdex", "freeCodeCamp.org", "Krish Naik"],
            "websites": ["Coursera", "NLTK.org", "Spacy.io"]
        },
        "intermediate": {
            "youtube": ["DeepLearningAI", "Stanford NLP", "Jay Alammar"],
            "websites": ["HuggingFace.co", "TowardsDataScience", "Papers with Code"]
        },
        "advanced": {
            "youtube": ["Yannic Kilcher", "AI Coffee Break", "Stanford CS224N"],
            "websites": ["ArXiv.org", "ACL Anthology", "OpenAI Research"]
        }
    }
}
```

## Adding New Topics

To add curated sources for a new topic:

1. Open `src/data/skills_database.py`
2. Add a new entry with the topic name
3. Include `resources` with `beginner`, `intermediate`, and `advanced` levels
4. List YouTube channels and websites for each level

Example:
```python
"Your New Topic": {
    "category": "Your Category",
    "salary_range": "$X - $Y",
    "resources": {
        "beginner": {
            "youtube": ["Channel1", "Channel2"],
            "websites": ["website1.com", "website2.com"]
        },
        # ... intermediate and advanced
    }
}
```

## Testing

Test the changes by:
1. Restart your backend worker
2. Generate a new learning path for "Natural Language Processing" (intermediate level)
3. Check the logs for the curated sources being used
4. Verify that resources are from the approved channels

## Notes

- The system still validates all URLs to ensure they're accessible
- If a curated source returns invalid URLs, they'll be filtered out
- If all curated sources fail, the system falls back to general search
- Perplexity may still occasionally hallucinate - the validation step catches this

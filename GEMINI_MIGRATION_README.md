# Gemini Migration README

## Overview

The application AI migration changed active text generation from OpenAI to Google Gemini while preserving the existing React, Flask, PostgreSQL, Redis/RQ, and ChromaDB architecture.

Target architecture:

```text
React + Vite + Tailwind
        |
        v
Flask REST API
        |
        +---- PostgreSQL
        +---- Redis / RQ
        +---- ChromaDB
        |       |
        |       +---- Sentence Transformers embeddings
        |
        +---- Gemini REST API
        |
        +---- Perplexity REST API for web-search features
```

## Gemini Configuration

Required server-side environment variables:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

The real `.env` file is loaded locally and must never be committed. Gemini credentials are not sent to React, returned through API responses, or logged.

The runtime environment resolved the configured model as `gemini-3.8-flash`. The application keeps model selection configurable through `GEMINI_MODEL`.

## Gemini Client

The reusable REST client is located at:

```text
src/ml/gemini_client.py
```

It uses the existing `requests` package and calls the Gemini `generateContent` endpoint. It handles:

- Missing API keys
- Empty prompts
- Network failures
- Timeouts
- HTTP 400, 401, 403, 429, and 5xx responses
- Malformed response JSON
- Empty model output
- Safe error messages without credentials

All active text-generation components reuse this client.

## Migrated Components

### Learning-path generation

The existing flow remains:

```text
React
  -> POST /api/generate
  -> Redis/RQ job
  -> worker/tasks.py
  -> LearningPathGenerator
  -> ModelOrchestrator
  -> Gemini
  -> Pydantic v1 validation
  -> Redis result
  -> PostgreSQL persistence
```

The learning-path algorithm, prompts, milestones, resource enrichment, status polling, and result persistence were preserved.

Malformed or incomplete structured responses are rejected instead of generating fake fallback learning paths.

### Chat

The authenticated `/api/ask` flow remains the primary frontend chat path and continues to enforce learning-path ownership.

The legacy `/chatbot_query` endpoint:

- Is not called by the React frontend.
- Now requires Flask authentication.
- Verifies learning-path ownership when a path ID is provided.
- Uses Gemini instead of OpenAI.

### RAG helpers

The following active components now use Gemini:

- `src/ml/query_rewriter.py`
- `src/ml/context_compressor.py`

Their local fallback behavior returns the original query or document instead of calling OpenAI.

## Perplexity

Perplexity functionality was preserved.

Updated modules:

- `src/ml/job_market.py`
- `src/ml/resource_search.py`

They now use direct `requests` calls to:

```text
https://api.perplexity.ai/chat/completions
```

The existing `PERPLEXITY_API_KEY`, models, prompts, parsing, and placeholder fallbacks remain. OpenAI fallback generation was removed.

## Sentence Transformer Embeddings

The selected local model is:

```text
all-MiniLM-L6-v2
```

Verified dimension:

```text
384
```

The shared embedding implementation is:

```text
src/ml/local_embeddings.py
```

New configurable Chroma collection names are:

```text
learning_resources_st
learning_paths_st
```

The original collections remain untouched:

```text
learning_resources
learning_paths
```

The original FAISS artifacts also remain untouched:

```text
vector_db/index.faiss
vector_db/index.pkl
```

The original FAISS index contains two 1536-dimensional vectors and was not overwritten.

## Opt-In Indexing

The migration indexer is:

```text
src/data/index_sentence_transformers.py
```

It does not run during application startup. It reads the available source files from:

```text
vector_db/documents/
```

Existing document IDs are skipped and collections are never deleted.

Example command:

```powershell
.\.venv\Scripts\python.exe -c "from src.data.index_sentence_transformers import index_documents; print(index_documents())"
```

## Semantic Cache

`src/utils/semantic_cache.py` now uses the same Sentence Transformer model for query embeddings.

Existing Redis cache entries created with old OpenAI 1536-dimensional vectors are not treated as compatible with the new 384-dimensional vectors. They will naturally miss under the new embedding implementation and can expire normally.

## Dependency Changes

Removed from dependency metadata:

- `openai`
- `langchain-openai`

Preserved versions:

- `pydantic==1.10.18`
- `langchain==0.0.267`
- `chromadb==0.3.29`

No Gemini SDK was installed. The migration uses `requests` directly.

## Remaining OpenAI References

Only legacy or dead references remain:

- `src/direct_openai.py`
- `src/utils/openai_compat.py`
- `test_direct_openai.py`
- A commented reference in `web_app/app.py`

No active application path uses OpenAI for text generation, chat, Perplexity, embeddings, or semantic caching.

## Verification Results

Passed:

- Python compilation for `src`, `web_app`, `worker`, and `backend`
- Pylance diagnostics for changed files
- Gemini mocked success and error handling
- Real Gemini REST connectivity
- Structured JSON parsing and malformed-output rejection
- Perplexity mocked request flow
- Sentence Transformer import
- Sentence Transformer 384-dimensional embedding generation
- Redis import
- RQ import
- ChromaDB import
- Gemini client import
- Frontend ESLint
- Frontend production build
- Focused regression tests: `6 passed`

Frontend build warnings concern stale Browserslist metadata only.

## Known Environment Blockers

ChromaDB client initialization requires `hnswlib`. The current Windows environment does not have Microsoft Visual C++ 14.0+ available, so installing `hnswlib` failed during wheel compilation.

The failure was:

```text
Microsoft Visual C++ 14.0 or greater is required
```

The application imports ChromaDB successfully, but full Chroma client initialization, Sentence Transformer indexing, and end-to-end Chroma retrieval remain unverified until the prerequisite is installed.

### Manual prerequisite

Install Microsoft C++ Build Tools with MSVC 14.0 or newer, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install hnswlib
```

After that, run the opt-in indexing command above and verify the new collections before using them in production.

## Authentication and Data Safety

The migration preserves:

- Flask-Login
- Google OAuth
- PostgreSQL models
- Server-side path ownership checks
- Redis/RQ job ownership checks
- Existing FAISS files
- Existing Chroma collection names
- Existing user and learning-path data

No Git operations were performed during the migration.

## Frontend Impact

No frontend source changes were required. The React application continues to use the existing backend API contracts and never calls Gemini directly.

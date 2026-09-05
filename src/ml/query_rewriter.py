"""
Query rewriting module for improving retrieval with vague or ambiguous queries.

Query rewriting uses an LLM to expand and clarify user queries before retrieval,
significantly improving results for short or unclear questions.
"""
import os
from typing import Optional
from openai import OpenAI


class QueryRewriter:
    """
    LLM-based query rewriter for improving retrieval.
    
    Transforms vague queries like "ML" into detailed queries like
    "machine learning algorithms including supervised and unsupervised learning".
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 100
    ):
        """
        Initialize query rewriter.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for rewriting (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens for rewritten query
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ Query rewriter initialized (model: {model})")
        else:
            print("❌ OPENAI_API_KEY not set. Query rewriting disabled.")
    
    def rewrite(self, query: str) -> str:
        """
        Rewrite a query to be more detailed and specific.
        
        Args:
            query: Original user query
            
        Returns:
            Rewritten, expanded query
        """
        if not self.client:
            # No rewriting available, return original
            return query
        
        # Skip rewriting for already detailed queries (>50 chars)
        if len(query) > 50:
            return query
        
        try:
            # Construct rewriting prompt
            prompt = f"""You are a query expansion expert. Your task is to rewrite the following search query to be more detailed and specific for a vector database search.

Original query: "{query}"

Rewrite this query to:
1. Expand abbreviations (e.g., "ML" → "machine learning")
2. Add relevant context and related terms
3. Make it more specific and searchable
4. Keep it concise (1-2 sentences max)

Rewritten query:"""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that expands search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=self.max_tokens
            )
            
            rewritten_query = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            rewritten_query = rewritten_query.strip('"\'')
            
            print(f"🔄 Query rewritten: '{query}' → '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            print(f"⚠️  Query rewriting failed: {e}. Using original query.")
            return query
    
    def rewrite_if_needed(self, query: str, threshold: int = 20) -> str:
        """
        Rewrite query only if it's shorter than threshold.
        
        Args:
            query: Original query
            threshold: Character threshold for rewriting
            
        Returns:
            Original or rewritten query
        """
        if len(query) < threshold:
            return self.rewrite(query)
        return query

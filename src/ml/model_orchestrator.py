"""
Model orchestrator for the AI Learning Path Generator.
Handles interactions with language models and embeddings.
"""
from typing import List, Dict, Any, Optional, Union, TypeVar, Type
import json
import os

# Using Pydantic v1
import pydantic
from pydantic import BaseModel as PydanticBaseModel

# Import from langchain (older version compatible with Pydantic v1)
# For type hints
T = TypeVar('T', bound='BaseModel')

class BaseModel(PydanticBaseModel):
    """Base model using Pydantic v1."""
    class Config:
        arbitrary_types_allowed = True

# We'll use only OpenAI for now to make the application work
# Both providers will default to using OpenAI

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain

from src.utils.config import DEFAULT_PROVIDER, GEMINI_MODEL, MAX_TOKENS, TEMPERATURE
from src.ml.gemini_client import GeminiClient

# Import token optimization utilities for cost savings
from src.utils.helpers import optimize_prompt, count_tokens, estimate_api_cost

# Import caching utilities to avoid repeated API calls
from src.utils.cache import cache, cached

# Import observability utilities for LLM monitoring
from src.utils.observability import get_observability_manager, estimate_cost

class ModelOrchestrator:
    """
    Manages AI model interactions with RAG capabilities.
    """
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        print("--- ModelOrchestrator.__init__ started ---")
        """
        Initialize the model orchestrator with RAG capabilities.
        
        Args:
            api_key: Optional API key (if not provided, will use from environment)
            provider: Optional provider name ('openai' or 'deepseek')
        """
        self.provider = provider.lower() if provider else DEFAULT_PROVIDER
        self.context = []
        self.goal = None
        self.planning_enabled = True
        self.memory = []
        
        if self.provider != 'gemini':
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'gemini'.")

        self.api_key = api_key
        self.gemini_client = GeminiClient(api_key=api_key, model=GEMINI_MODEL)
            
        # Track current model name
        self.model_name = GEMINI_MODEL
        
        # Initialize observability manager
        self.obs_manager = get_observability_manager()

        print(f"--- ModelOrchestrator.__init__: Gemini model configured: {self.model_name} ---")
    
    def init_language_model(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        print(f"--- ModelOrchestrator.init_language_model started (provider: {self.provider}, model: {model_name or self.model_name}) ---")
        """
        Initialize or switch the language model.
        
        Args:
            model_name: Name of the model to use
            temperature: Temperature setting for the model
        """
        # Update model name if provided
        if model_name:
            self.model_name = model_name
            
        temp = temperature if temperature is not None else TEMPERATURE
            
        self.gemini_client = GeminiClient(
            api_key=self.api_key,
            model=self.model_name,
        )
    
    def switch_provider(self, provider: str, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Switch between AI providers.
        
        Args:
            provider: The provider to switch to ('openai' or 'deepseek')
            api_key: Optional API key for the provider
            model_name: Optional model name to use
            
        Returns:
            str: Status message indicating the provider and model in use
        """
        try:
            self.provider = provider.lower()
            
            if self.provider != 'gemini':
                raise ValueError(f"Unsupported provider: {provider}. Use 'gemini'.")
            if api_key:
                self.api_key = api_key
                
            # Update model name if provided
            if model_name:
                self.model_name = model_name
                
            # Re-initialize the language model
            self.init_language_model()
            
            return f"Switched to {self.provider} provider with model {self.model_name}"
            
        except Exception as e:
            error_msg = f"Error switching to provider {provider}: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg) from e
    
    def generate_response(
        self, 
        prompt: str, 
        relevant_documents: Optional[List[str]] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True  # NEW: Enable caching by default
    ) -> str:
        """
        Generate a text response from the language model.
        
        Args:
            prompt: The prompt for the model
            relevant_documents: Optional list of relevant documents to add context
            temperature: Optional override for model temperature
            use_cache: Whether to use cached responses (default: True)
            
        Returns:
            The generated response as a string
        """
        # Check cache first to save money! 💰
        if use_cache:
            cache_key = cache.cache_key(
                "response",
                prompt[:200],  # First 200 chars of prompt
                str(relevant_documents)[:100] if relevant_documents else "",
                self.model_name,
                temperature or TEMPERATURE
            )
            
            cached_response = cache.get(cache_key)
            if cached_response:
                print("💰 Using cached response - $0.00 cost!")
                return cached_response
        
        # Optimize prompt to reduce token usage and save money! 💰
        full_prompt = optimize_prompt(prompt, relevant_documents, max_tokens=4000)
        
        # Log token count and estimated cost for monitoring
        input_token_count = count_tokens(full_prompt, self.model_name)
        estimated_input_cost = estimate_api_cost(input_token_count, self.model_name)
        print(f"💰 Token count: {input_token_count} (~${estimated_input_cost:.4f} input cost)")
        
        import time
        temp = temperature if temperature is not None else TEMPERATURE
        start_time = time.time()
        response_text = self.gemini_client.generate_text(
            prompt=full_prompt,
            system_message="You are an expert educational AI assistant that specializes in creating personalized learning paths.",
            temperature=temp,
            max_tokens=MAX_TOKENS,
        )
        latency_ms = (time.time() - start_time) * 1000
        output_token_count = count_tokens(response_text, self.model_name) if response_text else 0
        total_cost = estimate_cost(self.model_name, input_token_count, output_token_count)

        self.obs_manager.log_llm_call(
            prompt=full_prompt,
            response=response_text,
            model=self.model_name,
            metadata={
                "temperature": temp,
                "max_tokens": MAX_TOKENS,
                "provider": self.provider,
                "cached": False
            },
            latency_ms=latency_ms,
            token_count=input_token_count + output_token_count,
            cost=total_cost
        )

        if use_cache and response_text:
            cache.set(cache_key, response_text, ttl=86400)

        return response_text
    
    def generate_response_stream(
        self, 
        prompt: str, 
        relevant_documents: Optional[List[str]] = None,
        temperature: Optional[float] = None,
    ):
        """
        Generate streaming response for real-time output.
        
        Why streaming:
        - Users see progress immediately
        - Perceived performance is better
        - Same cost as regular response!
        - Better UX = happier users
        
        Args:
            prompt: The prompt for the model
            relevant_documents: Optional list of relevant documents to add context
            temperature: Optional override for model temperature
        
        Yields:
            Chunks of response text as they arrive
        """
        # Optimize prompt to reduce costs
        full_prompt = optimize_prompt(prompt, relevant_documents, max_tokens=4000)
        
        # Log token count
        token_count = count_tokens(full_prompt, self.model_name)
        estimated_cost = estimate_api_cost(token_count, self.model_name)
        print(f"💰 Streaming - Token count: {token_count} (~${estimated_cost:.4f} input cost)")
        
        temp = temperature if temperature is not None else TEMPERATURE
        
        try:
            response = self.gemini_client.generate_text(
                prompt=full_prompt,
                system_message="You are an expert educational AI assistant that specializes in creating personalized learning paths.",
                temperature=temp,
                max_tokens=MAX_TOKENS,
            )
            yield response
        except Exception as exc:
            yield f"Error: {exc}"
    
    def generate_structured_response(
        self,
        prompt: str,
        output_schema: str,
        relevant_documents: Optional[List[str]] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True  # NEW: Enable caching by default
    ) -> str:
        """
        Generate a structured response that follows a specific schema.
        
        Args:
            prompt: The prompt for the model
            output_schema: The schema instructions for the output
            relevant_documents: Optional list of relevant documents to add context
            temperature: Optional override for model temperature
            use_cache: Whether to use cached responses (default: True)
            
        Returns:
            The generated response as a JSON string
        """
        # Check cache first to save money! 💰
        if use_cache:
            cache_key = cache.cache_key(
                "structured",
                prompt[:200],  # First 200 chars of prompt
                output_schema[:100],  # First 100 chars of schema
                str(relevant_documents)[:100] if relevant_documents else "",
                self.model_name,
                temperature or 0.2
            )
            
            cached_response = cache.get(cache_key)
            if cached_response:
                print("💰 Using cached structured response - $0.00 cost!")
                return cached_response
        # Determine if this is a learning path generation
        is_learning_path = 'LearningPath' in output_schema
        
        # Prepare the prompt with schema instructions and emphasize required fields
        required_fields_reminder = ""
        if is_learning_path:
            required_fields_reminder = """
            IMPORTANT: Your response MUST include ALL of these required fields:
            - title: String title of the learning path
            - description: Detailed description of the learning path
            - topic: Main topic of study
            - expertise_level: Starting expertise level
            - learning_style: Preferred learning style
            - time_commitment: Weekly time commitment
            - duration_weeks: Total duration in weeks (integer)
            - goals: List of learning goals and objectives
            - milestones: List of learning milestones
            - prerequisites: List of prerequisites for this path
            - total_hours: Total estimated hours (integer)
            
            For each milestone, you MUST include:
            - title: Short title for the milestone
            - description: Detailed description
            - estimated_hours: Estimated hours to complete (integer)
            - resources: List of recommended learning resources
            - skills_gained: List of skills gained after completion
            """
        
        schema_prompt = f"""
        {prompt}
        
        Your response should follow this schema format:
        {output_schema}
        
        {required_fields_reminder}
        
        Please provide a valid JSON response that strictly follows this schema.
        Do not include any explanatory text outside the JSON structure.
        """
        
        # Optimize prompt with context to reduce token usage 💰
        full_prompt = optimize_prompt(schema_prompt, relevant_documents, max_tokens=6000)
        
        # Log token count and estimated cost
        token_count = count_tokens(full_prompt, self.model_name)
        estimated_cost = estimate_api_cost(token_count, self.model_name)
        print(f"💰 Structured response - Token count: {token_count} (~${estimated_cost:.4f} input cost)")
        
        # Set up the temperature - lower for structured outputs
        temp = temperature if temperature is not None else 0.2
        
        response_text = self.gemini_client.generate_text(
            prompt=full_prompt,
            system_message="You are an expert AI assistant that specializes in generating structured responses following specified schemas. Always include all required fields in your JSON response.",
            temperature=temp,
            max_tokens=MAX_TOKENS,
        )
        
        cleaned_response = response_text.strip()
        if "```" in cleaned_response:
            fenced_parts = cleaned_response.split("```")
            for part in fenced_parts:
                stripped_part = part.strip()
                if stripped_part.lower().startswith("json"):
                    cleaned_response = stripped_part[4:].strip()
                    break

        try:
            data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            data = None
            for index, character in enumerate(cleaned_response):
                if character not in "[{":
                    continue
                try:
                    data, _ = decoder.raw_decode(cleaned_response[index:])
                    break
                except json.JSONDecodeError:
                    continue
            if data is None:
                raise ValueError("Gemini returned malformed JSON.")

        if is_learning_path:
            if not isinstance(data, dict):
                raise ValueError("Gemini learning-path response must be a JSON object.")
            required_fields = {
                'title', 'description', 'topic', 'expertise_level',
                'learning_style', 'time_commitment', 'duration_weeks',
                'goals', 'milestones', 'prerequisites', 'total_hours'
            }
            missing_fields = sorted(required_fields - set(data))
            if missing_fields:
                raise ValueError(
                    f"Gemini learning-path response is missing fields: {', '.join(missing_fields)}"
                )
            milestone_fields = {
                'title', 'description', 'estimated_hours', 'resources', 'skills_gained'
            }
            if not isinstance(data['milestones'], list) or not data['milestones']:
                raise ValueError("Gemini learning-path response must contain milestones.")
            for index, milestone in enumerate(data['milestones'], start=1):
                if not isinstance(milestone, dict):
                    raise ValueError(f"Gemini milestone {index} is not a JSON object.")
                missing_milestone_fields = sorted(milestone_fields - set(milestone))
                if missing_milestone_fields:
                    raise ValueError(
                        f"Gemini milestone {index} is missing fields: {', '.join(missing_milestone_fields)}"
                    )

        json_result = json.dumps(data)
        if use_cache:
            cache.set(cache_key, json_result, ttl=86400)
        return json_result
    
    def _deepseek_completion(self, prompt: str, temperature: float, system_message: str = None):
        """Reject the removed legacy provider instead of making a fallback request."""
        raise ValueError("DeepSeek generation is no longer supported; use Gemini.")

    def _create_fallback_learning_path(self):
        """
        Create a fallback learning path with default values when generation fails.
        """
        import datetime
        import uuid
        fallback_path = {
            "id": str(uuid.uuid4()),
            "title": "General Learning Path",
            "description": "A default learning path created when specific generation failed.",
            "topic": "General Topic",
            "expertise_level": "beginner",
            "learning_style": "visual", 
            "time_commitment": "moderate",
            "duration_weeks": 8,
            "goals": ["Build foundational knowledge", "Develop practical skills"],
            "milestones": [
                {
                    "title": "Getting Started",
                    "description": "Introduction to the fundamentals.",
                    "estimated_hours": 10,
                    "resources": [
                        {"name": "Online Documentation", "url": "", "type": "documentation"}
                    ],
                    "skills_gained": ["Basic knowledge"]
                },
                {
                    "title": "Core Concepts",
                    "description": "Understanding core principles and practices.",
                    "estimated_hours": 15,
                    "resources": [
                        {"name": "Online Tutorial", "url": "", "type": "tutorial"}
                    ],
                    "skills_gained": ["Fundamental concepts"]
                }
            ],
            "prerequisites": ["None"],
            "total_hours": 25,
            "created_at": datetime.datetime.now().isoformat()
        }
        return json.dumps(fallback_path)
        
    def analyze_difficulty(self, content: str) -> float:
        """
        Analyze the difficulty level of educational content.
        
        Args:
            content: The content to analyze
            
        Returns:
            Difficulty score between 0 (easiest) and 1 (hardest)
        """
        prompt = f"""
        Analyze the following educational content and rate its difficulty level on a scale from 0 to 1,
        where 0 is very basic (elementary level) and 1 is extremely advanced (expert/PhD level).
        
        Content:
        {content[:1000]}...
        
        Consider factors like:
        - Technical vocabulary and jargon
        - Complexity of concepts
        - Prerequisites required to understand
        - Density of information
        
        Return only a numeric score between 0 and 1 with up to 2 decimal places.
        """
        
        response = self.generate_response(prompt, temperature=0.1)
        
        # Extract the numeric score
        try:
            # Look for patterns like "0.75" or "Difficulty: 0.75"
            import re
            matches = re.findall(r"([0-9]\.[0-9]{1,2})", response)
            if matches:
                score = float(matches[0])
                return max(0.0, min(1.0, score))  # Ensure between 0 and 1
            
            # If no decimal found, look for whole numbers
            matches = re.findall(r"^([0-9])$", response)
            if matches:
                score = float(matches[0])
                return max(0.0, min(1.0, score))  # Ensure between 0 and 1
                
            return 0.5  # Default to middle difficulty
        except Exception:
            return 0.5  # Default to middle difficulty
    
    def generate_resource_recommendations(
        self,
        topic: str,
        learning_style: str,
        expertise_level: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate tailored resource recommendations for a topic.
        
        Args:
            topic: The topic to find resources for
            learning_style: Preferred learning style
            expertise_level: User's expertise level
            count: Number of resources to recommend
            
        Returns:
            List of resource dictionaries
        """
        prompt = f"""
        Generate {count} learning resources for someone studying {topic}.
        
        Their learning style is {learning_style} and their expertise level is {expertise_level}.
        
        IMPORTANT: All resources MUST be in English only. Do not include resources in Portuguese, Spanish, or any other language.
        
        For each resource, include:
        1. Title (in English)
        2. Type (video, article, book, interactive, course, documentation, podcast, project)
        3. Description (1-2 sentences in English)
        4. Difficulty level (beginner, intermediate, advanced, expert)
        5. Estimated time to complete (in minutes or hours)
        6. URL (create a realistic but fictional URL if needed)
        
        Provide the response as a JSON array of resource objects. All text fields must be in English.
        """
        
        response = self.generate_structured_response(
            prompt=prompt,
            output_schema="""
            [
              {
                "title": "string",
                "type": "string",
                "description": "string",
                "difficulty": "string",
                "time_estimate": "string", 
                "url": "string"
              }
            ]
            """,
            temperature=0.7
        )
        
        try:
            resources = json.loads(response)
            return resources
        except Exception:
            # Fallback to empty list on parsing error
            return []
    
    def generate_path(self, topic: str, expertise_level: str, learning_style: str, context: List[str] = None) -> str:
        """
        Generate a learning path based on user preferences and context using RAG.
        
        Args:
            topic: The learning topic
            expertise_level: User's expertise level
            learning_style: User's preferred learning style
            context: Optional context to consider
            
        Returns:
            Generated learning path
        """
        # Combine provided context with stored context
        full_context = self.context + (context or [])
        
        # Plan if planning is enabled
        if self.planning_enabled and hasattr(self, '_plan_path_generation'):
            self._plan_path_generation(topic, expertise_level, learning_style, full_context)
        
        # Generate path with context
        prompt = f"""Generate a learning path for the following topic:
        
        Topic: {topic}
        Expertise Level: {expertise_level}
        Learning Style: {learning_style}
        
        Context:
        {' '.join(full_context)}
        
        Previous answers:
        {' '.join(self.memory)}
        
        Generate a structured learning path with milestones and resources.
        """
        
        path = self._generate_text(prompt)
        
        # Store path in memory
        self.memory.append(f"Generated path for {topic} with {expertise_level} level and {learning_style} style")
        
        return path
    
    def generate_answer(self, question: str, context: Optional[List[str]] = None, temperature: Optional[float] = None) -> str:
        """
        Generate an answer to a question using RAG and agentic behavior.
        
        Args:
            question: The question to answer
            context: Optional context to consider
            temperature: Optional temperature for response generation
            
        Returns:
            Generated answer
        """
        # Combine provided context with stored context
        full_context = self.context + (context or [])
        
        # Plan if planning is enabled
        if self.planning_enabled and hasattr(self, '_plan_answer_generation'):
            self._plan_answer_generation(question, full_context)
        
        # Generate answer with context
        prompt = f"""Answer the following question based on the provided context:
        
        Context:
        {' '.join(full_context)}
        
        Question: {question}"""
        
        # Store question in memory
        self.memory.append(f"Question: {question}")
        
        # Generate and return the answer
        return self.generate_response(prompt, relevant_documents=full_context, temperature=temperature)
    
    def _plan_answer_generation(self, question: str, context: List[str]) -> None:
        """
        Plan the answer generation process.
        
        Args:
            question: The question to answer
            context: Context information
        """
        # Analyze the question to determine the best approach
        question_lower = question.lower()
        
        # Determine if we need more context
        if len(context) < 2 and not any(keyword in question_lower for keyword in ["what", "how", "why", "when", "where", "who"]):
            self.context.append("Need more context for this question")
            
        # Determine the type of question
        if "how" in question_lower:
            self.context.append("This is a procedural question")
        elif "why" in question_lower:
            self.context.append("This is an explanatory question")
        elif "what" in question_lower:
            self.context.append("This is a definitional question")
        elif "compare" in question_lower or "difference" in question_lower:
            self.context.append("This is a comparative question")
            
    def _plan_path_generation(self, topic: str, expertise_level: str, learning_style: str, context: List[str]) -> None:
        """
        Plan the learning path generation process.
        
        Args:
            topic: The learning topic
            expertise_level: User's expertise level
            learning_style: User's preferred learning style
            context: Context information
        """
        # Determine the appropriate depth and breadth based on expertise level
        if expertise_level == "beginner":
            self.context.append("Focus on fundamentals and basic concepts")
        elif expertise_level == "intermediate":
            self.context.append("Include practical applications and case studies")
        elif expertise_level == "advanced":
            self.context.append("Include advanced techniques and research papers")
            
        # Adjust for learning style
        if learning_style == "visual":
            self.context.append("Prioritize video resources and diagrams")
        elif learning_style == "auditory":
            self.context.append("Prioritize podcasts and audio lectures")
        elif learning_style == "reading":
            self.context.append("Prioritize books and articles")
        elif learning_style == "kinesthetic":
            self.context.append("Prioritize hands-on projects and exercises")

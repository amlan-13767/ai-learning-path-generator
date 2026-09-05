"""
Learning path generation logic for the AI Learning Path Generator.
This module handles the creation and management of personalized learning paths.
"""
import datetime
import json
import os
import uuid
import hashlib
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Type
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, ValidationError, validator

from src.data.document_store import DocumentStore
from src.data.skills_database import get_skill_info
from src.ml.model_orchestrator import ModelOrchestrator
from src.ml.job_market import get_job_market_stats
from src.utils.config import (
    DEFAULT_REGION,
    EXPERTISE_LEVELS,
    LEARNING_STYLES,
    TIME_COMMITMENTS,
)
from src.utils.helpers import (
    calculate_study_schedule,
    difficulty_to_score,
    match_resources_to_learning_style,
)
from src.utils.observability import get_observability_manager, traceable
from src.utils.semantic_cache import SemanticCache
# Import for OpenAI-powered resource search
from src.ml.resource_search import search_resources


class ResourceItem(BaseModel):
    """A single learning resource."""

    type: str = Field(description="Type of the resource (e.g., article, video, book)")
    url: str = Field(description="URL of the resource")
    description: str = Field(description="Brief description of the resource")


class JobMarketData(BaseModel):
    """Job market data for a skill or role."""

    open_positions: Optional[str] = Field(
        description="Estimated number of open positions for this role/skill.",
        default="N/A",
    )
    trending_employers: Optional[List[str]] = Field(
        description="List of companies currently hiring for this role/skill.",
        default_factory=list,
    )
    average_salary: Optional[str] = Field(
        description="Estimated average salary range for this role/skill.", default="N/A"
    )
    related_roles: Optional[List[str]] = Field(
        description="Related job titles or roles for this skill/role.",
        default_factory=list,
    )
    demand_score: Optional[int] = Field(
        description="Demand score (0-100) for how hot this skill is right now", default=0
    )
    region: Optional[str] = Field(
        description="Region for which these stats apply", default=None
    )
    error: Optional[str] = Field(
        description="Error message if data could not be fetched.", default=None
    )


class Milestone(BaseModel):
    """A milestone in a learning path."""

    title: str = Field(description="Short title for the milestone")
    description: str = Field(description="Detailed description of what will be learned")
    estimated_hours: int = Field(
        description="Estimated hours to complete this milestone"
    )
    resources: List[ResourceItem] = Field(description="Recommended learning resources")
    skills_gained: List[str] = Field(
        description="Skills gained after completing this milestone"
    )
    job_market_data: JobMarketData = Field(
        description="Job market data for the skills gained",
        default_factory=JobMarketData,
    )

    @validator("resources", pre=True, always=True)
    def check_resources_not_empty(cls, v):
        if not v:
            # Instead of raising an error, provide a default resource
            return [
                ResourceItem(
                    type="article",
                    url="https://example.com/default-resource",
                    description="Default resource - Please explore additional materials for this milestone",
                )
            ]
        return v


class LearningPath(BaseModel):
    """Model representation of a learning path."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Title of the learning path")
    description: str = Field(description="Detailed description of the learning path")
    topic: str = Field(description="Main topic of study")
    expertise_level: str = Field(description="Starting expertise level")
    learning_style: str = Field(description="Preferred learning style")
    time_commitment: str = Field(description="Weekly time commitment")
    duration_weeks: Optional[int] = Field(
        description="Total duration in weeks", default=0
    )
    goals: List[str] = Field(description="Learning goals and objectives")
    milestones: List["Milestone"] = Field(description="Weekly or modular breakdown")
    schedule: Optional[Dict[str, Any]] = Field(
        default=None, description="The calculated study schedule"
    )
    prerequisites: List[str] = Field(description="Prerequisites for this path")
    total_hours: int = Field(description="Total estimated hours")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    job_market_data: JobMarketData = Field(
        description="Aggregated job market data for the main topic",
        default_factory=JobMarketData,
    )

    @validator("goals", pre=True, always=True)
    def check_goals_not_empty(cls, v):
        if not v:
            raise ValueError("Learning path goals list cannot be empty")
        # Ensure all goals are non-empty strings
        if not all(isinstance(goal, str) and goal.strip() for goal in v):
            raise ValueError("All goals must be non-empty strings")
        return v

    @validator("milestones", pre=True, always=True)
    def check_milestones_not_empty(cls, v):
        if not v:
            raise ValueError("Learning path milestones list cannot be empty")
        return v


class LearningPathGenerator:
    """
    Core class responsible for generating personalized learning paths.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the learning path generator.

        Args:
            api_key: Optional OpenAI API key (if not provided in environment)
        """
        self.model_orchestrator = ModelOrchestrator(api_key)
        self.document_store = DocumentStore()
        self.output_parser = PydanticOutputParser(pydantic_object=LearningPath)
        self.obs_manager = get_observability_manager()
        # Pass REDIS_URL from environment to SemanticCache
        self.semantic_cache = SemanticCache(redis_url=os.getenv('REDIS_URL'))

    def fetch_job_market_data(
        self,
        skill_or_role: str,
        region: Optional[str] = None,
        expertise_level: str = "intermediate",
    ) -> JobMarketData:
        """
        Fetch job market data for a given skill or role from the skills database.

        Args:
            skill_or_role: The skill or role to query job market data for.
            region: The region to query job market data for (default is DEFAULT_REGION).
            expertise_level: User's expertise level for resource filtering.

        Returns:
            A JobMarketData object containing job market statistics.
        """
        try:
            # Get skill info from database (includes salary and market info)
            skill_info = get_skill_info(skill_or_role, expertise_level)
            
            # Extract market info
            market_info = skill_info.get("market_info", {})
            
            # Create JobMarketData object
            return JobMarketData(
                open_positions=market_info.get("open_positions", "10,000+"),
                average_salary=skill_info.get("salary_range", "$80,000 - $150,000"),
                trending_employers=market_info.get("top_employers", ["Tech Companies"]),
                related_roles=market_info.get("related_roles", ["Software Engineer"]),
                region=region or DEFAULT_REGION
            )
        except Exception as e:
            # Fallback to default data
            return JobMarketData(
                open_positions="10,000+",
                average_salary="$80,000 - $150,000",
                trending_employers=["Tech Companies", "Startups", "Enterprises"],
                related_roles=["Software Engineer", "Developer"],
                region=region or DEFAULT_REGION,
                error=str(e)
            )

    def fetch_related_roles(
        self, skills: List[str], ai_provider: Optional[str] = None, ai_model: Optional[str] = None
    ) -> List[str]:
        """
        Fetch related job roles for a given list of skills using an LLM.

        Args:
            skills: The list of skills to find related job roles for.
            ai_provider: The AI provider to use (e.g., 'openai').
            ai_model: The specific AI model to use.

        Returns:
            A list of related job role titles.
        """
        if not skills:
            return []

        skills_str = ", ".join(skills)
        prompt = f"""
        Based on the following skills: {skills_str}, what are some relevant job titles or roles that utilize these skills?
        Please provide a list of job titles. Return the answer as a JSON array of strings.
        For example: ["Data Scientist", "Machine Learning Engineer", "Business Analyst"]
        """

        # Select orchestrator based on provider/model overrides
        orchestrator_to_use = self.model_orchestrator
        if ai_provider or ai_model:
            try:
                override_provider = ai_provider or self.model_orchestrator.provider
                orchestrator_to_use = ModelOrchestrator(provider=override_provider)
                orchestrator_to_use.init_language_model(model_name=ai_model)
            except Exception as init_error:
                print(
                    f"⚠️  Falling back to default orchestrator for related roles: {init_error}"
                )
                orchestrator_to_use = self.model_orchestrator

        try:
            # Use the selected orchestrator to get the response
            response_str = orchestrator_to_use.generate_response(
                prompt,
                use_cache=False,
            )

            # The response is expected to be a JSON string of a list
            roles = json.loads(response_str)
            if isinstance(roles, list):
                return roles
            return []
        except json.JSONDecodeError:
            # Fallback if the response is not valid JSON
            # Attempt to parse a plain list from the string
            if "[" in response_str and "]" in response_str:
                try:
                    # Extract content between brackets and split by comma
                    roles_str = response_str[response_str.find('[')+1:response_str.rfind(']')]
                    return [role.strip().strip('"\'') for role in roles_str.split(',')]
                except Exception:
                    return ["Could not parse roles"]
            return ["Could not determine roles"]
        except Exception as e:
            print(f"An unexpected error occurred while fetching related roles: {e}")
            return []

    def generate_path(
        self,
        topic: str,
        expertise_level: str,
        learning_style: str,
        time_commitment: str = "moderate",
        duration_weeks: Optional[int] = None,
        goals: List[str] = None,
        additional_info: Optional[str] = None,
        context: List[str] = None,
        ai_provider: Optional[str] = None,
        ai_model: Optional[str] = None,
        user_id: Optional[str] = None,  # For tracking in observability
    ) -> LearningPath:
        """
        Generate a personalized learning path based on user preferences.

        Args:
            topic: The main topic of study
            expertise_level: Starting level of expertise
            learning_style: Preferred learning style
            time_commitment: Weekly time commitment
            duration_weeks: User-specified duration in weeks (overrides calculated duration)
            goals: List of learning goals
            additional_info: Any additional information or constraints
            user_id: Optional user ID for tracking

        Returns:
            A complete learning path object
        """
        # --- High-Level Cache Check ---
        # Create a stable cache key by sorting and stringifying all inputs
        goals_str = json.dumps(sorted(goals) if goals else [])
        cache_key_data = {
            "topic": topic.lower().strip(),
            "expertise_level": expertise_level,
            "time_commitment": time_commitment,
            "duration_weeks": duration_weeks,
            "goals": goals_str,
            "additional_info": additional_info or ""
        }
        cache_key_str = json.dumps(cache_key_data, sort_keys=True).encode('utf-8')
        cache_key = hashlib.sha256(cache_key_str).hexdigest()

        cached_path = self.document_store.get_cached_path(cache_key)
        if cached_path:
            print(f"✅ Cache hit for learning path: {cache_key[:16]}... (topic: {topic})")
            # Ensure the cached data is a valid LearningPath object
            try:
                return LearningPath(**cached_path)
            except ValidationError as e:
                print(f"⚠️ Cached path validation failed, regenerating... Error: {e}")
        else:
            print(f"❌ Cache miss for learning path: {cache_key[:16]}... (topic: {topic})")
        # ---------------------------

        # Track generation time for observability
        generation_start_time = time.time()
        
        # Log the generation attempt
        self.obs_manager.log_event("path_generation_started", {
            "topic": topic,
            "expertise_level": expertise_level,
            "learning_style": learning_style,
            "time_commitment": time_commitment,
            "user_id": user_id
        })
        
        if goals is None:
            goals = [f"Master {topic}", f"Build practical skills in {topic}"]

        if expertise_level not in EXPERTISE_LEVELS:
            raise ValueError(
                f"Invalid expertise level. Choose from: {', '.join(EXPERTISE_LEVELS.keys())}"
            )

        # Allow None for learning_style and use a default
        if learning_style is None:
            learning_style = "visual"  # Default learning style
        elif learning_style not in LEARNING_STYLES:
            raise ValueError(
                f"Invalid learning style. Choose from: {', '.join(LEARNING_STYLES.keys())}"
            )

        # Allow None for time_commitment and use a default
        if time_commitment is None:
            time_commitment = "moderate"  # Default time commitment
        elif time_commitment not in TIME_COMMITMENTS:
            raise ValueError(
                f"Invalid time commitment. Choose from: {', '.join(TIME_COMMITMENTS.keys())}"
            )

        relevant_docs = self.document_store.search_documents(
            query=topic, filters={"expertise_level": expertise_level}, top_k=10
        )

        hours_map = {"minimal": 2, "moderate": 5, "substantial": 8, "intensive": 15}
        hours_per_week = hours_map.get(time_commitment, 5)

        # Use user-specified duration if provided, otherwise calculate
        if duration_weeks and duration_weeks > 0:
            adjusted_duration = duration_weeks
            print(f"✅ Using user-specified duration: {adjusted_duration} weeks")
        else:
            base_duration = 8
            intensity_factor = {
                "minimal": 2.0,
                "moderate": 1.5,
                "substantial": 1.0,
                "intensive": 0.75,
            }
            complexity_factor = {
                "beginner": 1.0,
                "intermediate": 1.2,
                "advanced": 1.5,
                "expert": 2.0,
            }

            adjusted_duration = int(
                base_duration
                * intensity_factor.get(time_commitment, 1.0)
                * complexity_factor.get(expertise_level, 1.0)
            )
            print(f"📊 Calculated duration: {adjusted_duration} weeks")
        
        # Calculate appropriate number of milestones based on duration
        # Rule: 1 milestone per 1-3 weeks
        if adjusted_duration <= 4:
            target_milestones = 3  # Short paths: 3 milestones
        elif adjusted_duration <= 8:
            target_milestones = 4  # Medium paths: 4 milestones
        elif adjusted_duration <= 12:
            target_milestones = 5  # Standard paths: 5 milestones
        elif adjusted_duration <= 20:
            target_milestones = 6  # Long paths: 6 milestones
        else:
            target_milestones = 7  # Very long paths: 7 milestones
        
        print(f"🎯 Target milestones for {adjusted_duration} weeks: {target_milestones}")

        # Build semantic cache query signature (captures the high-level intent)
        semantic_signature = json.dumps(
            {
                "topic": topic,
                "expertise_level": expertise_level,
                "time_commitment": time_commitment,
                "duration_weeks": adjusted_duration,
                "target_milestones": target_milestones,
                "goals": goals,
                "additional_info": additional_info,
            },
            sort_keys=True,
        )

        learning_path: Optional[LearningPath] = None
        parsed_successfully = False

        # --- Semantic Cache Check (pre-LLM) ---
        cached_semantic_path = self.semantic_cache.get(semantic_signature)
        if cached_semantic_path:
            try:
                learning_path = LearningPath(**cached_semantic_path)
                parsed_successfully = True
                print("✅ Semantic cache hit for learning path structure")
            except ValidationError as e:
                print(f"⚠️ Semantic cache entry invalid, regenerating. Error: {e}")
                cached_semantic_path = None
        else:
            print("❌ Semantic cache miss for learning path structure")
        # --------------------------------------

        # Few-Shot Prompting: Provide concrete examples to guide the AI
        # This dramatically improves output quality and consistency
        prompt_content = f"""Generate a detailed personalized learning path for the following:

Topic: {topic}
Expertise Level: {expertise_level} - {EXPERTISE_LEVELS[expertise_level]}
Learning Style: {learning_style} - {LEARNING_STYLES[learning_style]}
Time Commitment: {time_commitment} - {TIME_COMMITMENTS[time_commitment]}
Duration: {adjusted_duration} weeks
Target Milestones: {target_milestones} milestones
Learning Goals: {', '.join(goals)}
Additional Information: {additional_info or 'None provided'}

IMPORTANT: 
1. Return ONLY valid JSON matching this exact structure.
2. Generate EXACTLY {target_milestones} milestones (no more, no less).
3. Set duration_weeks to EXACTLY {adjusted_duration}.
4. Distribute the milestones evenly across the {adjusted_duration} weeks.

=== EXAMPLE 1: Python Programming (Beginner) ===
{{
  "title": "Complete Python Programming Journey",
  "description": "A comprehensive learning path designed for absolute beginners to master Python programming through hands-on projects and real-world applications.",
  "topic": "Python Programming",
  "expertise_level": "beginner",
  "learning_style": "visual",
  "time_commitment": "moderate",
  "duration_weeks": 8,
  "goals": ["Master Python basics", "Build real projects", "Prepare for data science"],
  "milestones": [
    {{
      "title": "Python Fundamentals",
      "description": "Learn Python syntax, variables, data types, and basic operations",
      "estimated_hours": 10,
      "resources": [
        {{"type": "video", "url": "https://example.com/python-basics", "description": "Python Basics Video Tutorial"}},
        {{"type": "interactive", "url": "https://example.com/python-exercises", "description": "Interactive Python Exercises"}}
      ],
      "skills_gained": ["Python syntax", "Data types", "Variables", "Basic operators"]
    }},
    {{
      "title": "Control Flow and Functions",
      "description": "Master if statements, loops, and creating reusable functions",
      "estimated_hours": 12,
      "resources": [
        {{"type": "article", "url": "https://example.com/control-flow", "description": "Control Flow Guide"}},
        {{"type": "video", "url": "https://example.com/functions", "description": "Functions Deep Dive"}}
      ],
      "skills_gained": ["Conditional logic", "Loops", "Function creation", "Code organization"]
    }}
  ],
  "prerequisites": ["Basic computer skills", "Text editor familiarity"],
  "total_hours": 40
}}

=== EXAMPLE 2: Machine Learning (Intermediate) ===
{{
  "title": "Practical Machine Learning Mastery",
  "description": "An intermediate-level path to master machine learning algorithms, model training, and deployment for real-world applications.",
  "topic": "Machine Learning",
  "expertise_level": "intermediate",
  "learning_style": "hands-on",
  "time_commitment": "substantial",
  "duration_weeks": 12,
  "goals": ["Build ML models", "Deploy to production", "Understand ML theory"],
  "milestones": [
    {{
      "title": "Supervised Learning Fundamentals",
      "description": "Master regression and classification algorithms with practical implementations",
      "estimated_hours": 15,
      "resources": [
        {{"type": "course", "url": "https://example.com/supervised-learning", "description": "Supervised Learning Course"}},
        {{"type": "project", "url": "https://example.com/ml-projects", "description": "Hands-on ML Projects"}}
      ],
      "skills_gained": ["Linear regression", "Logistic regression", "Decision trees", "Model evaluation"]
    }}
  ],
  "prerequisites": ["Python programming", "Basic statistics", "Linear algebra basics"],
  "total_hours": 60
}}

=== YOUR TASK ===
Now generate a similar learning path for:
Topic: {topic}
Expertise Level: {expertise_level}
Learning Style: {learning_style}
Time Commitment: {time_commitment}
Goals: {', '.join(goals)}

Requirements:
1. Include 3-7 milestones that represent major learning stages
2. Each milestone should have 2-4 resources tailored to the {learning_style} learning style
3. Estimate realistic hours for each milestone
4. List specific skills gained at each milestone
5. Include relevant prerequisites
6. Calculate total_hours as sum of all milestone hours

Return ONLY the JSON object, no markdown formatting or explanation.
"""

        prompt_with_context = prompt_content
        if context:
            context_text = "\n\nAdditional Context:\n" + "\n".join(context)
            prompt_with_context += context_text

        orchestrator_to_use = self.model_orchestrator
        if ai_provider:
            custom_orchestrator = ModelOrchestrator(provider=ai_provider)
            custom_orchestrator.init_language_model(model_name=ai_model)
            orchestrator_to_use = custom_orchestrator

        # Attempt up to 3 times to get a valid LearningPath JSON
        last_error: Optional[Exception] = None
        if not parsed_successfully:
            for attempt in range(3):
                if attempt > 0:
                    print(f"Retrying learning path generation (attempt {attempt+1}) due to previous validation failure…")
                response = orchestrator_to_use.generate_structured_response(
                    prompt=prompt_with_context,
                    output_schema=self.output_parser.get_format_instructions(),
                    relevant_documents=(
                        [doc.page_content for doc in relevant_docs] if relevant_docs else None
                    ),
                    temperature=0.6 + 0.1 * attempt,  # vary temperature slightly on retries
                )
                try:
                    learning_path = self.output_parser.parse(response)
                    parsed_successfully = True
                    # Store the successful structure for future semantic cache hits
                    self.semantic_cache.set(semantic_signature, learning_path.dict())
                    break
                except ValidationError as ve:
                    print("Validation failed when parsing AI response as LearningPath:", ve)
                    print("Offending response:\n", response)
                    last_error = ve
                    # Slightly tweak the prompt for the next attempt
                    prompt_with_context += (
                        "\n\nIMPORTANT: Your last response did NOT match the schema and was therefore rejected. "
                        "You MUST return a COMPLETE JSON object that follows the exact LearningPath schema with ALL required fields."
                    )
                except Exception as e:
                    print("Unexpected error while parsing AI response:", e)
                    print("Offending response:\n", response)
                    last_error = e
                    break  # Unexpected errors – don't retry further

        if not parsed_successfully:
            raise RuntimeError("LearningPath generation failed after 3 attempts") from last_error

        # Fetch job market data ONCE for the main topic (not per milestone)
        # This significantly speeds up generation time
        print(f"📊 Fetching job market data for main topic: {topic}")
        aggregated_job_market = self.fetch_job_market_data(topic, expertise_level=expertise_level)
        learning_path.job_market_data = aggregated_job_market

        # Fetch related roles once for the main topic
        all_skills = []
        for milestone in learning_path.milestones:
            if milestone.skills_gained:
                all_skills.extend(
                    milestone.skills_gained
                    if isinstance(milestone.skills_gained, list)
                    else [milestone.skills_gained]
                )

        if all_skills:
            related_roles = self.fetch_related_roles(
                all_skills[:5],  # Use top 5 skills only
                ai_provider=ai_provider,
                ai_model=ai_model,
            )
            aggregated_job_market.related_roles = related_roles

        # Share the aggregated job market snapshot with each milestone if needed downstream
        for milestone in learning_path.milestones:
            milestone.job_market_data = aggregated_job_market

        # Fetch resources for milestones IN PARALLEL (much faster!)
        print(f"🔍 Fetching resources for {len(learning_path.milestones)} milestones in parallel...")
        
        def fetch_milestone_resources(milestone_data):
            """Helper function to fetch resources for a single milestone"""
            milestone, index = milestone_data
            try:
                print(f"  [{index}/{len(learning_path.milestones)}] Fetching resources for: {milestone.title}")
                
                # Get trusted sources from the skills database
                skill_info = get_skill_info(topic, expertise_level)
                trusted_sources = skill_info.get("resources", {})
                
                # Prepare the trusted sources dict for Perplexity
                perplexity_sources = None
                if trusted_sources:
                    perplexity_sources = {
                        'youtube': trusted_sources.get('youtube', []),
                        'websites': trusted_sources.get('websites', [])
                    }
                    print(f"  📚 Using curated sources:")
                    if perplexity_sources.get('youtube'):
                        print(f"     YouTube: {', '.join(perplexity_sources['youtube'][:3])}{'...' if len(perplexity_sources['youtube']) > 3 else ''}")
                    if perplexity_sources.get('websites'):
                        print(f"     Websites: {', '.join(perplexity_sources['websites'][:3])}{'...' if len(perplexity_sources['websites']) > 3 else ''}")
                else:
                    print(f"  ⚠️  No curated sources found for '{topic}' - using general search")
                
                # Use Perplexity to search within trusted sources
                contextualized_query = f"{topic}: {milestone.title}"
                print(f"  🔍 Searching with Perplexity...")
                
                perplexity_results = search_resources(
                    contextualized_query, 
                    k=5,  # Get more resources for better variety
                    trusted_sources=perplexity_sources
                )
                
                if perplexity_results and len(perplexity_results) > 0:
                    print(f"  ✓ Found {len(perplexity_results)} specific resources from trusted sources")
                    return milestone, [ResourceItem(**r) for r in perplexity_results]
                else:
                    # Fallback to default resources if Perplexity fails
                    print(f"  ⚠️ Perplexity search returned no results, using fallback")
                    return milestone, [
                        ResourceItem(
                            type="Video",
                            url=f"https://www.youtube.com/results?search_query={milestone.title.replace(' ', '+')}",
                            description=f"YouTube: {milestone.title}"
                        ),
                        ResourceItem(
                            type="Online Course",
                            url=f"https://www.coursera.org/search?query={milestone.title.replace(' ', '+')}",
                            description=f"Coursera: {milestone.title}"
                        )
                    ]
                    
            except Exception as _err:
                print(f"  ⚠️  Resource search failed for {milestone.title}: {_err}")
                # Return default resources
                return milestone, [
                    ResourceItem(
                        type="Video",
                        url=f"https://www.youtube.com/results?search_query={milestone.title.replace(' ', '+')}",
                        description=f"YouTube: {milestone.title}"
                    ),
                    ResourceItem(
                        type="Online Course",
                        url=f"https://www.coursera.org/search?query={milestone.title.replace(' ', '+')}",
                        description=f"Coursera: {milestone.title}"
                    )
                ]
        
        # Use ThreadPoolExecutor to fetch resources in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            milestone_data = [(m, i+1) for i, m in enumerate(learning_path.milestones)]
            future_to_milestone = {
                executor.submit(fetch_milestone_resources, data): data[0] 
                for data in milestone_data
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_milestone):
                milestone, resources = future.result()
                milestone.resources = resources
        
        print(f"✅ All resources fetched!")
        
        # Validate all resources to ensure they're accessible
        print(f"🔍 Validating resource URLs...")
        all_resources_to_validate = []
        for milestone in learning_path.milestones:
            for resource in milestone.resources:
                all_resources_to_validate.append({
                    'url': resource.url,
                    'title': resource.description,
                    'type': resource.type
                })
        
        # Run validation asynchronously
        try:
            from src.utils.resource_validator import ResourceValidator
            validator = ResourceValidator(cache_ttl_hours=24, max_retries=2)
            
            # Create event loop for async validation
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            validated_resources = loop.run_until_complete(
                validator.validate_resources(all_resources_to_validate)
            )
            
            # Update milestones with validation results and filter out invalid resources
            resource_index = 0
            for milestone in learning_path.milestones:
                validated_milestone_resources = []
                for resource in milestone.resources:
                    if resource_index < len(validated_resources):
                        validation = validated_resources[resource_index].get('validation', {})
                        
                        # Only keep resources with high confidence (valid or temporarily unavailable)
                        if validation.get('valid', False) or validation.get('confidence', 0) >= 0.5:
                            validated_milestone_resources.append(resource)
                            if not validation.get('valid'):
                                print(f"  ⚠️  Keeping potentially valid resource: {resource.url[:50]}... (confidence: {validation.get('confidence')})")
                        else:
                            print(f"  ❌ Filtered out invalid resource: {resource.url[:50]}... ({validation.get('error', 'unknown error')})")
                        
                        resource_index += 1
                
                # Update milestone with validated resources
                milestone.resources = validated_milestone_resources
            
            # Get validation stats
            stats = validator.get_validation_stats()
            print(f"✅ Validation complete: {stats['valid_count']}/{stats['total_checked']} resources valid ({stats['success_rate']}%)")
            
        except Exception as e:
            print(f"⚠️  Resource validation failed: {e}")
            print(f"   Continuing with unvalidated resources...")
            import traceback
            traceback.print_exc()

        # Ensure each milestone has resources after validation; perform general search fallback if needed
        for milestone in learning_path.milestones:
            try:
                if not milestone.resources or len(milestone.resources) == 0:
                    print(f"  ⚠️  No valid resources after validation for: {milestone.title}. Running general search fallback...")
                    contextualized_query = f"{topic}: {milestone.title}"
                    general_results = search_resources(contextualized_query, k=5, trusted_sources=None)
                    if general_results:
                        milestone.resources = [ResourceItem(**r) for r in general_results[:3]]
                
                if not milestone.resources or len(milestone.resources) == 0:
                    print(f"  ⚠️  General search returned no results. Adding search links for: {milestone.title}")
                    yt_q = milestone.title.replace(' ', '+')
                    g_q = milestone.title.replace(' ', '+')
                    milestone.resources = [
                        ResourceItem(
                            type="Video",
                            url=f"https://www.youtube.com/results?search_query={yt_q}",
                            description=f"YouTube: {milestone.title}"
                        ),
                        ResourceItem(
                            type="Web Search",
                            url=f"https://www.google.com/search?q={g_q}",
                            description=f"Google: {milestone.title}"
                        ),
                    ]
                
                if len(milestone.resources) < 2:
                    print(f"  ℹ️  Topping up resources for: {milestone.title}")
                    contextualized_query = f"{topic}: {milestone.title}"
                    more_results = search_resources(contextualized_query, k=5, trusted_sources=None)
                    if more_results:
                        for r in more_results:
                            if len(milestone.resources) >= 3:
                                break
                            try:
                                milestone.resources.append(ResourceItem(**r))
                            except Exception:
                                continue
            except Exception as _e:
                print(f"  ⚠️  Post-validation fallback failed for {milestone.title}: {_e}")

        topic_weights = {
            milestone.title: milestone.estimated_hours
            for milestone in learning_path.milestones
        }

        schedule = calculate_study_schedule(
            weeks=adjusted_duration,
            hours_per_week=hours_per_week,
            topic_weights=topic_weights,
        )
        learning_path.schedule = schedule

        for milestone in learning_path.milestones:
            milestone.resources = match_resources_to_learning_style(
                resources=milestone.resources, learning_style=learning_style
            )

            learning_path.total_hours = sum(
                m.estimated_hours for m in learning_path.milestones if m.estimated_hours
            )
            learning_path.duration_weeks = adjusted_duration
            learning_path.id = str(uuid.uuid4())
            
            # Mark as successful
            success = True
            
            # Log success metrics
            generation_time_ms = (time.time() - generation_start_time) * 1000
            self.obs_manager.log_metric("path_generation_success", 1.0, {
                "topic": topic,
                "expertise_level": expertise_level,
                "duration_ms": generation_time_ms,
                "milestone_count": len(learning_path.milestones),
                "user_id": user_id
            })
            
            self.obs_manager.log_event("path_generation_completed", {
                "topic": topic,
                "expertise_level": expertise_level,
                "milestone_count": len(learning_path.milestones),
                "total_hours": learning_path.total_hours,
                "duration_weeks": learning_path.duration_weeks,
                "generation_time_ms": generation_time_ms,
                "user_id": user_id
            })

            # --- Cache the final result ---
            self.document_store.cache_path(cache_key, learning_path.dict())
            # ---------------------------

            return learning_path

    def save_path(
        self, learning_path: LearningPath, output_dir: str = "learning_paths"
    ) -> str:
        """
        Save a learning path to file.

        Args:
            learning_path (LearningPath): The learning path to save.
            output_dir (str, optional): Directory to save the path. Defaults to "learning_paths".

        Returns:
            str: Path to the saved file.
        """
        path_dir = Path(output_dir)
        path_dir.mkdir(exist_ok=True, parents=True)

        safe_topic = learning_path.topic.lower().replace(" ", "_")[:30]
        filename = f"{safe_topic}_{learning_path.id[:8]}.json"
        file_path = path_dir / filename

        with open(file_path, "w") as f:
            f.write(json.dumps(learning_path.dict(), indent=2))

        return str(file_path)

    def load_path(
        self, path_id: str, input_dir: str = "learning_paths"
    ) -> Optional[LearningPath]:
        """
        Load a learning path from file by ID.

        Args:
            path_id (str): ID of the learning path to load.
            input_dir (str, optional): Directory to search for the path. Defaults to "learning_paths".

        Returns:
            Optional[LearningPath]: The loaded learning path or None if not found.
        """
        path_dir = Path(input_dir)
        if not path_dir.exists():
            return None

        for file_path in path_dir.glob(f"*_{path_id[:8]}.json"):
            try:
                with open(file_path, "r") as f:
                    path_data = json.load(f)
                    if path_data.get("id", "").startswith(path_id):
                        return LearningPath(**path_data)
            except Exception:
                continue

        return None

"""
Intent Classification Service
Phase 2: AI-Powered Intent Detection and Entity Extraction

This service handles:
- Classifying user intent from messages
- Extracting entities (milestone names, week numbers, etc.)
- Routing messages to appropriate handlers
"""

from typing import Dict, Optional, List, Tuple
import json
from src.ml.model_orchestrator import ModelOrchestrator
from src.utils.config import DEFAULT_MODEL


class IntentClassifier:
    """
    Classifies user intents and extracts entities using AI.
    
    Intents:
    - MODIFY_PATH: User wants to change their learning path
    - CHECK_PROGRESS: User wants to know their progress
    - ASK_QUESTION: User has a question about content
    - GENERAL_CHAT: General conversation
    - REQUEST_HELP: User needs help/guidance
    """
    
    # Intent definitions
    INTENTS = {
        'MODIFY_PATH': {
            'description': 'User wants to modify their learning path',
            'examples': [
                'Make week 2 easier',
                'Add more video resources',
                'Split this milestone into smaller parts',
                'Remove this resource',
                'Change the duration to 8 weeks'
            ]
        },
        'CHECK_PROGRESS': {
            'description': 'User wants to check their learning progress',
            'examples': [
                'How am I doing?',
                'What percentage have I completed?',
                'How much time have I spent?',
                'When will I finish?',
                'Show my progress'
            ]
        },
        'ASK_QUESTION': {
            'description': 'User has a question about learning content',
            'examples': [
                'What is React?',
                'How do I use hooks?',
                'Explain this concept',
                'I don\'t understand this part',
                'Can you clarify?'
            ]
        },
        'REQUEST_HELP': {
            'description': 'User needs help or guidance',
            'examples': [
                'I\'m stuck',
                'This is too hard',
                'I need help',
                'Can you guide me?',
                'What should I do next?'
            ]
        },
        'GENERAL_CHAT': {
            'description': 'General conversation or greeting',
            'examples': [
                'Hello',
                'Thanks!',
                'That\'s helpful',
                'Good morning',
                'How are you?'
            ]
        }
    }
    
    def __init__(self):
        """Initialize the intent classifier."""
        self.orchestrator = ModelOrchestrator()
    
    def classify_intent(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None,
        learning_path_data: Optional[Dict] = None
    ) -> Tuple[str, Dict, float]:
        """
        Classify user intent and extract entities.
        
        Args:
            message: User's message
            conversation_context: Recent conversation history
            learning_path_data: Current learning path data (for context)
            
        Returns:
            Tuple of (intent, entities, confidence)
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(
            message,
            conversation_context,
            learning_path_data
        )
        
        # Get AI classification
        try:
            response = self.orchestrator.generate_structured_response(
                prompt=prompt,
                output_schema=self._get_classification_schema(),
                temperature=0.3,  # Lower temperature for more consistent classification
                use_cache=True
            )
            
            result = json.loads(response)
            
            return (
                result.get('intent', 'GENERAL_CHAT'),
                result.get('entities', {}),
                result.get('confidence', 0.5)
            )
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            # Fallback to simple keyword matching
            return self._fallback_classification(message)
    
    def _build_classification_prompt(
        self,
        message: str,
        conversation_context: Optional[List[Dict]],
        learning_path_data: Optional[Dict]
    ) -> str:
        """Build the prompt for intent classification."""
        
        # Build intent descriptions
        intent_descriptions = []
        for intent, info in self.INTENTS.items():
            examples = '\n    '.join([f'- "{ex}"' for ex in info['examples'][:3]])
            intent_descriptions.append(
                f"  {intent}: {info['description']}\n    Examples:\n    {examples}"
            )
        
        intent_text = '\n'.join(intent_descriptions)
        
        # Add conversation context if available
        context_text = ""
        if conversation_context and len(conversation_context) > 0:
            recent_messages = conversation_context[-3:]  # Last 3 messages
            context_lines = [f"  {msg['role']}: {msg['content']}" for msg in recent_messages]
            context_text = f"\n\nRecent conversation:\n" + '\n'.join(context_lines)
        
        # Add learning path context if available
        path_context = ""
        if learning_path_data:
            path_context = f"\n\nCurrent learning path: {learning_path_data.get('title', 'Unknown')}"
            if 'milestones' in learning_path_data:
                milestone_count = len(learning_path_data['milestones'])
                path_context += f"\nTotal milestones: {milestone_count}"
        
        prompt = f"""Classify the user's intent and extract relevant entities.

Available intents:
{intent_text}

User message: "{message}"{context_text}{path_context}

Analyze the message and determine:
1. The primary intent
2. Any entities mentioned (milestone numbers, week numbers, resource types, actions, etc.)
3. Your confidence level (0.0 to 1.0)

Extract entities such as:
- milestone_index: Which milestone (0-based index)
- week_number: Which week
- action: What action to take (simplify, split, add, remove, etc.)
- resource_type: Type of resource (video, article, tutorial, etc.)
- metric: What metric to check (percentage, time, completion, etc.)
- difficulty: Difficulty level mentioned (easier, harder, beginner, advanced, etc.)

Provide your analysis."""
        
        return prompt
    
    def _get_classification_schema(self) -> str:
        """Get the JSON schema for classification output."""
        return """
{
  "intent": "string (one of: MODIFY_PATH, CHECK_PROGRESS, ASK_QUESTION, REQUEST_HELP, GENERAL_CHAT)",
  "entities": {
    "milestone_index": "integer or null",
    "week_number": "integer or null",
    "action": "string or null",
    "resource_type": "string or null",
    "metric": "string or null",
    "difficulty": "string or null",
    "topic": "string or null"
  },
  "confidence": "float (0.0 to 1.0)",
  "reasoning": "string (brief explanation of classification)"
}
"""
    
    def _fallback_classification(self, message: str) -> Tuple[str, Dict, float]:
        """
        Fallback classification using simple keyword matching.
        
        Used when AI classification fails.
        """
        message_lower = message.lower()
        
        # Check for modification keywords
        modify_keywords = ['change', 'modify', 'add', 'remove', 'split', 'easier', 'harder', 'update']
        if any(keyword in message_lower for keyword in modify_keywords):
            return ('MODIFY_PATH', {}, 0.6)
        
        # Check for progress keywords
        progress_keywords = ['progress', 'completed', 'finish', 'how am i', 'how far', 'percentage']
        if any(keyword in message_lower for keyword in progress_keywords):
            return ('CHECK_PROGRESS', {}, 0.6)
        
        # Check for help keywords
        help_keywords = ['help', 'stuck', 'difficult', 'hard', 'confused', 'guide']
        if any(keyword in message_lower for keyword in help_keywords):
            return ('REQUEST_HELP', {}, 0.6)
        
        # Check for question keywords
        question_keywords = ['what', 'how', 'why', 'when', 'where', 'explain', 'clarify']
        if any(keyword in message_lower for keyword in question_keywords):
            return ('ASK_QUESTION', {}, 0.6)
        
        # Default to general chat
        return ('GENERAL_CHAT', {}, 0.5)
    
    def extract_milestone_reference(
        self,
        message: str,
        learning_path_data: Dict
    ) -> Optional[int]:
        """
        Extract milestone reference from message.
        
        Handles references like:
        - "week 2" → milestone index 1
        - "milestone 3" → milestone index 2
        - "the current one" → current milestone
        - "this milestone" → current milestone
        
        Args:
            message: User's message
            learning_path_data: Learning path data
            
        Returns:
            Milestone index (0-based) or None
        """
        message_lower = message.lower()
        
        # Check for week number
        import re
        week_match = re.search(r'week\s+(\d+)', message_lower)
        if week_match:
            week_num = int(week_match.group(1))
            return week_num - 1  # Convert to 0-based index
        
        # Check for milestone number
        milestone_match = re.search(r'milestone\s+(\d+)', message_lower)
        if milestone_match:
            milestone_num = int(milestone_match.group(1))
            return milestone_num - 1  # Convert to 0-based index
        
        # Check for ordinal references
        ordinals = {
            'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4,
            'sixth': 5, 'seventh': 6, 'eighth': 7, 'ninth': 8, 'tenth': 9
        }
        for ordinal, index in ordinals.items():
            if ordinal in message_lower:
                return index
        
        return None

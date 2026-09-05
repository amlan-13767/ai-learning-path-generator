"""
Enhanced Chatbot Controller
Phase 5: Integration & Orchestration

This service orchestrates all chatbot functionality:
- Conversation memory
- Intent classification
- Path modification
- Progress tracking
- Response generation
"""

from typing import Dict, Optional, List
import time
from datetime import datetime

from src.services.conversation_manager import ConversationManager
from src.services.intent_classifier import IntentClassifier
from src.services.path_modifier import PathModifier
from src.services.progress_tracker import ProgressTracker
from src.ml.model_orchestrator import ModelOrchestrator
from src.utils.helpers import count_tokens, estimate_api_cost
from web_app.models import UserLearningPath


class EnhancedChatbot:
    """
    Enhanced conversational chatbot with memory, intent understanding,
    and path modification capabilities.
    
    Features:
    - Multi-turn conversations with memory
    - Intent classification and routing
    - Dynamic path modifications
    - Progress tracking and insights
    - Contextual responses
    """
    
    def __init__(self):
        """Initialize the enhanced chatbot."""
        self.conversation_manager = ConversationManager(context_window_size=10)
        self.intent_classifier = IntentClassifier()
        self.path_modifier = PathModifier()
        self.progress_tracker = ProgressTracker()
        self.orchestrator = ModelOrchestrator()
    
    def process_message(
        self,
        user_id: int,
        message: str,
        learning_path_id: Optional[str] = None
    ) -> Dict:
        """
        Process a user message and generate response.
        
        This is the main entry point for the chatbot.
        
        Args:
            user_id: User ID
            message: User's message
            learning_path_id: Optional learning path ID for context
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Store user message
            user_msg = self.conversation_manager.add_message(
                user_id=user_id,
                message=message,
                role='user',
                learning_path_id=learning_path_id
            )
            
            # Step 2: Get conversation context
            conversation_context = self.conversation_manager.get_context_window(
                user_id=user_id,
                learning_path_id=learning_path_id
            )
            
            # Step 3: Get learning path data if available
            learning_path_data = None
            if learning_path_id:
                learning_path = UserLearningPath.query.get(learning_path_id)
                if learning_path and learning_path.user_id == user_id:
                    learning_path_data = learning_path.path_data_json
            
            # Step 4: Classify intent
            intent, entities, confidence = self.intent_classifier.classify_intent(
                message=message,
                conversation_context=conversation_context,
                learning_path_data=learning_path_data
            )
            
            print(f"🎯 Intent: {intent} (confidence: {confidence:.2f})")
            print(f"📦 Entities: {entities}")
            
            # Step 5: Route to appropriate handler
            if intent == 'MODIFY_PATH' and learning_path_id:
                response_data = self._handle_path_modification(
                    user_id=user_id,
                    learning_path_id=learning_path_id,
                    message=message,
                    entities=entities,
                    chat_message_id=user_msg.id
                )
            
            elif intent == 'CHECK_PROGRESS' and learning_path_id:
                response_data = self._handle_progress_check(
                    user_id=user_id,
                    learning_path_id=learning_path_id,
                    entities=entities
                )
            
            elif intent == 'ASK_QUESTION':
                response_data = self._handle_question(
                    message=message,
                    conversation_context=conversation_context,
                    learning_path_data=learning_path_data
                )
            
            elif intent == 'REQUEST_HELP':
                response_data = self._handle_help_request(
                    message=message,
                    learning_path_data=learning_path_data,
                    conversation_context=conversation_context
                )
            
            else:  # GENERAL_CHAT
                response_data = self._handle_general_chat(
                    message=message,
                    conversation_context=conversation_context
                )
            
            # Step 6: Store assistant response
            response_time_ms = int((time.time() - start_time) * 1000)
            tokens_used = response_data.get('tokens_used', 0)
            
            self.conversation_manager.add_message(
                user_id=user_id,
                message=response_data['response'],
                role='assistant',
                learning_path_id=learning_path_id,
                intent=intent,
                entities=entities,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms
            )
            
            # Step 7: Return response with metadata
            return {
                'success': True,
                'response': response_data['response'],
                'intent': intent,
                'entities': entities,
                'confidence': confidence,
                'response_time_ms': response_time_ms,
                'tokens_used': tokens_used,
                'metadata': response_data.get('metadata', {})
            }
        
        except Exception as e:
            print(f"Chatbot error: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error response
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            
            self.conversation_manager.add_message(
                user_id=user_id,
                message=error_response,
                role='assistant',
                learning_path_id=learning_path_id
            )
            
            return {
                'success': False,
                'response': error_response,
                'error': str(e)
            }
    
    def _handle_path_modification(
        self,
        user_id: int,
        learning_path_id: str,
        message: str,
        entities: Dict,
        chat_message_id: int
    ) -> Dict:
        """Handle path modification requests."""
        print("🔧 Handling path modification...")
        
        # Attempt to modify the path
        result = self.path_modifier.modify_path(
            learning_path_id=learning_path_id,
            user_id=user_id,
            modification_request=message,
            entities=entities,
            chat_message_id=chat_message_id
        )
        
        if result['success']:
            response = f"✅ {result['description']}\n\nYour learning path has been updated successfully!"
            
            # Add details if available
            if 'changes' in result:
                changes = result['changes']
                if 'data' in changes:
                    response += "\n\nWhat changed:"
                    # Format the changes nicely
                    if 'resources' in changes.get('data', {}):
                        resources = changes['data']['resources']
                        response += f"\n- Added {len(resources)} new resource(s)"
        else:
            response = f"I couldn't modify your learning path: {result.get('error', 'Unknown error')}\n\n"
            response += "Could you please rephrase your request or be more specific?"
        
        return {
            'response': response,
            'tokens_used': 0,  # Modification doesn't use many tokens
            'metadata': result
        }
    
    def _handle_progress_check(
        self,
        user_id: int,
        learning_path_id: str,
        entities: Dict
    ) -> Dict:
        """Handle progress check requests."""
        print("📊 Handling progress check...")
        
        # Get progress summary
        progress = self.progress_tracker.get_progress_summary(
            user_id=user_id,
            learning_path_id=learning_path_id
        )
        
        if 'error' in progress:
            return {
                'response': f"I couldn't retrieve your progress: {progress['error']}",
                'tokens_used': 0
            }
        
        # Format progress report
        response = self._format_progress_report(progress)
        
        return {
            'response': response,
            'tokens_used': 0,  # Progress calculation doesn't use tokens
            'metadata': progress
        }
    
    def _handle_question(
        self,
        message: str,
        conversation_context: List[Dict],
        learning_path_data: Optional[Dict]
    ) -> Dict:
        """Handle content questions."""
        print("❓ Handling question...")
        
        # Build context for AI
        context_parts = []
        
        if learning_path_data:
            context_parts.append(f"Learning Path: {learning_path_data.get('title', 'Unknown')}")
            context_parts.append(f"Topic: {learning_path_data.get('topic', 'Unknown')}")
        
        # Build prompt
        system_message = """You are an expert educational AI assistant. Answer the user's question clearly and helpfully.
If the question is about their learning path, provide specific, actionable advice.
Keep your response concise but informative."""
        
        # Add conversation context
        messages = [{"role": "system", "content": system_message}]
        
        # Add recent context (last 4 messages)
        if conversation_context:
            messages.extend(conversation_context[-4:])
        
        # Add current question if not already in context
        if not conversation_context or conversation_context[-1]['content'] != message:
            messages.append({"role": "user", "content": message})
        
        # Generate response
        full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        tokens = count_tokens(full_prompt)
        
        response = self.orchestrator.generate_response(
            prompt=message,
            relevant_documents=context_parts if context_parts else None,
            temperature=0.7,
            use_cache=True
        )
        
        return {
            'response': response,
            'tokens_used': tokens
        }
    
    def _handle_help_request(
        self,
        message: str,
        learning_path_data: Optional[Dict],
        conversation_context: List[Dict]
    ) -> Dict:
        """Handle help requests."""
        print("🆘 Handling help request...")
        
        # Build supportive response
        context_parts = []
        
        if learning_path_data:
            context_parts.append(f"User is learning: {learning_path_data.get('title', 'Unknown')}")
            context_parts.append(f"Expertise level: {learning_path_data.get('expertise_level', 'Unknown')}")
        
        system_message = """You are a supportive learning coach. The user is asking for help.
Provide encouraging, specific guidance. Break down complex topics into manageable steps.
Be empathetic and motivating."""
        
        messages = [{"role": "system", "content": system_message}]
        if conversation_context:
            messages.extend(conversation_context[-4:])
        messages.append({"role": "user", "content": message})
        
        full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        tokens = count_tokens(full_prompt)
        
        response = self.orchestrator.generate_response(
            prompt=message,
            relevant_documents=context_parts if context_parts else None,
            temperature=0.8,  # Slightly higher for more empathetic responses
            use_cache=True
        )
        
        return {
            'response': response,
            'tokens_used': tokens
        }
    
    def _handle_general_chat(
        self,
        message: str,
        conversation_context: List[Dict]
    ) -> Dict:
        """Handle general conversation."""
        print("💬 Handling general chat...")
        
        system_message = """You are a friendly AI learning assistant. Engage in natural conversation
while staying focused on helping the user with their learning journey."""
        
        messages = [{"role": "system", "content": system_message}]
        if conversation_context:
            messages.extend(conversation_context[-4:])
        messages.append({"role": "user", "content": message})
        
        full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        tokens = count_tokens(full_prompt)
        
        response = self.orchestrator.generate_response(
            prompt=message,
            temperature=0.8,
            use_cache=True
        )
        
        return {
            'response': response,
            'tokens_used': tokens
        }
    
    def _format_progress_report(self, progress: Dict) -> str:
        """Format progress data into a readable report."""
        report = f"""📊 **Your Learning Progress**

**Overall Progress:** {progress['completion_percentage']}% complete
({progress['completed_milestones']}/{progress['total_milestones']} milestones)

⏱️ **Time Spent:** {progress['time_spent_hours']} hours
"""
        
        # Current milestone
        if progress.get('current_milestone'):
            current = progress['current_milestone']
            report += f"\n🎯 **Current Milestone:** {current['title']}"
            report += f"\n   Estimated: {current['estimated_hours']} hours"
        
        # Estimated completion
        if progress.get('estimated_completion_date'):
            report += f"\n\n📅 **Estimated Completion:** {progress['estimated_completion_date']}"
        
        # Streak
        if progress.get('streak_days', 0) > 0:
            report += f"\n\n🔥 **Streak:** {progress['streak_days']} days - Keep it up!"
        
        # Pace analysis
        if progress.get('pace_analysis'):
            pace = progress['pace_analysis']
            report += f"\n\n📈 **Pace:** You're {pace['description']}"
        
        # Skills acquired
        if progress.get('skills_acquired'):
            skills = progress['skills_acquired'][:5]  # Show first 5
            if skills:
                report += f"\n\n✅ **Skills Acquired:**"
                for skill in skills:
                    report += f"\n   • {skill}"
                if len(progress['skills_acquired']) > 5:
                    report += f"\n   • ...and {len(progress['skills_acquired']) - 5} more!"
        
        # Insights
        if progress.get('insights'):
            report += "\n\n💡 **Insights:**"
            for insight in progress['insights'][:3]:  # Show top 3
                report += f"\n   • {insight}"
        
        return report

"""
Conversation Manager Service
Phase 1: Conversation Memory & Context Management

This service handles:
- Conversation history storage and retrieval
- Context window management (last N messages)
- Session management
- Message persistence
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from web_app import db
from web_app.models import ChatMessage, ConversationSession, User, UserLearningPath


class ConversationManager:
    """
    Manages conversation state, history, and context for the chatbot.
    
    Key Features:
    - Store and retrieve conversation history
    - Manage conversation sessions
    - Build context windows for AI
    - Track conversation metrics
    """
    
    def __init__(self, context_window_size: int = 10):
        """
        Initialize the conversation manager.
        
        Args:
            context_window_size: Number of recent messages to include in context (default: 10)
        """
        self.context_window_size = context_window_size
    
    def get_or_create_session(
        self,
        user_id: int,
        learning_path_id: Optional[str] = None
    ) -> ConversationSession:
        """
        Get active session or create a new one.
        
        Sessions expire after 30 minutes of inactivity.
        
        Args:
            user_id: User ID
            learning_path_id: Optional learning path ID
            
        Returns:
            ConversationSession object
        """
        # Check for active session in last 30 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        active_session = ConversationSession.query.filter(
            ConversationSession.user_id == user_id,
            ConversationSession.is_active == True,
            ConversationSession.last_activity_at >= cutoff_time
        ).order_by(ConversationSession.last_activity_at.desc()).first()
        
        if active_session:
            # Update last activity
            active_session.last_activity_at = datetime.utcnow()
            db.session.commit()
            return active_session
        
        # Create new session
        new_session = ConversationSession(
            user_id=user_id,
            learning_path_id=learning_path_id,
            is_active=True
        )
        db.session.add(new_session)
        db.session.commit()
        
        return new_session
    
    def add_message(
        self,
        user_id: int,
        message: str,
        role: str,
        learning_path_id: Optional[str] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
        tokens_used: int = 0,
        response_time_ms: Optional[int] = None
    ) -> ChatMessage:
        """
        Add a message to conversation history.
        
        Args:
            user_id: User ID
            message: Message content
            role: 'user' or 'assistant'
            learning_path_id: Optional learning path ID
            intent: Classified intent (from Phase 2)
            entities: Extracted entities (from Phase 2)
            tokens_used: Number of tokens used for this message
            response_time_ms: Response time in milliseconds
            
        Returns:
            ChatMessage object
        """
        # Get or create session
        session = self.get_or_create_session(user_id, learning_path_id)
        
        # Create message
        chat_message = ChatMessage(
            user_id=user_id,
            learning_path_id=learning_path_id,
            message=message,
            role=role,
            intent=intent,
            entities=entities,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            session_id=session.id
        )
        
        db.session.add(chat_message)
        
        # Update session stats
        session.message_count += 1
        session.total_tokens_used += tokens_used
        session.last_activity_at = datetime.utcnow()
        
        db.session.commit()
        
        return chat_message
    
    def get_conversation_history(
        self,
        user_id: int,
        learning_path_id: Optional[str] = None,
        limit: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            learning_path_id: Optional filter by learning path
            limit: Maximum number of messages to return
            session_id: Optional filter by session
            
        Returns:
            List of ChatMessage objects (ordered by timestamp)
        """
        query = ChatMessage.query.filter(ChatMessage.user_id == user_id)
        
        if learning_path_id:
            query = query.filter(ChatMessage.learning_path_id == learning_path_id)
        
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        
        query = query.order_by(ChatMessage.timestamp.asc())
        
        if limit:
            # Get the most recent N messages
            total_count = query.count()
            if total_count > limit:
                query = query.offset(total_count - limit)
        
        return query.all()
    
    def get_context_window(
        self,
        user_id: int,
        learning_path_id: Optional[str] = None,
        window_size: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context for AI.
        
        Returns messages in OpenAI chat format:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Args:
            user_id: User ID
            learning_path_id: Optional learning path ID
            window_size: Number of recent messages (default: self.context_window_size)
            
        Returns:
            List of message dictionaries in OpenAI format
        """
        window_size = window_size or self.context_window_size
        
        # Get recent messages
        messages = self.get_conversation_history(
            user_id=user_id,
            learning_path_id=learning_path_id,
            limit=window_size
        )
        
        # Convert to OpenAI format
        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.message
            })
        
        return context
    
    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        Get or generate session summary.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session summary text or None
        """
        session = ConversationSession.query.get(session_id)
        if not session:
            return None
        
        return session.summary
    
    def end_session(self, session_id: str, summary: Optional[str] = None):
        """
        End a conversation session.
        
        Args:
            session_id: Session ID
            summary: Optional session summary
        """
        session = ConversationSession.query.get(session_id)
        if session:
            session.is_active = False
            session.ended_at = datetime.utcnow()
            if summary:
                session.summary = summary
            db.session.commit()
    
    def get_conversation_stats(self, user_id: int) -> Dict:
        """
        Get conversation statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with conversation stats
        """
        total_messages = ChatMessage.query.filter(
            ChatMessage.user_id == user_id
        ).count()
        
        total_sessions = ConversationSession.query.filter(
            ConversationSession.user_id == user_id
        ).count()
        
        total_tokens = db.session.query(
            db.func.sum(ChatMessage.tokens_used)
        ).filter(
            ChatMessage.user_id == user_id
        ).scalar() or 0
        
        # Get intent distribution
        intent_counts = db.session.query(
            ChatMessage.intent,
            db.func.count(ChatMessage.id)
        ).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.intent.isnot(None)
        ).group_by(ChatMessage.intent).all()
        
        intent_distribution = {intent: count for intent, count in intent_counts}
        
        return {
            'total_messages': total_messages,
            'total_sessions': total_sessions,
            'total_tokens_used': total_tokens,
            'intent_distribution': intent_distribution
        }
    
    def clear_old_sessions(self, days: int = 30):
        """
        Archive old inactive sessions.
        
        Args:
            days: Number of days after which to archive sessions
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_sessions = ConversationSession.query.filter(
            ConversationSession.last_activity_at < cutoff_date,
            ConversationSession.is_active == True
        ).all()
        
        for session in old_sessions:
            session.is_active = False
            session.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        return len(old_sessions)

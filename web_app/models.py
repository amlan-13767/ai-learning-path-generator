from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web_app import db, login_manager # Assuming db and login_manager are initialized in __init__.py
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
import uuid

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    registration_source = db.Column(db.String(20), default='email_password')  # 'email_password', 'google', etc.
    google_subject = db.Column(db.String(255), unique=True, nullable=True, index=True)
    login_count = db.Column(db.Integer, default=0)
    
    # Profile information (optional)
    display_name = db.Column(db.String(100))  # For a more personalized display name vs username
    bio = db.Column(db.Text)
    
    # Relationships for Feature 1: User Accounts & Progress Tracking
    # A user can have multiple learning paths they've generated or saved
    learning_paths = db.relationship('UserLearningPath', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class UserLearningPath(db.Model):
    __tablename__ = 'user_learning_paths'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Storing the original AI-generated path data as JSON for now
    # This can be normalized further if needed for Feature 2 (Enhanced Resource Management)
    path_data_json = db.Column(db.JSON, nullable=False) 
    title = db.Column(db.String(200), nullable=True) # Extracted from path_data for easier display
    topic = db.Column(db.String(100), nullable=True) # Extracted from path_data
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)

    # Relationships for Feature 1: Progress Tracking
    # A learning path can have multiple progress entries (one per milestone)
    progress_entries = db.relationship('LearningProgress', backref='path', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<UserLearningPath {self.id} for User {self.user_id}>'

class LearningProgress(db.Model):
    __tablename__ = 'learning_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=False)
    # Assuming milestones have a unique identifier within the path_data_json
    # For simplicity, let's say milestone_title or an index can serve as this ID for now.
    # This might need refinement based on how milestones are structured in path_data_json.
    milestone_identifier = db.Column(db.String(200), nullable=False) 
    status = db.Column(db.String(50), default='not_started')  # e.g., 'not_started', 'in_progress', 'completed'
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    # For Feature 3 (Interactive Learning - Quizzes), we might add quiz attempts here or in a separate table

    __table_args__ = (db.UniqueConstraint('user_learning_path_id', 'milestone_identifier', name='_user_path_milestone_uc'),)

    def __repr__(self):
        return f'<LearningProgress for Milestone {self.milestone_identifier} in Path {self.user_learning_path_id}>'


class ResourceProgress(db.Model):
    """
    Tracks completion status of individual resources within milestones.
    Enables persistent progress tracking across sessions and devices.
    """
    __tablename__ = 'resource_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=False)
    milestone_index = db.Column(db.Integer, nullable=False)  # 0-based index of milestone
    resource_index = db.Column(db.Integer, nullable=False)  # 0-based index of resource within milestone
    resource_url = db.Column(db.String(500), nullable=False)  # Store URL for reference
    
    # Progress tracking
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one entry per user, path, milestone, and resource
    __table_args__ = (
        db.UniqueConstraint('user_id', 'learning_path_id', 'milestone_index', 'resource_index', 
                          name='_user_path_milestone_resource_uc'),
    )

    def __repr__(self):
        return f'<ResourceProgress User:{self.user_id} Path:{self.learning_path_id} M:{self.milestone_index} R:{self.resource_index} Completed:{self.completed}>'


class MilestoneProgress(db.Model):
    """
    Tracks completion status of entire milestones within learning paths.
    Provides high-level progress tracking for milestone completion.
    """
    __tablename__ = 'milestone_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=False)
    milestone_index = db.Column(db.Integer, nullable=False)  # 0-based index of milestone
    
    # Progress tracking
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one entry per user, path, and milestone
    __table_args__ = (
        db.UniqueConstraint('user_id', 'learning_path_id', 'milestone_index', 
                          name='_user_path_milestone_progress_uc'),
    )

    def __repr__(self):
        return f'<MilestoneProgress User:{self.user_id} Path:{self.learning_path_id} Milestone:{self.milestone_index} Completed:{self.completed}>'

# Models for Feature 2: Enhanced Resource Management (Placeholders, to be detailed later)
# class CustomResource(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     # ... fields for URL, title, description, type, tags ...

# class ResourceRating(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     resource_id = db.Column(db.Integer, db.ForeignKey('some_global_resource_table_or_original_resource_id'))
#     rating = db.Column(db.Integer) # 1-5
#     review = db.Column(db.Text)

# Models for Feature 3: Interactive Learning (Placeholders, to be detailed later)
# class Quiz(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     milestone_identifier = db.Column(db.String(200)) # Links to a milestone
#     # ... fields for quiz title, description ...

# class Question(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
#     # ... fields for question text, type (MCQ, code), options, correct_answer, explanation ...

# class UserQuizAttempt(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
#     score = db.Column(db.Float)
#     # ... fields for answers given, completion_date ...


# ============================================
# CONVERSATIONAL CHATBOT MODELS
# Phase 1: Conversation Memory System
# ============================================

class ChatMessage(db.Model):
    """
    Stores all conversation messages between user and AI assistant.
    
    Enhanced with:
    - Conversation memory and context
    - Multi-turn dialogue support
    - Learning path context tracking
    - Conversation analytics
    - Automatic cleanup utilities
    """
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=True)
    
    # Message content
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    
    # Conversation grouping (NEW: enhanced from session_id)
    conversation_id = db.Column(db.String(36), nullable=True, index=True)  # Groups related messages
    
    # Learning path context (NEW)
    context = db.Column(db.JSON, nullable=True)  # Stores path state, progress, current milestone
    
    # Intent classification (Phase 2)
    intent = db.Column(db.String(50), nullable=True)  # 'modify_path', 'check_progress', 'ask_question', 'general'
    entities = db.Column(db.JSON, nullable=True)  # Extracted entities from message
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    tokens_used = db.Column(db.Integer, default=0)  # Track API costs
    response_time_ms = db.Column(db.Integer, nullable=True)  # Performance tracking
    
    # Legacy field (kept for backward compatibility)
    session_id = db.Column(db.String(36), nullable=True, index=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.id} by User {self.user_id} ({self.role}) in Conversation {self.conversation_id}>'
    
    @staticmethod
    def get_conversation_history(conversation_id, limit=10):
        """
        Get recent messages from a conversation.
        
        Args:
            conversation_id: The conversation ID to fetch
            limit: Maximum number of messages to return (default: 10)
            
        Returns:
            List of ChatMessage objects, ordered by timestamp (oldest first)
        """
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(
            ChatMessage.timestamp.asc()
        ).limit(limit).all()
        
        return messages
    
    @staticmethod
    def get_recent_context(conversation_id):
        """
        Get the most recent context from a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Dictionary with learning path context, or None
        """
        # Get the most recent message with context
        message = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).filter(
            ChatMessage.context.isnot(None)
        ).order_by(
            ChatMessage.timestamp.desc()
        ).first()
        
        return message.context if message else None
    
    @staticmethod
    def clean_old_messages(days=7):
        """
        Delete messages older than specified days.
        
        Args:
            days: Number of days to keep (default: 7)
            
        Returns:
            Number of messages deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_messages = ChatMessage.query.filter(
            ChatMessage.timestamp < cutoff_date
        ).all()
        
        count = len(old_messages)
        
        for message in old_messages:
            db.session.delete(message)
        
        db.session.commit()
        
        return count
    
    @staticmethod
    def get_conversation_stats(conversation_id):
        """
        Get statistics about a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Dictionary with conversation statistics
        """
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).all()
        
        if not messages:
            return None
        
        user_messages = [m for m in messages if m.role == 'user']
        assistant_messages = [m for m in messages if m.role == 'assistant']
        
        total_tokens = sum(m.tokens_used for m in messages if m.tokens_used)
        avg_response_time = sum(m.response_time_ms for m in assistant_messages if m.response_time_ms) / len(assistant_messages) if assistant_messages else 0
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_tokens': total_tokens,
            'avg_response_time_ms': avg_response_time,
            'started_at': min(m.timestamp for m in messages),
            'last_message_at': max(m.timestamp for m in messages)
        }


class PathModification(db.Model):
    """
    Tracks all modifications made to learning paths via chatbot.
    
    This enables:
    - Modification history and audit trail
    - Undo functionality
    - Understanding user preferences
    - Path evolution tracking
    """
    __tablename__ = 'path_modifications'
    
    id = db.Column(db.Integer, primary_key=True)
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=True)
    
    # What changed
    modification_type = db.Column(db.String(50), nullable=False)  # 'add_resource', 'modify_milestone', 'split_milestone', etc.
    target_path = db.Column(db.String(200), nullable=True)  # JSON path to modified element (e.g., 'milestones[2].resources')
    
    # Change details
    change_description = db.Column(db.Text, nullable=False)  # Human-readable description
    old_value = db.Column(db.JSON, nullable=True)  # Previous value (for undo)
    new_value = db.Column(db.JSON, nullable=True)  # New value
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_reverted = db.Column(db.Boolean, default=False)  # If user undid this change
    
    def __repr__(self):
        return f'<PathModification {self.id} for Path {self.learning_path_id}>'


class ConversationSession(db.Model):
    """
    Groups related chat messages into sessions.
    
    This enables:
    - Session-based context management
    - Conversation analytics
    - Session summaries
    - Better context window management
    """
    __tablename__ = 'conversation_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'), nullable=True)
    
    # Session metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Session summary (generated by AI)
    summary = db.Column(db.Text, nullable=True)
    
    # Session stats
    message_count = db.Column(db.Integer, default=0)
    total_tokens_used = db.Column(db.Integer, default=0)
    
    # Session state
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ConversationSession {self.id} for User {self.user_id}>'


class OAuth(OAuthConsumerMixin, db.Model):
    """Store OAuth tokens for Flask-Dance"""
    __tablename__ = 'flask_dance_oauth'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='oauth_tokens')

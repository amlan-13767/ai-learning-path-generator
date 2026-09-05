"""
Database Migration: Add Conversational Chatbot Tables

Run this to create the new tables for:
- ChatMessage (conversation history)
- PathModification (modification tracking)
- ConversationSession (session management)

Usage:
    python -m migrations.add_chatbot_tables
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def run_migration():
    """Create the new chatbot tables."""
    print("Initializing database migration...")
    
    try:
        # Import only what we need to avoid loading heavy dependencies
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from dotenv import load_dotenv
        
        # Load environment variables
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        
        # Create minimal Flask app
        app = Flask(__name__)
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL', 'sqlite:///learning_path.db')
        
        # Fix SQLite path if needed
        if database_url.startswith('sqlite:///') and not database_url.startswith('sqlite:////'):
            db_path = database_url.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(project_root, db_path)
                database_url = f'sqlite:///{db_path}'
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        # Define the models directly here to avoid import issues
        with app.app_context():
            print(f"Using database: {database_url}")
            print("\nCreating chatbot tables...")
            
            # Execute raw SQL to create tables
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    learning_path_id VARCHAR(36),
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    summary TEXT,
                    message_count INTEGER DEFAULT 0,
                    total_tokens_used INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (learning_path_id) REFERENCES user_learning_paths(id)
                )
            """))
            
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    learning_path_id VARCHAR(36),
                    message TEXT NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    intent VARCHAR(50),
                    entities TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER,
                    session_id VARCHAR(36),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (learning_path_id) REFERENCES user_learning_paths(id),
                    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id)
                )
            """))
            
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS path_modifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_path_id VARCHAR(36) NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_message_id INTEGER,
                    modification_type VARCHAR(50) NOT NULL,
                    target_path VARCHAR(200),
                    change_description TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_reverted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (learning_path_id) REFERENCES user_learning_paths(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (chat_message_id) REFERENCES chat_messages(id)
                )
            """))
            
            db.session.commit()
            
            print("✅ Successfully created chatbot tables:")
            print("   - conversation_sessions")
            print("   - chat_messages")
            print("   - path_modifications")
            print("\n🎉 Your database is ready for the enhanced chatbot!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_migration()

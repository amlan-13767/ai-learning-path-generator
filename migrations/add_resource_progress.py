"""
Migration script to add ResourceProgress table for persistent resource tracking.
Run this after updating models.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import create_app, db
from web_app.models import ResourceProgress

def migrate():
    """Create the resource_progress table"""
    app = create_app()
    
    with app.app_context():
        print("Creating resource_progress table...")
        
        # Create the table
        db.create_all()
        
        print("✅ ResourceProgress table created successfully!")
        print("\nTable structure:")
        print("- id (Primary Key)")
        print("- user_id (Foreign Key -> users.id)")
        print("- learning_path_id (Foreign Key -> user_learning_paths.id)")
        print("- milestone_index (Integer)")
        print("- resource_index (Integer)")
        print("- resource_url (String)")
        print("- completed (Boolean)")
        print("- completed_at (DateTime)")
        print("- created_at (DateTime)")
        print("- updated_at (DateTime)")
        print("\n✨ Users can now track resource completion persistently!")

if __name__ == "__main__":
    migrate()

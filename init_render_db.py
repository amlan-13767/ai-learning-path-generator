#!/usr/bin/env python3
"""
Initialize PostgreSQL database on Render.
This script runs database migrations to create all required tables.
"""
import os
import sys
from flask_migrate import upgrade
from web_app import create_app, db

def init_database():
    """Initialize database with migrations"""
    print("=" * 60)
    print("🔧 Initializing PostgreSQL Database on Render")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("Please configure PostgreSQL in Render dashboard.")
        sys.exit(1)
    
    print(f"✅ Database URL found: {database_url[:30]}...")
    
    # Create Flask app
    print("\n📦 Creating Flask application...")
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Checking database connection...")
        try:
            # Test database connection
            db.engine.connect()
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
        
        print("\n🚀 Running database migrations...")
        try:
            # Run all migrations
            upgrade()
            print("✅ Database migrations completed successfully!")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
            print("\nAttempting to create missing tables...")
            try:
                # Create tables if they don't exist (ignores existing ones)
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                existing_tables = inspector.get_table_names()
                print(f"📋 Existing tables: {', '.join(existing_tables)}")
                
                # Only create tables that don't exist
                db.create_all()
                print("✅ Database schema verified/updated!")
            except Exception as e2:
                # If it fails due to existing constraints, that's actually OK
                if "already exists" in str(e2).lower():
                    print("⚠️  Some tables/constraints already exist - this is OK!")
                    print("✅ Database schema is ready!")
                else:
                    print(f"❌ Failed to create tables: {e2}")
                    sys.exit(1)
        
        print("\n🔍 Verifying tables...")
        try:
            # Check if users table exists
            from web_app.models import User
            user_count = User.query.count()
            print(f"✅ Users table exists (current count: {user_count})")
        except Exception as e:
            print(f"❌ Users table verification failed: {e}")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print("\nYour database is ready to use. You can now:")
        print("1. Register new users")
        print("2. Login with Google OAuth")
        print("3. Create learning paths")
        print("\n")

if __name__ == "__main__":
    init_database()

#!/usr/bin/env python3
"""Initialize database tables for production deployment."""
import os
from web_app import create_app, db

# Create Flask app
app = create_app()

with app.app_context():
    print("Creating database tables...")
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
    except Exception as e:
        # If tables/constraints already exist, that's OK
        if "already exists" in str(e).lower():
            print("⚠️  Some tables/constraints already exist - continuing...")
            print("✅ Database is ready!")
        else:
            print(f"❌ Error creating tables: {e}")
            raise

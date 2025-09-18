#!/usr/bin/env python3
"""
Database Setup Script for Course Recommendation System
Initializes the database and loads sample course data
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database_utils import initialize_database, insert_course, bulk_generate_embeddings
from dotenv import load_dotenv


def load_sample_data():
    """Load sample course data into the database."""
    sample_data_path = Path(__file__).parent.parent / "data" / "sample_courses.json"
    
    if not sample_data_path.exists():
        print("❌ Sample data file not found!")
        return False
    
    try:
        with open(sample_data_path, 'r') as f:
            courses = json.load(f)
        
        print(f"📚 Loading {len(courses)} sample courses...")
        
        success_count = 0
        for course in courses:
            if insert_course(course):
                success_count += 1
                print(f"✅ Loaded: {course['title']}")
            else:
                print(f"❌ Failed: {course['title']}")
        
        print(f"\n🎉 Successfully loaded {success_count}/{len(courses)} courses!")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return False


def setup_database():
    """Complete database setup process."""
    print("🚀 Starting Course Recommendation Database Setup")
    print("=" * 50)
    
    # Load environment variables from specific .env file only
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path, override=False)
    
    # Check for required environment variables
    required_vars = ['WATSONX_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure to copy .env.example to .env and fill in your credentials")
        print("📖 See README.md for setup instructions")
    
    # Initialize database structure
    print("\n📊 Initializing database structure...")
    try:
        initialize_database()
        print("✅ Database structure created successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Load sample data
    print("\n📚 Loading sample course data...")
    if not load_sample_data():
        print("⚠️  Failed to load sample data, but database structure is ready")
    
    # Generate embeddings if API key is available
    if os.getenv('WATSONX_API_KEY'):
        print("\n🧠 Generating course embeddings with IBM Watsonx...")
        try:
            bulk_generate_embeddings()
            print("✅ Embeddings generated successfully!")
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            print("💡 You can generate embeddings later when API credentials are configured")
    else:
        print("\n⚠️  Skipping embedding generation (WATSONX_API_KEY not set)")
        print("💡 Configure your API key and run this script again to generate embeddings")
    
    print("\n🎉 Database setup complete!")
    print("\n📋 Next steps:")
    print("1. Configure your .env file with API credentials")
    print("2. Run: streamlit run app.py")
    print("3. Start exploring course recommendations!")
    
    return True


if __name__ == "__main__":
    setup_database()
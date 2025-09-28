#!/usr/bin/env python3
"""
Comprehensive functionality test suite for AI Course Recommender
Tests all major components and functions
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

def test_database_initialization():
    """Test database initialization and basic operations"""
    print("\n🔍 Testing Database Initialization...")
    try:
        from database_utils import initialize_database, get_database_stats
        
        # Initialize database
        initialize_database()
        print("✅ Database initialized successfully")
        
        # Get stats
        stats = get_database_stats()
        print(f"📊 Database Stats:")
        print(f"   - Total courses: {stats['total_courses']}")
        print(f"   - Courses with embeddings: {stats['courses_with_embeddings']}")
        print(f"   - Skill level distribution: {stats['level_distribution']}")
        print(f"   - Provider distribution: {stats.get('provider_distribution', 'N/A')}")
        
        assert stats['total_courses'] > 0, "No courses in database"
        assert stats['courses_with_embeddings'] > 0, "No embeddings generated"
        print("✅ Database tests passed!")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_vector_search():
    """Test vector search functionality"""
    print("\n🔍 Testing Vector Search...")
    try:
        from vector_search import search_courses_by_vector
        
        # Test search queries
        test_queries = [
            "python programming for beginners",
            "machine learning with tensorflow",
            "web development",
            "cloud computing AWS"
        ]
        
        for query in test_queries:
            print(f"\n   Testing query: '{query}'")
            results = search_courses_by_vector(query, limit=3)
            
            assert len(results) > 0, f"No results for query: {query}"
            
            # Display results
            for i, course in enumerate(results[:2], 1):
                # Handle CourseSearchResult object
                if hasattr(course, 'title'):
                    print(f"   {i}. {course.title} (Score: {course.similarity_score:.3f})")
                else:
                    print(f"   {i}. {course.get('title', 'N/A')} (Score: {course.get('similarity_score', 0):.3f})")
        
        print("✅ Vector search tests passed!")
        return True
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False

def test_course_analytics():
    """Test course analytics and recommendation system"""
    print("\n🔍 Testing Course Analytics...")
    try:
        from course_analytics import course_recommendation_rag
        
        # Test user preferences
        user_preferences = {
            'skill_level': 'intermediate',
            'modality': 'online',
            'max_duration_hours': 50,
            'background': 'Software developer with basic Python knowledge'
        }
        
        # Test queries
        test_queries = [
            "I want to learn data science",
            "Help me become a machine learning engineer"
        ]
        
        for query in test_queries:
            print(f"\n   Testing recommendation for: '{query}'")
            result = course_recommendation_rag(query, user_preferences)
            
            assert result is not None, "No result returned"
            assert 'recommendations' in result, "No recommendations in result"
            assert len(result['recommendations']) > 0, "Empty recommendations list"
            
            # Display top recommendations
            for i, rec in enumerate(result['recommendations'][:2], 1):
                print(f"   {i}. {rec['title']} - {rec['recommendation_reason'][:50]}...")
                print(f"      Score: {rec['recommendation_score']:.3f} | Level: {rec['level']}")
        
        print("✅ Course analytics tests passed!")
        return True
    except Exception as e:
        print(f"❌ Course analytics test failed: {e}")
        return False

def test_ui_components():
    """Test UI component imports"""
    print("\n🔍 Testing UI Components...")
    try:
        from ui.components.course_card import render_course_card
        from ui.components.chat_interface import render_chat_interface
        from ui.components.learning_path import render_learning_path_visualization
        
        print("✅ All UI components imported successfully")
        return True
    except Exception as e:
        print(f"❌ UI component test failed: {e}")
        return False

def test_watsonx_connection():
    """Test IBM Watsonx connection"""
    print("\n🔍 Testing IBM Watsonx Connection...")
    try:
        from langchain_ibm import WatsonxEmbeddings
        
        # Check environment variables
        api_key = os.getenv('WATSONX_API_KEY')
        project_id = os.getenv('WATSONX_PROJECT_ID')
        url = os.getenv('WATSONX_URL')
        
        assert api_key, "WATSONX_API_KEY not found in environment"
        assert project_id, "WATSONX_PROJECT_ID not found in environment"
        assert url, "WATSONX_URL not found in environment"
        
        print(f"   API Key: {'*' * 10}{api_key[-4:]}")
        print(f"   Project ID: {project_id}")
        print(f"   URL: {url}")
        
        # Initialize embeddings
        embeddings = WatsonxEmbeddings(
            model_id="ibm/slate-30m-english-rtrvr",
            url=url,
            apikey=api_key,
            project_id=project_id
        )
        
        # Test embedding generation
        test_text = "Test embedding generation"
        embedding = embeddings.embed_query(test_text)
        
        assert len(embedding) > 0, "Empty embedding returned"
        print(f"   Embedding dimension: {len(embedding)}")
        print("✅ Watsonx connection test passed!")
        return True
    except Exception as e:
        print(f"❌ Watsonx connection test failed: {e}")
        return False

def test_streamlit_imports():
    """Test Streamlit and required imports"""
    print("\n🔍 Testing Streamlit Dependencies...")
    try:
        import streamlit as st
        import plotly.express as px
        import pandas as pd
        
        print(f"   Streamlit version: {st.__version__}")
        print("✅ Streamlit imports successful")
        return True
    except Exception as e:
        print(f"❌ Streamlit import test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("=" * 60)
    print("🚀 AI COURSE RECOMMENDER - COMPREHENSIVE FUNCTIONALITY TEST")
    print("=" * 60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    results = {
        'Database': test_database_initialization(),
        'Vector Search': test_vector_search(),
        'Watsonx Connection': test_watsonx_connection(),
        'Course Analytics': test_course_analytics(),
        'UI Components': test_ui_components(),
        'Streamlit': test_streamlit_imports()
    }
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(results))*100:.1f}%")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! The application is fully functional.")
        print("\n📝 Next Steps:")
        print("1. Run the Streamlit app: streamlit run app.py")
        print("2. Access at: http://localhost:8501")
        print("3. Start searching for courses!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
"""
SQLite database utilities for course recommendation system.
Provides database setup, course management, and embedding operations.
"""

import sqlite3
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from langchain_ibm import WatsonxEmbeddings
from dotenv import load_dotenv


def get_database_path() -> str:
    """Get the path to the SQLite database."""
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'course_catalog.db')


def initialize_database():
    """Initialize the SQLite database with required tables."""
    db_path = get_database_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create course catalog table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_catalog (
            course_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            provider TEXT,
            level TEXT,
            duration_hours INTEGER,
            modality TEXT,
            tags TEXT,  -- JSON array of tags
            prerequisites TEXT,  -- JSON array of prerequisites
            valid_regions TEXT,  -- JSON array of regions
            course_content TEXT,
            content_embedding BLOB,  -- Numpy array stored as blob
            course_rating REAL DEFAULT 0.0,
            enrollment_count INTEGER DEFAULT 0,
            certification_offered BOOLEAN DEFAULT FALSE,
            certification_body TEXT,
            price REAL,
            instructor_name TEXT,
            instructor_credentials TEXT,
            instructor_experience INTEGER,
            instructor_bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON course_catalog(level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_modality ON course_catalog(modality)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider ON course_catalog(provider)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_duration ON course_catalog(duration_hours)")
    
    # Create user profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            preferences TEXT,  -- JSON object with user preferences
            completed_courses TEXT,  -- JSON array of completed course IDs
            learning_goals TEXT,  -- JSON array of learning goals
            skill_assessments TEXT,  -- JSON object with skill levels
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create learning paths table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_paths (
            path_id TEXT PRIMARY KEY,
            user_id TEXT,
            path_name TEXT,
            path_description TEXT,
            course_sequence TEXT,  -- JSON array of course IDs in order
            target_skill_level TEXT,
            estimated_duration_hours INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
        )
    """)
    
    conn.commit()
    conn.close()


def insert_course(course_data: Dict[str, Any]) -> bool:
    """Insert a new course into the database."""
    db_path = get_database_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO course_catalog (
                course_id, title, provider, level, duration_hours, modality,
                tags, prerequisites, valid_regions, course_content,
                course_rating, enrollment_count, certification_offered,
                certification_body, price, instructor_name, instructor_credentials,
                instructor_experience, instructor_bio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            course_data.get('course_id'),
            course_data.get('title'),
            course_data.get('provider'),
            course_data.get('level'),
            course_data.get('duration_hours'),
            course_data.get('modality'),
            json.dumps(course_data.get('tags', [])),
            json.dumps(course_data.get('prerequisites', [])),
            json.dumps(course_data.get('valid_regions', [])),
            course_data.get('course_content'),
            course_data.get('course_rating', 0.0),
            course_data.get('enrollment_count', 0),
            course_data.get('certification_offered', False),
            course_data.get('certification_body'),
            course_data.get('price'),
            course_data.get('instructor_name'),
            course_data.get('instructor_credentials'),
            course_data.get('instructor_experience'),
            course_data.get('instructor_bio')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error inserting course: {e}")
        return False


def update_course_embedding(course_id: str, embedding: List[float]) -> bool:
    """Update the embedding for a specific course."""
    db_path = get_database_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Convert embedding to numpy array and store as blob
        embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
        
        cursor.execute("""
            UPDATE course_catalog 
            SET content_embedding = ?, updated_at = CURRENT_TIMESTAMP
            WHERE course_id = ?
        """, (embedding_blob, course_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating embedding: {e}")
        return False


def bulk_generate_embeddings():
    """Generate embeddings for all courses without embeddings using IBM Watsonx."""
    # Load environment variables from specific .env file only
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path, override=False)
    
    # Initialize IBM Watsonx embeddings
    watsonx_api_key = os.getenv('WATSONX_API_KEY')
    watsonx_project_id = os.getenv('WATSONX_PROJECT_ID')
    
    if not watsonx_api_key:
        raise ValueError("WATSONX_API_KEY environment variable is required")
    
    if not watsonx_project_id:
        raise ValueError("WATSONX_PROJECT_ID environment variable is required")
    
    embeddings = WatsonxEmbeddings(
        model_id="intfloat/multilingual-e5-large",
        url='https://us-south.ml.cloud.ibm.com',
        project_id=watsonx_project_id,
        apikey=watsonx_api_key,
        params={
            "truncate_input_tokens": 512,
            "return_options": {
                "input_text": False
            }
        }
    )
    
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get courses without embeddings
    cursor.execute("""
        SELECT course_id, title, course_content, tags, provider
        FROM course_catalog 
        WHERE content_embedding IS NULL
    """)
    
    courses = cursor.fetchall()
    
    if not courses:
        print("All courses already have embeddings")
        conn.close()
        return
    
    print(f"Generating embeddings for {len(courses)} courses...")
    
    for course_id, title, content, tags_json, provider in courses:
        try:
            # Create comprehensive text for embedding
            tags = json.loads(tags_json) if tags_json else []
            text_parts = [title]
            
            if content:
                text_parts.append(content)
            if provider:
                text_parts.append(f"Provider: {provider}")
            if tags:
                text_parts.append(f"Topics: {', '.join(tags)}")
                
            full_text = " | ".join(text_parts)
            
            # Generate embedding
            embedding = embeddings.embed_query(full_text)
            
            # Store embedding
            if update_course_embedding(course_id, embedding):
                print(f"✓ Generated embedding for: {title}")
            else:
                print(f"✗ Failed to store embedding for: {title}")
                
        except Exception as e:
            print(f"✗ Error processing {title}: {e}")
    
    conn.close()
    print("Embedding generation complete!")


def get_course_count() -> int:
    """Get total number of courses in the database."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM course_catalog")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def get_courses_with_embeddings_count() -> int:
    """Get number of courses that have embeddings."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM course_catalog WHERE content_embedding IS NOT NULL")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def search_courses_by_keywords(keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """Search courses by keywords in title, content, or tags."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build search query
    search_conditions = []
    params = []
    
    for keyword in keywords:
        search_conditions.append("(title LIKE ? OR course_content LIKE ? OR tags LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    
    query = f"""
        SELECT course_id, title, provider, level, duration_hours, modality,
               tags, prerequisites, valid_regions, course_content
        FROM course_catalog
        WHERE {' OR '.join(search_conditions)}
        LIMIT ?
    """
    params.append(limit)
    
    cursor.execute(query, params)
    results = []
    
    for row in cursor.fetchall():
        results.append({
            'course_id': row[0],
            'title': row[1],
            'provider': row[2],
            'level': row[3],
            'duration_hours': row[4],
            'modality': row[5],
            'tags': json.loads(row[6]) if row[6] else [],
            'prerequisites': json.loads(row[7]) if row[7] else [],
            'valid_regions': json.loads(row[8]) if row[8] else [],
            'course_content': row[9]
        })
    
    conn.close()
    return results


def get_database_stats() -> Dict[str, Any]:
    """Get comprehensive database statistics."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total courses
    cursor.execute("SELECT COUNT(*) FROM course_catalog")
    stats['total_courses'] = cursor.fetchone()[0]
    
    # Courses with embeddings
    cursor.execute("SELECT COUNT(*) FROM course_catalog WHERE content_embedding IS NOT NULL")
    stats['courses_with_embeddings'] = cursor.fetchone()[0]
    
    # Level distribution
    cursor.execute("SELECT level, COUNT(*) FROM course_catalog GROUP BY level")
    stats['level_distribution'] = dict(cursor.fetchall())
    
    # Modality distribution
    cursor.execute("SELECT modality, COUNT(*) FROM course_catalog GROUP BY modality")
    stats['modality_distribution'] = dict(cursor.fetchall())
    
    # Provider distribution
    cursor.execute("SELECT provider, COUNT(*) FROM course_catalog GROUP BY provider ORDER BY COUNT(*) DESC LIMIT 10")
    stats['top_providers'] = dict(cursor.fetchall())
    
    # Duration statistics
    cursor.execute("SELECT AVG(duration_hours), MIN(duration_hours), MAX(duration_hours) FROM course_catalog WHERE duration_hours > 0")
    avg_dur, min_dur, max_dur = cursor.fetchone()
    stats['duration_stats'] = {
        'average': avg_dur,
        'minimum': min_dur,
        'maximum': max_dur
    }
    
    conn.close()
    return stats


if __name__ == "__main__":
    # Initialize database and show stats
    print("Initializing course recommendation database...")
    initialize_database()
    
    stats = get_database_stats()
    print(f"\nDatabase Statistics:")
    print(f"Total courses: {stats['total_courses']}")
    print(f"Courses with embeddings: {stats['courses_with_embeddings']}")
    print(f"Level distribution: {stats['level_distribution']}")
    print(f"Modality distribution: {stats['modality_distribution']}")
    
    if stats['total_courses'] > 0 and stats['courses_with_embeddings'] == 0:
        print("\nGenerating embeddings for all courses...")
        bulk_generate_embeddings()
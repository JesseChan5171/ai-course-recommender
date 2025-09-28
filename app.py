#!/usr/bin/env python3
"""
🎓 AI-Powered Course Recommendation System - Streamlit UI
Ultra-sophisticated interface for intelligent course discovery and learning path generation.
"""

import streamlit as st
import sys
import os
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional

# Add src to path for imports
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from course_analytics import course_recommendation_rag
    from vector_search import search_courses_by_vector
    from database_utils import get_database_stats, initialize_database
    
    # Test database connection to ensure backend is working
    stats = get_database_stats()
    BACKEND_AVAILABLE = True
except Exception as e:
    st.error(f"Backend not available: {e}")
    BACKEND_AVAILABLE = False

# Import UI components
try:
    from ui.components.course_card import render_course_card, render_course_grid
    from ui.components.chat_interface import render_chat_interface, add_message_to_history
    from ui.components.learning_path import render_learning_path_visualization
    UI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    st.warning(f"Some UI components not available: {e}")
    UI_COMPONENTS_AVAILABLE = False

# Configure Streamlit page
st.set_page_config(
    page_title="🎓 AI Course Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/course-recommender/help',
        'Report a bug': 'https://github.com/course-recommender/issues',
        'About': '''
        # AI-Powered Course Recommendation System
        
        Built with IBM Watsonx, LangChain, and LangGraph
        
        **Features:**
        - Semantic course search
        - Personalized recommendations
        - Learning path generation
        - Skill gap analysis
        '''
    }
)

# Utility functions
def validate_user_input(query: str) -> bool:
    """
    Validate user input for search queries.
    
    Args:
        query: User search query
        
    Returns:
        bool: True if input is valid, False otherwise
    """
    if not query or not query.strip():
        return False
    
    # Check minimum length
    if len(query.strip()) < 2:
        return False
    
    # Check for potentially harmful content (basic security)
    harmful_patterns = ['<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=']
    query_lower = query.lower()
    if any(pattern in query_lower for pattern in harmful_patterns):
        return False
    
    # Check maximum length (prevent very long queries)
    if len(query) > 500:
        return False
    
    return True


def sanitize_query(query: str) -> str:
    """
    Sanitize and clean user query.
    
    Args:
        query: Raw user query
        
    Returns:
        str: Sanitized query
    """
    if not query:
        return ""
    
    # Strip whitespace and normalize
    clean_query = query.strip()
    
    # Remove multiple spaces
    import re
    clean_query = re.sub(r'\s+', ' ', clean_query)
    
    # Remove potentially harmful characters but keep basic punctuation
    clean_query = re.sub(r'[<>"\']', '', clean_query)
    
    return clean_query


# Custom CSS styling
def load_custom_css():
    """Load custom CSS for enhanced UI styling."""
    css_file = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
            # Add cache-busting comment
            css_content = f"/* Cache bust: {datetime.now().isoformat()} */\n" + css_content
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # Embedded CSS if file doesn't exist
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
            display: flex !important;
            align-items: center !important;
            gap: 2rem !important;
            text-align: left !important;
        }
        
        .tree-container {
            flex-shrink: 0;
            width: 120px;
            height: 140px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
        }
        
        .growing-tree {
            width: 100px;
            height: 120px;
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.2));
        }
        
        .header-content {
            flex: 1;
            min-width: 0;
        }
        
        .main-header h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2.5rem;
        }
        
        .main-header p {
            margin: 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Hide Streamlit default elements for cleaner look */
        #MainMenu {visibility: hidden;}
        .stDeployButton {display: none;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .score-badge {
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-weight: bold;
        }
        
        .chat-message {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .user-message {
            background: #e3f2fd;
            text-align: right;
        }
        
        .ai-message {
            background: #f3e5f5;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .learning-path-step {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        /* Tree Animation Styles */
        .tree-trunk {
            stroke-dasharray: 40;
            stroke-dashoffset: 40;
            animation: drawBranch 1s ease-out forwards;
        }
        
        .tree-branch-1 {
            stroke-dasharray: 25;
            stroke-dashoffset: 25;
            animation: drawBranch 0.8s ease-out 1s forwards;
        }
        
        .tree-branch-2 {
            stroke-dasharray: 25;
            stroke-dashoffset: 25;
            animation: drawBranch 0.8s ease-out 1.1s forwards;
        }
        
        .tree-branch-3 {
            stroke-dasharray: 20;
            stroke-dashoffset: 20;
            animation: drawBranch 0.6s ease-out 1.8s forwards;
        }
        
        .tree-branch-4 {
            stroke-dasharray: 20;
            stroke-dashoffset: 20;
            animation: drawBranch 0.6s ease-out 1.9s forwards;
        }
        
        .tree-branch-5 {
            stroke-dasharray: 18;
            stroke-dashoffset: 18;
            animation: drawBranch 0.6s ease-out 2s forwards;
        }
        
        .tree-branch-6 {
            stroke-dasharray: 15;
            stroke-dashoffset: 15;
            animation: drawBranch 0.5s ease-out 2.4s forwards;
        }
        
        .tree-branch-7 {
            stroke-dasharray: 15;
            stroke-dashoffset: 15;
            animation: drawBranch 0.5s ease-out 2.5s forwards;
        }
        
        .tree-branch-8 {
            stroke-dasharray: 12;
            stroke-dashoffset: 12;
            animation: drawBranch 0.4s ease-out 2.6s forwards;
        }
        
        .tree-branch-9 {
            stroke-dasharray: 8;
            stroke-dashoffset: 8;
            animation: drawBranch 0.3s ease-out 2.9s forwards;
        }
        
        .tree-branch-10 {
            stroke-dasharray: 8;
            stroke-dashoffset: 8;
            animation: drawBranch 0.3s ease-out 3s forwards;
        }
        
        .tree-leaves {
            opacity: 0;
            transform: scale(0.8);
            animation: growLeaves 1s ease-out 3.2s forwards;
        }
        
        .tree-leaves circle {
            transform-origin: center;
            animation: leafFloat 3s ease-in-out infinite;
        }
        
        .tree-leaves circle:nth-child(1) { animation-delay: 0s; }
        .tree-leaves circle:nth-child(2) { animation-delay: 0.2s; }
        .tree-leaves circle:nth-child(3) { animation-delay: 0.4s; }
        .tree-leaves circle:nth-child(4) { animation-delay: 0.6s; }
        .tree-leaves circle:nth-child(5) { animation-delay: 0.8s; }
        .tree-leaves circle:nth-child(6) { animation-delay: 1s; }
        
        @keyframes drawBranch {
            from {
                stroke-dashoffset: 100;
            }
            to {
                stroke-dashoffset: 0;
            }
        }
        
        @keyframes growLeaves {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        @keyframes leafFloat {
            0%, 100% {
                transform: translateY(0px) rotate(0deg);
            }
            33% {
                transform: translateY(-2px) rotate(1deg);
            }
            66% {
                transform: translateY(1px) rotate(-1deg);
            }
        }
        
        /* Responsive tree design */
        @media (max-width: 768px) {
            .main-header {
                flex-direction: column !important;
                text-align: center !important;
                gap: 1rem !important;
            }
            
            .tree-container {
                width: 80px;
                height: 100px;
            }
            
            .growing-tree {
                width: 70px;
                height: 85px;
            }
            
            .header-content h1 {
                font-size: 2rem !important;
                text-align: center !important;
            }
            
            .header-content p {
                text-align: center !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_recommendations' not in st.session_state:
        st.session_state.current_recommendations = None
    
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'skill_level': 'beginner',
            'modality': 'online',
            'max_duration_hours': 100,
            'background': '',
            'completed_courses': [],
            'preferences': {}
        }
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'favorite_courses' not in st.session_state:
        st.session_state.favorite_courses = []

def render_main_header():
    """Render the main application header with animated growing tree."""
    
    # Create the tree SVG as a separate string to avoid parsing issues
    tree_svg = '''<svg class="growing-tree" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
<path class="tree-trunk" d="M50 120 L50 80" stroke="rgba(139, 120, 93, 0.9)" stroke-width="4" fill="none" stroke-linecap="round"/>
<path class="tree-branch-1" d="M50 80 L35 65" stroke="rgba(139, 120, 93, 0.9)" stroke-width="3" fill="none" stroke-linecap="round"/>
<path class="tree-branch-2" d="M50 80 L65 65" stroke="rgba(139, 120, 93, 0.9)" stroke-width="3" fill="none" stroke-linecap="round"/>
<path class="tree-branch-3" d="M35 65 L25 55" stroke="rgba(139, 120, 93, 0.8)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path class="tree-branch-4" d="M65 65 L75 55" stroke="rgba(139, 120, 93, 0.8)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path class="tree-branch-5" d="M50 82 L40 70" stroke="rgba(139, 120, 93, 0.8)" stroke-width="2" fill="none" stroke-linecap="round"/>
<path class="tree-branch-6" d="M35 65 L30 50" stroke="rgba(139, 120, 93, 0.7)" stroke-width="1.5" fill="none" stroke-linecap="round"/>
<path class="tree-branch-7" d="M65 65 L70 50" stroke="rgba(139, 120, 93, 0.7)" stroke-width="1.5" fill="none" stroke-linecap="round"/>
<path class="tree-branch-8" d="M40 70 L32 60" stroke="rgba(139, 120, 93, 0.7)" stroke-width="1.5" fill="none" stroke-linecap="round"/>
<path class="tree-branch-9" d="M25 55 L22 48" stroke="rgba(139, 120, 93, 0.6)" stroke-width="1" fill="none" stroke-linecap="round"/>
<path class="tree-branch-10" d="M75 55 L78 48" stroke="rgba(139, 120, 93, 0.6)" stroke-width="1" fill="none" stroke-linecap="round"/>
<g class="tree-leaves">
<circle cx="22" cy="48" r="6" fill="rgba(34, 197, 94, 0.8)"/>
<circle cx="30" cy="50" r="7" fill="rgba(34, 197, 94, 0.9)"/>
<circle cx="78" cy="48" r="6" fill="rgba(34, 197, 94, 0.8)"/>
<circle cx="70" cy="50" r="7" fill="rgba(34, 197, 94, 0.9)"/>
<circle cx="32" cy="60" r="5" fill="rgba(74, 222, 128, 0.8)"/>
<circle cx="45" cy="68" r="6" fill="rgba(34, 197, 94, 0.8)"/>
<circle cx="38" cy="58" r="4" fill="rgba(74, 222, 128, 0.7)"/>
<circle cx="62" cy="58" r="4" fill="rgba(74, 222, 128, 0.7)"/>
<circle cx="28" cy="54" r="3" fill="rgba(74, 222, 128, 0.9)"/>
<circle cx="72" cy="54" r="3" fill="rgba(74, 222, 128, 0.9)"/>
</g>
</svg>'''
    
    # Header with animated tree using f-string formatting
    header_html = f'''
    <div class="main-header">
        <div class="tree-container">
            {tree_svg}
        </div>
        <div class="header-content">
            <h1>🎓 AI Course Recommender</h1>
            <p>Discover your perfect learning journey with intelligent recommendations</p>
        </div>
    </div>
    '''
    
    st.markdown(header_html, unsafe_allow_html=True)

def render_breadcrumb_navigation():
    """Render breadcrumb navigation for better orientation."""
    current_page = st.session_state.get('current_page', 'home')
    
    breadcrumb_map = {
        'home': '🏠 Home',
        'search': '🔍 Search',
        'recommendations': '🎯 Recommendations', 
        'learning_path': '🛤️ Learning Path',
        'favorites': '❤️ Favorites',
        'profile': '👤 Profile'
    }
    
    breadcrumb_html = '<div class="breadcrumb-nav">'
    for key, label in breadcrumb_map.items():
        if key == current_page:
            breadcrumb_html += f'<span class="breadcrumb-current">{label}</span>'
        else:
            breadcrumb_html += f'<span class="breadcrumb-link">{label}</span>'
        if key != list(breadcrumb_map.keys())[-1]:
            breadcrumb_html += ' <span class="breadcrumb-separator">›</span> '
    breadcrumb_html += '</div>'
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)

def render_user_journey_indicator():
    """Show where the user is in their learning journey."""
    journey_steps = [
        ('search', '🔍 Discover', st.session_state.get('has_searched', False)),
        ('recommendations', '🎯 Get Recommendations', st.session_state.get('has_recommendations', False)),
        ('learning_path', '🛤️ Build Learning Path', st.session_state.get('has_learning_path', False)),
        ('enroll', '🎓 Start Learning', st.session_state.get('has_enrolled', False))
    ]
    
    st.markdown("<div class='journey-indicator'>", unsafe_allow_html=True)
    cols = st.columns(len(journey_steps))
    
    for i, (step_id, step_name, completed) in enumerate(journey_steps):
        with cols[i]:
            status_class = 'completed' if completed else 'pending'
            icon = '✓' if completed else '○'
            st.markdown(f'<div class="journey-step {status_class}">{icon} {step_name}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_user_status_panel():
    """Render user status and quick access panel."""
    # Learning statistics
    favorites_count = len(st.session_state.get('favorite_courses', []))
    learning_plan_count = len(st.session_state.get('learning_plan', []))
    
    st.markdown(f"""
    <div class="user-status-panel">
        <div class="status-item">
            <span class="status-icon">❤️</span>
            <span class="status-text">{favorites_count} Favorites</span>
        </div>
        <div class="status-item">
            <span class="status-icon">📅</span>
            <span class="status-text">{learning_plan_count} Planned</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    if st.button("👤 My Profile", key="profile_btn", help="View and edit your learning profile"):
        st.session_state.current_page = 'profile'
        st.rerun()

def render_sidebar():
    """Render the sidebar with user preferences and controls."""
    with st.sidebar:
        st.header("🎯 Learning Preferences")
        
        # User Profile Section
        with st.expander("👤 User Profile", expanded=True):
            skill_level = st.selectbox(
                "Current Skill Level",
                options=['beginner', 'intermediate', 'advanced', 'expert'],
                index=['beginner', 'intermediate', 'advanced', 'expert'].index(
                    st.session_state.user_profile['skill_level']
                ),
                help="Your current expertise level"
            )
            
            modality = st.selectbox(
                "Preferred Learning Mode",
                options=['online', 'hybrid', 'in-person', 'any'],
                index=['online', 'hybrid', 'in-person', 'any'].index(
                    st.session_state.user_profile['modality']
                ),
                help="How you prefer to learn"
            )
            
            max_duration = st.slider(
                "Maximum Course Duration (hours)",
                min_value=5,
                max_value=200,
                value=st.session_state.user_profile['max_duration_hours'],
                step=5,
                help="Maximum time you can invest"
            )
            
            background = st.text_area(
                "Background & Experience",
                value=st.session_state.user_profile['background'],
                placeholder="Describe your current knowledge, work experience, or relevant skills...",
                help="This helps AI provide better recommendations"
            )
        
        # Advanced Filters
        with st.expander("🔧 Advanced Filters"):
            provider_filter = st.multiselect(
                "Preferred Providers",
                options=['TechAcademy', 'DataCamp', 'Coursera', 'Udemy', 'edX', 'Any'],
                default=['Any'],
                help="Filter by course providers"
            )
            
            price_range = st.slider(
                "Price Range ($)",
                min_value=0,
                max_value=500,
                value=(0, 200),
                help="Filter courses by price"
            )
            
            certification_required = st.checkbox(
                "Certification Required",
                value=False,
                help="Only show courses that offer certificates"
            )
            
            rating_threshold = st.slider(
                "Minimum Rating",
                min_value=3.0,
                max_value=5.0,
                value=4.0,
                step=0.1,
                help="Minimum course rating"
            )
        
        # Update session state
        st.session_state.user_profile.update({
            'skill_level': skill_level,
            'modality': modality,
            'max_duration_hours': max_duration,
            'background': background,
            'preferences': {
                'providers': provider_filter,
                'price_range': price_range,
                'certification_required': certification_required,
                'rating_threshold': rating_threshold
            }
        })
        
        # Database Stats
        if BACKEND_AVAILABLE:
            with st.expander("📊 Database Stats"):
                try:
                    stats = get_database_stats()
                    st.metric("Total Courses", stats['total_courses'])
                    st.metric("With Embeddings", stats['courses_with_embeddings'])
                    
                    if stats['level_distribution']:
                        st.write("**Level Distribution:**")
                        for level, count in stats['level_distribution'].items():
                            st.write(f"• {level.title()}: {count}")
                except Exception as e:
                    st.error(f"Database error: {e}")
        
        # Quick Actions
        st.header("⚡ Quick Actions")
        
        if st.button("🔄 Reset Preferences", use_container_width=True):
            st.session_state.user_profile = {
                'skill_level': 'beginner',
                'modality': 'online',
                'max_duration_hours': 100,
                'background': '',
                'completed_courses': [],
                'preferences': {}
            }
            st.rerun()
        
        if st.button("💾 Save Profile", use_container_width=True):
            profile_json = json.dumps(st.session_state.user_profile, indent=2)
            st.download_button(
                label="Download Profile",
                data=profile_json,
                file_name=f"learning_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # Upload Profile
        uploaded_profile = st.file_uploader(
            "📁 Upload Saved Profile",
            type=['json'],
            help="Upload a previously saved learning profile"
        )
        
        if uploaded_profile:
            try:
                profile_data = json.load(uploaded_profile)
                st.session_state.user_profile.update(profile_data)
                st.success("Profile loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading profile: {e}")

def render_search_interface():
    """Render the main search interface."""
    st.header("🔍 Find Your Perfect Course")
    
    # Simple search interface
    render_quick_search()
    
    # Add chat interface directly without expander to avoid nested expander error
    render_chat_interface()

def render_quick_search():
    """Render simple, clean search interface."""
    
    # Main search interface
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "What would you like to learn?",
            placeholder="e.g., Python for data science, machine learning basics, web development...",
            help="Describe what you want to learn in natural language",
            key="main_search_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Align button with input
        search_button = st.button("🔍 Search", use_container_width=True, type="primary")
    
    # Advanced search filters (collapsed by default)
    with st.expander("⚙️ Search Filters", expanded=False):
        render_simple_search_filters()
    
    # Process search
    if search_button and query:
        st.session_state.has_searched = True
        process_search_query(query)

def render_search_suggestions():
    """Render search suggestions and popular topics."""
    st.markdown("**💡 Popular Topics:**")
    
    popular_topics = [
        ("🐍 Python Programming", "python programming basics"),
        ("🤖 Machine Learning", "machine learning fundamentals"),
        ("🌐 Web Development", "web development with javascript"),
        ("📊 Data Science", "data science and analytics"),
        ("☁️ Cloud Computing", "cloud computing aws azure"),
        ("🎨 UI/UX Design", "ui ux design principles")
    ]
    
    cols = st.columns(3)
    for i, (label, query) in enumerate(popular_topics):
        with cols[i % 3]:
            if st.button(label, key=f"topic_{i}", help=f"Search for: {query}"):
                st.session_state.main_search_input = query
                process_search_query(query)

def render_live_search_suggestions(query: str):
    """Render live search suggestions based on current input."""
    # Generate suggestions based on query
    suggestions = generate_search_suggestions(query)
    
    if suggestions:
        st.markdown("**💡 Suggestions:**")
        suggestion_cols = st.columns(min(len(suggestions), 3))
        
        for i, suggestion in enumerate(suggestions[:3]):
            with suggestion_cols[i]:
                if st.button(f"→ {suggestion}", key=f"search_suggestion_{i}"):
                    st.session_state.main_search_input = suggestion
                    process_search_query(suggestion)

def generate_search_suggestions(query: str) -> List[str]:
    """Generate search suggestions based on the current query."""
    query_lower = query.lower()
    
    suggestion_map = {
        'python': ['python for beginners', 'python data science', 'python web development'],
        'machine': ['machine learning basics', 'machine learning with python', 'deep learning fundamentals'],
        'web': ['web development html css', 'web development javascript', 'full stack web development'],
        'data': ['data science fundamentals', 'data analysis with pandas', 'data visualization'],
        'javascript': ['javascript basics', 'javascript react', 'javascript node.js'],
        'ai': ['artificial intelligence basics', 'ai and machine learning', 'ai for business'],
        'cloud': ['cloud computing aws', 'cloud architecture', 'cloud security'],
        'design': ['ui ux design', 'graphic design', 'web design principles']
    }
    
    suggestions = []
    for keyword, suggestion_list in suggestion_map.items():
        if keyword in query_lower:
            suggestions.extend(suggestion_list)
    
    return suggestions[:3]

def render_simple_search_filters():
    """Render simplified search filters."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        skill_level = st.selectbox(
            "Skill Level",
            options=["Any", "Beginner", "Intermediate", "Advanced"],
            index=0
        )
    
    with col2:
        duration = st.selectbox(
            "Duration",
            options=["Any", "< 10 hours", "10-50 hours", "> 50 hours"],
            index=0
        )
    
    with col3:
        price = st.selectbox(
            "Price",
            options=["Any", "Free", "< $50", "$50-200", "> $200"],
            index=0
        )
    
    # Store filters in session state
    st.session_state.search_filters = {
        'skill_level': skill_level if skill_level != "Any" else None,
        'duration': duration if duration != "Any" else None,
        'price': price if price != "Any" else None
    }

def render_advanced_search_filters():
    """Render advanced search filters."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📚 Content Filters**")
        course_types = st.multiselect(
            "Course Types",
            ["Tutorial", "Certification", "Bootcamp", "University Course", "Workshop"],
            key="search_course_types"
        )
        
        difficulty_levels = st.multiselect(
            "Difficulty Levels",
            ["Beginner", "Intermediate", "Advanced", "Expert"],
            key="search_difficulty"
        )
    
    with col2:
        st.markdown("**⏱️ Time & Format**")
        duration_range = st.slider(
            "Duration (hours)",
            min_value=1,
            max_value=200,
            value=(1, 50),
            key="search_duration"
        )
        
        format_options = st.multiselect(
            "Learning Format",
            ["Online", "Hybrid", "In-Person", "Self-Paced"],
            key="search_format"
        )
    
    with col3:
        st.markdown("**💰 Cost & Quality**")
        price_range = st.slider(
            "Price Range ($)",
            min_value=0,
            max_value=500,
            value=(0, 200),
            key="search_price"
        )
        
        min_rating = st.slider(
            "Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=3.0,
            step=0.5,
            key="search_rating"
        )

def render_search_history():
    """Render search history with quick re-search options."""
    if st.session_state.get('search_history'):
        with st.expander("📝 Recent Searches", expanded=False):
            for i, search in enumerate(st.session_state.search_history[-5:]):  # Show last 5 searches
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"🔍 {search['query']}")
                    st.caption(f"🕒 {search['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    if st.button("🔄 Search Again", key=f"research_{i}"):
                        process_search_query(search['query'])
                
                with col3:
                    if st.button("❌ Remove", key=f"remove_search_{i}"):
                        st.session_state.search_history.pop(-(5-i))
                        st.rerun()

def process_search_query(query: str):
    """Process a search query and display results."""
    if not BACKEND_AVAILABLE:
        st.error("Backend services not available. Please check the system configuration.")
        return
    
    # Validate and sanitize query
    if not validate_user_input(query):
        st.error("Please enter a valid search query.")
        return
    
    clean_query = sanitize_query(query)
    
    # Add to search history
    st.session_state.search_history.append({
        'query': clean_query,
        'timestamp': datetime.now(),
        'user_profile': st.session_state.user_profile.copy()
    })
    
    # Show loading spinner
    with st.spinner("🤖 AI is analyzing your request and finding the best courses..."):
        try:
            # Call the RAG pipeline
            result = course_recommendation_rag(
                query=clean_query,
                user_preferences=st.session_state.user_profile
            )
            
            # Store results in session state
            st.session_state.current_recommendations = result
            
            # Display results
            render_search_results(result)
            
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            st.info("Please try a different query or check if the database is properly initialized.")

def render_search_results(result: Dict[str, Any]):
    """Render comprehensive search results."""
    if not result or not result.get('recommendations'):
        st.warning("No courses found for your query. Try adjusting your search terms or preferences.")
        return
    
    # AI Response
    st.subheader("🤖 AI Learning Advisor")
    ai_response = result.get('response', 'No detailed response available.')
    st.markdown(f"""
    <div class="ai-message">
        {ai_response}
    </div>
    """, unsafe_allow_html=True)
    
    # Course Recommendations
    st.subheader(f"📚 Recommended Courses ({len(result['recommendations'])})")
    
    # Simply display all recommendations as cards without options
    recommendations = result['recommendations']
    render_course_grid(recommendations)

def render_course_table(recommendations: List[Dict]):
    """Render courses in table format."""
    df_data = []
    for rec in recommendations:
        df_data.append({
            'Course': rec['title'],
            'Provider': rec['provider'],
            'Level': rec['level'].title(),
            'Duration (h)': rec['duration_hours'],
            'Score': f"{rec['recommendation_score']:.3f}",
            'Reason': rec['recommendation_reason'][:50] + '...' if len(rec['recommendation_reason']) > 50 else rec['recommendation_reason']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_compact_course_list(recommendations: List[Dict]):
    """Render courses in compact list format."""
    for i, rec in enumerate(recommendations, 1):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{i}. {rec['title']}**")
                st.caption(f"{rec['provider']} • {rec['recommendation_reason']}")
            
            with col2:
                st.metric("Score", f"{rec['recommendation_score']:.3f}")
            
            with col3:
                st.write(f"**{rec['level'].title()}**")
                st.caption(f"{rec['duration_hours']}h")
            
            with col4:
                if st.button("❤️", key=f"fav_{i}", help="Add to favorites"):
                    add_to_favorites(rec)

def add_to_favorites(course: Dict):
    """Add a course to user's favorites."""
    if course not in st.session_state.favorite_courses:
        st.session_state.favorite_courses.append(course)
        st.success(f"Added '{course['title']}' to favorites!")

def render_skill_gap_analysis(skill_gaps: Dict):
    """Render skill gap analysis with visualizations."""
    st.subheader("⚠️ Skill Gap Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_color = {
            'Low': 'green',
            'Medium': 'orange', 
            'High': 'red'
        }
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {severity_color.get(skill_gaps['gap_severity'], 'gray')}">
                {skill_gaps['gap_severity']} Severity
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Gaps Identified", len(skill_gaps.get('identified_gaps', [])))
    
    with col3:
        st.metric("Prerequisites Missing", len(skill_gaps.get('prerequisite_issues', [])))
    
    # Detailed breakdown
    if skill_gaps.get('identified_gaps'):
        st.write("**Skills to Acquire:**")
        for gap in skill_gaps['identified_gaps'][:5]:
            st.write(f"• {gap}")
    
    if skill_gaps.get('recommended_additional_courses'):
        st.write("**Recommended Bridge Courses:**")
        for course in skill_gaps['recommended_additional_courses'][:3]:
            st.write(f"• {course}")

def render_analytics_summary(analytics: Dict):
    """Render analytics summary with charts."""
    st.subheader("📊 Search Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Courses Analyzed", analytics['total_courses_analyzed'])
    
    with col2:
        st.metric("Avg Similarity", f"{analytics['average_similarity_score']:.3f}")
    
    with col3:
        if analytics.get('skill_level_distribution'):
            most_common_level = max(analytics['skill_level_distribution'], 
                                  key=analytics['skill_level_distribution'].get)
            st.metric("Most Common Level", most_common_level.title())
    
    with col4:
        if analytics.get('duration_statistics'):
            avg_duration = analytics['duration_statistics'].get('mean', 0)
            st.metric("Avg Duration", f"{avg_duration:.0f}h")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if analytics.get('skill_level_distribution'):
            fig = px.pie(
                values=list(analytics['skill_level_distribution'].values()),
                names=[name.title() for name in analytics['skill_level_distribution'].keys()],
                title="Skill Level Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if analytics.get('top_tags'):
            tags_data = analytics['top_tags'][:8]
            if tags_data:
                fig = px.bar(
                    x=[tag[1] for tag in tags_data],
                    y=[tag[0] for tag in tags_data],
                    orientation='h',
                    title="Popular Topics"
                )
                fig.update_layout(xaxis_title="Count", yaxis_title="Topics")
                st.plotly_chart(fig, use_container_width=True)

def render_analytics_dashboard():
    """Render comprehensive analytics dashboard."""
    st.subheader("📈 Course Discovery Analytics")
    
    if not st.session_state.search_history:
        st.info("No search history available. Start by making some course searches!")
        return
    
    # Search history chart
    search_dates = [search['timestamp'].date() for search in st.session_state.search_history]
    search_df = pd.DataFrame({'Date': search_dates})
    daily_searches = search_df.groupby('Date').size().reset_index(name='Searches')
    
    fig = px.line(daily_searches, x='Date', y='Searches', title="Daily Search Activity")
    st.plotly_chart(fig, use_container_width=True)
    
    # Popular search terms
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recent Searches:**")
        for search in st.session_state.search_history[-5:]:
            st.write(f"• {search['query'][:50]}...")
    
    with col2:
        if st.session_state.favorite_courses:
            st.write("**Favorite Courses:**")
            for fav in st.session_state.favorite_courses[:5]:
                st.write(f"❤️ {fav['title']}")

def main():
    """Main application entry point."""
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Check backend availability
    if not BACKEND_AVAILABLE:
        st.error("⚠️ Backend services are not available. Please ensure the course recommendation system is properly set up.")
        st.info("To set up the backend:")
        st.code("""
        # Navigate to project directory
        cd course_recom
        
        # Initialize database
        python -c "from src.database_utils import initialize_database; initialize_database()"
        
        # Populate with sample data
        python populate_database.py
        """)
        return
    
    # Render main interface
    render_main_header()
    
    # Main content area - single column for cleaner layout
    render_search_interface()
    
    # Show current recommendations if available
    if st.session_state.current_recommendations:
        st.divider()
        st.markdown("### 🎯 Recommended Courses")
        result = st.session_state.current_recommendations
        
        # Show recommendations
        if result.get('recommendations'):
            for i, course in enumerate(result['recommendations'][:5]):  # Limit to top 5
                render_course_card(course, i, variant="compact")
        
        # Show learning path if available
        if result.get('learning_path'):
            with st.expander("🛤️ Suggested Learning Path", expanded=False):
                render_learning_path_visualization(result['learning_path'])
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎓 AI-Powered Course Recommendation System</p>
        <p>Built with ❤️ using IBM Watsonx, LangChain, and Streamlit</p>
        <p><small>v1.0.0 • Ultra-Sophisticated Edition</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
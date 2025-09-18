"""
Course Card Components for Streamlit UI
Renders individual course cards and course grids with advanced styling and interactivity.
"""

import streamlit as st
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

def render_course_card(course: Dict[str, Any], index: int = 0, variant: str = "default") -> None:
    """
    Render a single course card with progressive disclosure and improved cognitive load.
    
    Args:
        course: Dictionary containing course information
        index: Index for unique widget keys
        variant: Card variant - "compact", "default", or "detailed"
    """
    if variant == "compact":
        render_compact_course_card(course, index)
    elif variant == "detailed":
        render_detailed_course_card(course, index)
    else:
        render_default_course_card(course, index)

def render_compact_course_card(course: Dict[str, Any], index: int = 0) -> None:
    """
    Render a compact course card for mobile and list views.
    """
    # Extract and format data first
    title = truncate_text(course.get('title', 'Unknown Course'), 50)
    provider = course.get('provider', 'Unknown Provider')
    score = course.get('recommendation_score', 0)
    level = course.get('level', 'intermediate')
    duration = course.get('duration_hours', 0)
    modality = course.get('modality', 'online')
    
    # Format values
    score_indicator = render_score_indicator(score)
    level_emoji = get_level_emoji(level)
    modality_emoji = get_modality_emoji(modality)
    duration_text = format_duration_compact(duration)
    
    with st.container():
        st.markdown(f"""
        <div style="
            background: rgba(30, 32, 36, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border-left: 3px solid #667eea;
            border: 1px solid rgba(255, 255, 255, 0.1);
        " data-testid="course-card-{index}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <h4 style="color: #ffffff; margin: 0 0 0.25rem 0; font-weight: 600; font-size: 1.1rem; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);">{title}</h4>
                    <span style="color: #94a3b8; font-size: 0.9rem; font-weight: 500; letter-spacing: 0.5px;">{provider}</span>
                </div>
                <div style="margin-left: 1rem;">
                    {score_indicator}
                </div>
            </div>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.875rem;">
                <span style="color: #cbd5e1; font-weight: 500;">{level_emoji} {level.title()}</span>
                <span style="color: #cbd5e1; font-weight: 500;">⏰ {duration_text}</span>
                <span style="color: #cbd5e1; font-weight: 500;">{modality_emoji} {modality.title()}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick actions
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("View Details", key=f"compact_details_{index}", help="View full course information"):
                st.session_state[f"show_details_{index}"] = True
        with col2:
            if st.button("❤️", key=f"compact_fav_{index}", help="Add to favorites"):
                add_to_favorites(course)
        with col3:
            if st.button("📅", key=f"compact_plan_{index}", help="Add to learning plan"):
                add_to_learning_plan(course)

def render_default_course_card(course: Dict[str, Any], index: int = 0) -> None:
    """
    Render the default course card with progressive disclosure.
    """
    with st.container():
        # Enhanced card header with better visual hierarchy
        st.markdown(f"""
        <div class="course-card course-card-default" data-testid="course-card-{index}">
            <div class="course-card-header-enhanced">
                <div class="course-primary-info">
                    <h3 class="course-title-main">{course.get('title', 'Unknown Course')}</h3>
                    <div class="course-provider-badge">{course.get('provider', 'Unknown Provider')}</div>
                </div>
                <div class="course-score-visual">
                    {render_visual_score(course.get('recommendation_score', 0))}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Essential info only (Progressive Disclosure Level 1)
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Primary metrics
            level = course.get('level', 'intermediate').title()
            duration = course.get('duration_hours', 0)
            st.markdown(f"""
            <div class="course-essential-info">
                <span class="info-pill level-pill">{get_level_emoji(level.lower())} {level}</span>
                <span class="info-pill duration-pill">⏰ {format_duration_smart(duration)}</span>
                <span class="info-pill format-pill">{get_modality_emoji(course.get('modality', 'online'))} {course.get('modality', 'Online').title()}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Quick action - most important
            if st.button("🔍 Learn More", key=f"learn_more_{index}", help="View detailed course information", type="primary"):
                st.session_state[f"expanded_card_{index}"] = not st.session_state.get(f"expanded_card_{index}", False)
        
        with col3:
            # Quick favorite action
            fav_icon = "💚" if is_course_favorited(course) else "🤍"
            if st.button(f"{fav_icon}", key=f"fav_toggle_{index}", help="Toggle favorite"):
                toggle_favorite(course)
        
        # Progressive Disclosure - Show reason briefly
        reason = course.get('recommendation_reason', 'Good match for your learning goals')
        if len(reason) > 100:
            reason = reason[:100] + "..."
        st.markdown(f"<div class='course-reason-brief'>💡 {reason}</div>", unsafe_allow_html=True)
        
        # Progressive Disclosure Level 2 - Expandable detailed info
        if st.session_state.get(f"expanded_card_{index}", False):
            render_expanded_card_content(course, index)
        
        st.divider()

def render_expanded_card_content(course: Dict[str, Any], index: int) -> None:
    """
    Render expanded content for the course card.
    """
    with st.container():
        # Detailed metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Course Metrics**")
            if course.get('course_rating'):
                rating = course['course_rating']
                st.markdown(f"Rating: {render_star_rating(rating)} ({rating}/5.0)")
            
            if course.get('enrollment_count'):
                enrollment = course['enrollment_count']
                st.markdown(f"Students: 👥 {format_number_compact(enrollment)}")
            
            similarity = course.get('similarity_score', 0)
            st.markdown(f"Relevance: {render_relevance_bar(similarity)}")
        
        with col2:
            st.markdown("**🎯 Learning Outcomes**")
            
            # Tags - limited to most relevant
            tags = course.get('tags', [])
            if tags:
                top_tags = tags[:4]  # Show only top 4 tags
                tag_html = " ".join([f'<span class="skill-badge-small">{tag}</span>' for tag in top_tags])
                st.markdown(tag_html, unsafe_allow_html=True)
                if len(tags) > 4:
                    st.caption(f"+ {len(tags) - 4} more topics")
            
            # Certification indicator
            if course.get('certification_offered'):
                st.markdown("🏆 **Professional Certificate Available**")
        
        # Full reason
        full_reason = course.get('recommendation_reason', '')
        if full_reason:
            with st.expander("💡 Why this course matches your needs", expanded=False):
                st.write(full_reason)
        
        # Prerequisites - only if they exist
        prerequisites = course.get('prerequisites', [])
        if prerequisites:
            with st.expander("📋 Prerequisites", expanded=False):
                for prereq in prerequisites[:3]:  # Show max 3 prerequisites
                    st.write(f"• {prereq}")
                if len(prerequisites) > 3:
                    st.caption(f"+ {len(prerequisites) - 3} more prerequisites")
        
        # Action buttons - organized by importance
        st.markdown("**Quick Actions:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📅 Add to Learning Plan", key=f"plan_exp_{index}", use_container_width=True):
                add_to_learning_plan(course)
        
        with col2:
            if st.button("📊 Compare Courses", key=f"compare_exp_{index}", use_container_width=True):
                add_to_comparison(course)
        
        with col3:
            if st.button("🔗 Find Similar", key=f"similar_exp_{index}", use_container_width=True):
                find_similar_courses(course)

def render_detailed_course_card(course: Dict[str, Any], index: int = 0) -> None:
    """
    Render a detailed course card for comparison and detailed views.
    """
    with st.expander(f"📖 {course.get('title', 'Course Details')}", expanded=True):
        show_course_details(course, index)

def render_course_grid(courses: List[Dict[str, Any]]) -> None:
    """
    Render courses in a responsive grid layout.
    
    Args:
        courses: List of course dictionaries
    """
    if not courses:
        st.warning("No courses to display.")
        return
    
    # Grid layout - 2 columns for better readability
    cols = st.columns(2)
    
    for i, course in enumerate(courses):
        with cols[i % 2]:
            render_course_card(course, i)

def render_course_comparison(courses: List[Dict[str, Any]]) -> None:
    """
    Render a detailed comparison view of multiple courses.
    
    Args:
        courses: List of courses to compare
    """
    if not courses:
        st.info("No courses selected for comparison.")
        return
    
    st.subheader(f"📊 Course Comparison ({len(courses)} courses)")
    
    # Comparison metrics
    metrics = ['recommendation_score', 'similarity_score', 'duration_hours']
    
    for metric in metrics:
        st.write(f"**{metric.replace('_', ' ').title()}:**")
        
        values = [course.get(metric, 0) for course in courses]
        course_names = [course.get('title', f'Course {i+1}')[:30] for i, course in enumerate(courses)]
        
        fig = px.bar(
            x=course_names,
            y=values,
            title=f"{metric.replace('_', ' ').title()} Comparison"
        )
        fig.update_layout(xaxis_title="Courses", yaxis_title=metric.replace('_', ' ').title())
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed comparison table
    comparison_data = []
    for course in courses:
        comparison_data.append({
            'Course': course.get('title', 'Unknown')[:40],
            'Provider': course.get('provider', 'Unknown'),
            'Level': course.get('level', 'Unknown').title(),
            'Duration (h)': course.get('duration_hours', 0),
            'Score': f"{course.get('recommendation_score', 0):.3f}",
            'Relevance': f"{course.get('similarity_score', 0):.3f}",
            'Certification': "✅" if course.get('certification_offered') else "❌",
            'Rating': course.get('course_rating', 'N/A')
        })
    
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_course_details(course: Dict[str, Any], index: int) -> None:
    """
    Show detailed course information in a modal-like expander.
    
    Args:
        course: Course dictionary
        index: Index for unique keys
    """
    with st.expander(f"📖 Detailed Information: {course.get('title', 'Course')}", expanded=True):
        
        # Course overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📚 Course Overview")
            st.write(f"**Title:** {course.get('title', 'N/A')}")
            st.write(f"**Provider:** {course.get('provider', 'N/A')}")
            st.write(f"**Level:** {course.get('level', 'N/A').title()}")
            st.write(f"**Duration:** {course.get('duration_hours', 0)} hours")
            st.write(f"**Format:** {course.get('modality', 'N/A').title()}")
        
        with col2:
            st.markdown("### 📊 Recommendations")
            st.write(f"**Recommendation Score:** {course.get('recommendation_score', 0):.3f}")
            st.write(f"**Similarity Score:** {course.get('similarity_score', 0):.3f}")
            st.write(f"**Why Recommended:** {course.get('recommendation_reason', 'N/A')}")
            
            if course.get('course_rating'):
                st.write(f"**Rating:** {course['course_rating']}/5.0 ⭐")
            
            if course.get('enrollment_count'):
                st.write(f"**Students Enrolled:** {course['enrollment_count']:,}")
        
        # Content preview
        content_preview = course.get('content_preview', '')
        if content_preview:
            st.markdown("### 📝 Course Content Preview")
            st.write(content_preview)
        
        # Tags and topics
        tags = course.get('tags', [])
        if tags:
            st.markdown("### 🏷️ Topics Covered")
            tag_html = " ".join([f'<span class="skill-badge">{tag}</span>' for tag in tags])
            st.markdown(tag_html, unsafe_allow_html=True)
        
        # Prerequisites
        prerequisites = course.get('prerequisites', [])
        if prerequisites:
            st.markdown("### 📋 Prerequisites")
            for prereq in prerequisites:
                st.write(f"• {prereq}")
        
        # Regional availability
        regions = course.get('valid_regions', [])
        if regions:
            st.markdown("### 🌍 Available Regions")
            st.write(", ".join(regions))
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("❤️ Add to Favorites", key=f"detail_fav_{index}"):
                add_to_favorites(course)
        
        with col2:
            if st.button("📅 Add to Learning Plan", key=f"detail_plan_{index}"):
                add_to_learning_plan(course)
        
        with col3:
            if st.button("📊 Add to Comparison", key=f"detail_compare_{index}"):
                add_to_comparison(course)

def get_score_color(score: float) -> str:
    """Get color based on recommendation score."""
    if score >= 0.8:
        return "linear-gradient(45deg, #4CAF50, #8BC34A)"
    elif score >= 0.6:
        return "linear-gradient(45deg, #FF9800, #FFC107)"
    else:
        return "linear-gradient(45deg, #757575, #9E9E9E)"

def get_level_emoji(level: str) -> str:
    """Get emoji for skill level."""
    emoji_map = {
        'beginner': '🌱',
        'intermediate': '🌿',
        'advanced': '🌳',
        'expert': '🏆'
    }
    return emoji_map.get(level, '📚')

def get_modality_emoji(modality: str) -> str:
    """Get emoji for learning modality."""
    emoji_map = {
        'online': '💻',
        'hybrid': '🔄',
        'in-person': '🏢',
        'self-paced': '⏰'
    }
    return emoji_map.get(modality, '📖')

def add_to_favorites(course: Dict[str, Any]) -> None:
    """Add course to user's favorites."""
    if 'favorite_courses' not in st.session_state:
        st.session_state.favorite_courses = []
    
    # Check if already in favorites
    course_ids = [fav.get('course_id') for fav in st.session_state.favorite_courses]
    if course.get('course_id') not in course_ids:
        st.session_state.favorite_courses.append(course)
        st.success(f"✅ Added '{course.get('title', 'Course')}' to favorites!")
    else:
        st.warning(f"'{course.get('title', 'Course')}' is already in your favorites.")

def add_to_comparison(course: Dict[str, Any]) -> None:
    """Add course to comparison list."""
    if 'comparison_courses' not in st.session_state:
        st.session_state.comparison_courses = []
    
    # Limit comparison to 4 courses
    if len(st.session_state.comparison_courses) >= 4:
        st.warning("Comparison limit reached (4 courses max). Remove a course to add another.")
        return
    
    # Check if already in comparison
    course_ids = [comp.get('course_id') for comp in st.session_state.comparison_courses]
    if course.get('course_id') not in course_ids:
        st.session_state.comparison_courses.append(course)
        st.success(f"✅ Added '{course.get('title', 'Course')}' to comparison!")
    else:
        st.warning(f"'{course.get('title', 'Course')}' is already in comparison.")

def add_to_learning_plan(course: Dict[str, Any]) -> None:
    """Add course to user's learning plan."""
    if 'learning_plan' not in st.session_state:
        st.session_state.learning_plan = []
    
    # Check if already in plan
    course_ids = [plan.get('course_id') for plan in st.session_state.learning_plan]
    if course.get('course_id') not in course_ids:
        st.session_state.learning_plan.append(course)
        st.success(f"✅ Added '{course.get('title', 'Course')}' to learning plan!")
    else:
        st.warning(f"'{course.get('title', 'Course')}' is already in your learning plan.")

def find_similar_courses(course: Dict[str, Any]) -> None:
    """Find and display similar courses."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        from vector_search import get_similar_courses
        
        course_id = course.get('course_id')
        if not course_id:
            st.error("Course ID not available for similarity search.")
            return
        
        with st.spinner("Finding similar courses..."):
            similar_courses = get_similar_courses(course_id, limit=3)
            
            if similar_courses:
                st.success(f"Found {len(similar_courses)} similar courses:")
                for i, sim_course in enumerate(similar_courses):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{sim_course.title}** ({sim_course.provider})")
                            st.caption(f"Similarity: {sim_course.similarity_score:.3f}")
                        with col2:
                            if st.button("View", key=f"sim_view_{i}"):
                                course_dict = {
                                    'course_id': sim_course.course_id,
                                    'title': sim_course.title,
                                    'provider': sim_course.provider,
                                    'level': sim_course.level,
                                    'duration_hours': sim_course.duration_hours,
                                    'modality': sim_course.modality,
                                    'tags': sim_course.tags,
                                    'similarity_score': sim_course.similarity_score,
                                    'content_preview': sim_course.content_preview
                                }
                                show_course_details(course_dict, f"sim_{i}")
            else:
                st.info("No similar courses found.")
                
    except Exception as e:
        st.error(f"Error finding similar courses: {e}")

# New utility functions for progressive disclosure design

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis if it exceeds max_length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_duration_compact(hours: float) -> str:
    """Format duration in a compact way."""
    if hours < 1:
        return f"{int(hours * 60)}min"
    elif hours < 24:
        return f"{hours:.0f}h"
    else:
        days = hours / 8
        return f"{days:.0f}d"

def format_duration_smart(hours: float) -> str:
    """Smart duration formatting based on length."""
    if hours < 1:
        return f"{int(hours * 60)} minutes"
    elif hours <= 8:
        return f"{hours:.1f} hours"
    elif hours <= 40:
        return f"{hours/8:.0f} days"
    else:
        weeks = hours / 40
        return f"{weeks:.1f} weeks"

def format_number_compact(num: int) -> str:
    """Format large numbers in compact form."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    else:
        return f"{num:,}"

def render_score_indicator(score: float) -> str:
    """Render score as a visual indicator."""
    if score >= 0.9:
        return '<div class="score-indicator excellent">🎆 Excellent</div>'
    elif score >= 0.8:
        return '<div class="score-indicator very-good">🔵 Very Good</div>'
    elif score >= 0.7:
        return '<div class="score-indicator good">🟡 Good</div>'
    elif score >= 0.6:
        return '<div class="score-indicator fair">🟠 Fair</div>'
    else:
        return '<div class="score-indicator poor">🔴 Poor</div>'

def render_visual_score(score: float) -> str:
    """Render score as a visual progress indicator."""
    percentage = int(score * 100)
    color = get_score_color_class(score)
    return f'<div class="score-visual"><div class="score-circle {color}"><span class="score-text">{percentage}</span></div><div class="score-label">Match</div></div>'

def render_star_rating(rating: float) -> str:
    """Render star rating with half-stars."""
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars = "⭐" * full_stars + "✨" * half_star + "☆" * empty_stars
    return stars

def render_relevance_bar(similarity: float) -> str:
    """Render relevance as a progress bar."""
    percentage = int(similarity * 100)
    color = "success" if similarity >= 0.8 else "warning" if similarity >= 0.6 else "danger"
    return f'''
    <div class="relevance-bar">
        <div class="relevance-fill {color}" style="width: {percentage}%"></div>
        <span class="relevance-text">{percentage}%</span>
    </div>
    '''

def get_score_color_class(score: float) -> str:
    """Get CSS class for score color."""
    if score >= 0.8:
        return "score-excellent"
    elif score >= 0.6:
        return "score-good"
    else:
        return "score-fair"

def is_course_favorited(course: Dict[str, Any]) -> bool:
    """Check if course is in favorites."""
    if 'favorite_courses' not in st.session_state:
        return False
    
    course_ids = [fav.get('course_id') for fav in st.session_state.favorite_courses]
    return course.get('course_id') in course_ids

def toggle_favorite(course: Dict[str, Any]) -> None:
    """Toggle course favorite status."""
    if 'favorite_courses' not in st.session_state:
        st.session_state.favorite_courses = []
    
    course_ids = [fav.get('course_id') for fav in st.session_state.favorite_courses]
    course_id = course.get('course_id')
    
    if course_id in course_ids:
        # Remove from favorites
        st.session_state.favorite_courses = [
            fav for fav in st.session_state.favorite_courses 
            if fav.get('course_id') != course_id
        ]
        st.toast(f"Removed from favorites: {course.get('title', 'Course')}", icon="💔")
    else:
        # Add to favorites
        st.session_state.favorite_courses.append(course)
        st.toast(f"Added to favorites: {course.get('title', 'Course')}", icon="❤️")

def render_course_preview(course: Dict[str, Any], index: int) -> None:
    """Render a quick preview of the course."""
    with st.container():
        st.markdown(f"""
        <div class="course-preview">
            <h4>Quick Preview</h4>
            <p><strong>Duration:</strong> {format_duration_smart(course.get('duration_hours', 0))}</p>
            <p><strong>Level:</strong> {course.get('level', 'Intermediate').title()}</p>
            <p><strong>Format:</strong> {course.get('modality', 'Online').title()}</p>
        </div>
        """, unsafe_allow_html=True)

# Enhanced grid rendering functions

def render_course_grid(courses: List[Dict[str, Any]], variant: str = "default") -> None:
    """Render courses in a responsive grid layout with improved UX."""
    if not courses:
        render_empty_state()
        return
    
    # Add view options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**{len(courses)} courses found**")
    
    with col2:
        view_mode = st.selectbox(
            "View:",
            ["Grid", "List", "Compact"],
            index=0,
            key="course_view_mode"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Relevance", "Rating", "Duration", "Title"],
            index=0,
            key="course_sort"
        )
    
    # Sort courses
    sorted_courses = sort_courses(courses, sort_by)
    
    # Render based on view mode
    if view_mode == "List":
        render_course_list(sorted_courses)
    elif view_mode == "Compact":
        render_course_compact_grid(sorted_courses)
    else:
        render_course_default_grid(sorted_courses, variant)

def render_course_list(courses: List[Dict[str, Any]]) -> None:
    """Render courses in a single-column list view."""
    for i, course in enumerate(courses):
        render_course_card(course, i, variant="compact")

def render_course_compact_grid(courses: List[Dict[str, Any]]) -> None:
    """Render courses in a compact grid for mobile."""
    cols = st.columns(1)  # Single column for mobile-friendly compact view
    
    for i, course in enumerate(courses):
        with cols[0]:
            render_course_card(course, i, variant="compact")

def render_course_default_grid(courses: List[Dict[str, Any]], variant: str = "default") -> None:
    """Render courses in the default 2-column grid."""
    cols = st.columns(2)
    
    for i, course in enumerate(courses):
        with cols[i % 2]:
            render_course_card(course, i, variant=variant)

def render_empty_state() -> None:
    """Render empty state when no courses are found."""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h3>No courses found</h3>
        <p>Try adjusting your search criteria or browse our course catalog.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📚 Browse All Courses", key="browse_all", use_container_width=True):
            st.session_state.show_all_courses = True

def sort_courses(courses: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort courses by the specified criteria."""
    if sort_by == "Relevance":
        return sorted(courses, key=lambda x: x.get('recommendation_score', 0), reverse=True)
    elif sort_by == "Rating":
        return sorted(courses, key=lambda x: x.get('course_rating', 0), reverse=True)
    elif sort_by == "Duration":
        return sorted(courses, key=lambda x: x.get('duration_hours', 0))
    elif sort_by == "Title":
        return sorted(courses, key=lambda x: x.get('title', '').lower())
    else:
        return courses
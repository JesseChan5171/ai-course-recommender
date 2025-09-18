"""
Learning Path Visualization Components for Streamlit UI
Renders interactive learning paths, progress tracking, and skill progression visualizations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

def render_learning_path_visualization(learning_path: Dict[str, Any]) -> None:
    """
    Render a comprehensive learning path visualization.
    
    Args:
        learning_path: Dictionary containing learning path information
    """
    if not learning_path:
        st.warning("No learning path data available.")
        return
    
    st.subheader(f"🎯 {learning_path.get('path_name', 'Learning Path')}")
    
    # Path overview metrics
    render_path_overview(learning_path)
    
    # Interactive timeline
    render_path_timeline(learning_path)
    
    # Skill progression chart
    render_skill_progression(learning_path)
    
    # Course sequence with dependencies
    render_course_sequence(learning_path)
    
    # Progress tracking
    render_progress_tracker(learning_path)
    
    # Path customization options
    render_path_customization(learning_path)

def render_path_overview(learning_path: Dict[str, Any]) -> None:
    """Render learning path overview metrics."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_hours = learning_path.get('total_duration_hours', 0)
        st.metric(
            "📚 Total Duration",
            f"{total_hours}h",
            help="Total time investment required"
        )
    
    with col2:
        months = learning_path.get('estimated_completion_months', 0)
        st.metric(
            "⏰ Timeline",
            f"{months} months",
            help="Estimated completion time"
        )
    
    with col3:
        courses = learning_path.get('courses', [])
        st.metric(
            "🎓 Courses",
            len(courses),
            help="Number of courses in path"
        )
    
    with col4:
        skill_progression = learning_path.get('skill_progression', [])
        if skill_progression:
            start_level = skill_progression[0] if skill_progression else 'Unknown'
            end_level = skill_progression[-1] if len(skill_progression) > 1 else start_level
            st.metric(
                "📈 Skill Growth",
                f"{start_level.title()} → {end_level.title()}",
                help="Skill level progression"
            )
    
    # Path description
    description = learning_path.get('path_description', '')
    if description:
        st.info(f"📝 **Path Description:** {description}")

def render_path_timeline(learning_path: Dict[str, Any]) -> None:
    """Render interactive timeline visualization."""
    
    st.markdown("### 📅 Learning Timeline")
    
    courses = learning_path.get('courses', [])
    if not courses:
        st.warning("No courses in learning path.")
        return
    
    # Create timeline data
    timeline_data = create_timeline_data(courses)
    
    # Timeline visualization options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        view_mode = st.radio(
            "Timeline View",
            ["Gantt Chart", "Progress Flow", "Calendar View"],
            help="Choose how to visualize the timeline"
        )
        
        hours_per_week = st.slider(
            "Study Hours/Week",
            min_value=5,
            max_value=40,
            value=10,
            help="Adjust based on your availability"
        )
    
    with col1:
        if view_mode == "Gantt Chart":
            render_gantt_chart(timeline_data, hours_per_week)
        elif view_mode == "Progress Flow":
            render_progress_flow(timeline_data)
        else:
            render_calendar_view(timeline_data, hours_per_week)

def create_timeline_data(courses: List[Dict]) -> List[Dict]:
    """Create timeline data from courses."""
    timeline_data = []
    cumulative_hours = 0
    
    for i, course in enumerate(courses):
        duration = course.get('duration_hours', 20)
        
        timeline_data.append({
            'course_id': course.get('course_id', f'course_{i}'),
            'title': course.get('title', f'Course {i+1}'),
            'duration_hours': duration,
            'start_hour': cumulative_hours,
            'end_hour': cumulative_hours + duration,
            'level': course.get('level', 'intermediate'),
            'provider': course.get('provider', 'Unknown'),
            'sequence': i + 1
        })
        
        cumulative_hours += duration
    
    return timeline_data

def render_gantt_chart(timeline_data: List[Dict], hours_per_week: int) -> None:
    """Render Gantt chart for learning timeline."""
    
    if not timeline_data:
        return
    
    # Convert hours to weeks
    df_gantt = []
    for course in timeline_data:
        start_week = course['start_hour'] / hours_per_week
        duration_weeks = course['duration_hours'] / hours_per_week
        
        df_gantt.append({
            'Task': course['title'][:30] + '...' if len(course['title']) > 30 else course['title'],
            'Start': start_week,
            'Finish': start_week + duration_weeks,
            'Duration': duration_weeks,
            'Level': course['level'].title(),
            'Provider': course['provider']
        })
    
    # Create Gantt chart
    fig = px.timeline(
        df_gantt,
        x_start='Start',
        x_end='Finish',
        y='Task',
        color='Level',
        title=f"Learning Timeline ({hours_per_week}h/week)",
        labels={'Start': 'Week', 'Finish': 'Week'}
    )
    
    fig.update_layout(
        height=max(400, len(timeline_data) * 40),
        showlegend=True,
        xaxis_title="Weeks from Start"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_progress_flow(timeline_data: List[Dict]) -> None:
    """Render flow diagram showing course progression."""
    
    if not timeline_data:
        return
    
    # Create flow diagram data
    fig = go.Figure()
    
    # Add nodes for each course
    x_positions = list(range(len(timeline_data)))
    y_positions = [0] * len(timeline_data)
    
    # Add course nodes
    for i, course in enumerate(timeline_data):
        # Determine color based on level
        color_map = {
            'beginner': '#4CAF50',
            'intermediate': '#FF9800', 
            'advanced': '#F44336',
            'expert': '#9C27B0'
        }
        color = color_map.get(course['level'], '#757575')
        
        fig.add_trace(go.Scatter(
            x=[i],
            y=[0],
            mode='markers+text',
            marker=dict(
                size=course['duration_hours'] * 2,  # Size based on duration
                color=color,
                line=dict(width=2, color='white')
            ),
            text=f"{course['sequence']}",
            textposition="middle center",
            textfont=dict(color='white', size=12, family='Arial Black'),
            name=course['level'].title(),
            hovertemplate=f"<b>{course['title']}</b><br>" +
                         f"Level: {course['level'].title()}<br>" +
                         f"Duration: {course['duration_hours']}h<br>" +
                         f"Provider: {course['provider']}<extra></extra>",
            showlegend=i == 0 or course['level'] != timeline_data[i-1]['level']
        ))
    
    # Add connecting arrows
    for i in range(len(timeline_data) - 1):
        fig.add_annotation(
            x=i + 0.5,
            y=0,
            ax=i,
            ay=0,
            xref='x',
            yref='y',
            axref='x',
            ayref='y',
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor='#666'
        )
    
    fig.update_layout(
        title="Course Progression Flow",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title="Learning Sequence"
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, 1]
        ),
        height=300,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Course details below the flow
    st.markdown("**📚 Course Sequence:**")
    for course in timeline_data:
        col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
        
        with col1:
            st.write(f"**{course['sequence']}**")
        with col2:
            st.write(course['title'])
        with col3:
            st.write(f"{course['level'].title()}")
        with col4:
            st.write(f"{course['duration_hours']}h")

def render_calendar_view(timeline_data: List[Dict], hours_per_week: int) -> None:
    """Render calendar view of learning schedule."""
    
    if not timeline_data:
        return
    
    # Calculate weekly schedule
    total_weeks = sum(course['duration_hours'] for course in timeline_data) / hours_per_week
    
    # Create calendar data
    calendar_data = []
    current_date = datetime.now()
    
    for course in timeline_data:
        course_weeks = course['duration_hours'] / hours_per_week
        
        for week in range(int(course_weeks) + 1):
            week_date = current_date + timedelta(weeks=week)
            calendar_data.append({
                'Date': week_date.strftime('%Y-%m-%d'),
                'Week': week + 1,
                'Course': course['title'][:20],
                'Hours': min(hours_per_week, course['duration_hours'] - (week * hours_per_week)),
                'Level': course['level']
            })
        
        current_date += timedelta(weeks=course_weeks)
    
    # Create calendar heatmap
    df_calendar = pd.DataFrame(calendar_data)
    
    if not df_calendar.empty:
        fig = px.density_heatmap(
            df_calendar,
            x='Week',
            y='Course',
            z='Hours',
            title=f"Weekly Learning Schedule ({hours_per_week}h/week)",
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(height=max(300, len(timeline_data) * 50))
        st.plotly_chart(fig, use_container_width=True)

def render_skill_progression(learning_path: Dict[str, Any]) -> None:
    """Render skill progression visualization."""
    
    st.markdown("### 📈 Skill Progression")
    
    skill_progression = learning_path.get('skill_progression', [])
    courses = learning_path.get('courses', [])
    
    if not skill_progression or not courses:
        st.info("Skill progression data not available.")
        return
    
    # Create skill progression data
    skill_levels = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
    skill_values = [1, 2, 3, 4]
    
    # Map current progression
    progression_values = []
    for skill in skill_progression:
        skill_index = next((i for i, level in enumerate(['beginner', 'intermediate', 'advanced', 'expert']) if level == skill.lower()), 1)
        progression_values.append(skill_index + 1)
    
    # Create progression chart
    fig = go.Figure()
    
    # Add progression line
    fig.add_trace(go.Scatter(
        x=list(range(len(skill_progression))),
        y=progression_values,
        mode='lines+markers',
        name='Your Progression',
        line=dict(color='#667eea', width=4),
        marker=dict(size=10, color='#667eea')
    ))
    
    # Add skill level annotations
    for i, (skill, value) in enumerate(zip(skill_progression, progression_values)):
        fig.add_annotation(
            x=i,
            y=value,
            text=skill.title(),
            showarrow=True,
            arrowhead=2,
            arrowcolor='#667eea',
            bgcolor='white',
            bordercolor='#667eea'
        )
    
    fig.update_layout(
        title="Skill Level Progression Through Learning Path",
        xaxis_title="Learning Progress",
        yaxis_title="Skill Level",
        yaxis=dict(
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['Novice', 'Beginner', 'Intermediate', 'Advanced', 'Expert']
        ),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_course_sequence(learning_path: Dict[str, Any]) -> None:
    """Render detailed course sequence with dependencies."""
    
    st.markdown("### 🔗 Course Dependencies & Sequence")
    
    courses = learning_path.get('courses', [])
    if not courses:
        return
    
    # Create dependency visualization
    for i, course in enumerate(courses):
        with st.container():
            # Course step header
            col1, col2, col3 = st.columns([0.5, 3, 1])
            
            with col1:
                # Step number with progress indicator
                if i < len(courses) - 1:
                    step_icon = "🔵"
                else:
                    step_icon = "🏁"
                st.markdown(f"### {step_icon} {i+1}")
            
            with col2:
                st.markdown(f"**{course.get('title', 'Unknown Course')}**")
                st.caption(f"📚 {course.get('provider', 'Unknown')} • {course.get('level', 'intermediate').title()}")
            
            with col3:
                duration = course.get('duration_hours', 0)
                st.metric("Duration", f"{duration}h")
            
            # Course details
            reason = course.get('recommendation_reason', 'Part of learning progression')
            st.write(f"**Why this course:** {reason}")
            
            # Prerequisites (if any)
            prerequisites = course.get('prerequisites', [])
            if prerequisites:
                st.write(f"**Prerequisites:** {', '.join(prerequisites)}")
            
            # Tags
            tags = course.get('tags', [])
            if tags:
                tag_html = " ".join([f'<span class="skill-badge">{tag}</span>' for tag in tags[:4]])
                st.markdown(tag_html, unsafe_allow_html=True)
            
            # Progress connection arrow (except for last course)
            if i < len(courses) - 1:
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <span style="font-size: 2rem; color: #667eea;">⬇️</span>
                </div>
                """, unsafe_allow_html=True)

def render_progress_tracker(learning_path: Dict[str, Any]) -> None:
    """Render interactive progress tracking interface."""
    
    st.markdown("### 📊 Progress Tracker")
    
    courses = learning_path.get('courses', [])
    if not courses:
        return
    
    # Initialize progress state
    if 'course_progress' not in st.session_state:
        st.session_state.course_progress = {course.get('course_id', f'course_{i}'): 0 for i, course in enumerate(courses)}
    
    # Progress overview
    total_courses = len(courses)
    completed_courses = sum(1 for progress in st.session_state.course_progress.values() if progress >= 100)
    overall_progress = sum(st.session_state.course_progress.values()) / len(courses) if courses else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Completed Courses", f"{completed_courses}/{total_courses}")
    
    with col2:
        st.metric("Overall Progress", f"{overall_progress:.1f}%")
    
    with col3:
        total_hours = sum(course.get('duration_hours', 0) for course in courses)
        completed_hours = sum(
            (course.get('duration_hours', 0) * st.session_state.course_progress.get(course.get('course_id', f'course_{i}'), 0) / 100)
            for i, course in enumerate(courses)
        )
        st.metric("Hours Completed", f"{completed_hours:.1f}/{total_hours}")
    
    # Overall progress bar
    st.progress(overall_progress / 100 if overall_progress <= 100 else 1.0)
    
    # Individual course progress
    st.markdown("**📚 Individual Course Progress:**")
    
    for i, course in enumerate(courses):
        course_id = course.get('course_id', f'course_{i}')
        title = course.get('title', 'Unknown Course')
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            progress = st.slider(
                f"{title[:40]}...",
                min_value=0,
                max_value=100,
                value=st.session_state.course_progress[course_id],
                key=f"progress_{course_id}",
                help=f"Track your progress through {title}"
            )
            st.session_state.course_progress[course_id] = progress
        
        with col2:
            if progress >= 100:
                st.success("✅ Complete")
            elif progress >= 50:
                st.warning("🔄 In Progress")
            else:
                st.info("📚 Not Started")
        
        with col3:
            hours_completed = (course.get('duration_hours', 0) * progress / 100)
            st.write(f"{hours_completed:.1f}h")

def render_path_customization(learning_path: Dict[str, Any]) -> None:
    """Render learning path customization options."""
    
    st.markdown("### ⚙️ Customize Your Path")
    
    with st.expander("🔧 Path Customization Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Schedule Preferences")
            
            study_pace = st.selectbox(
                "Study Pace",
                ["Relaxed (5-10h/week)", "Moderate (10-20h/week)", "Intensive (20-30h/week)", "Full-time (30+ h/week)"],
                index=1
            )
            
            preferred_days = st.multiselect(
                "Preferred Study Days",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=["Monday", "Wednesday", "Friday"]
            )
            
            break_weeks = st.number_input(
                "Break Weeks Between Courses",
                min_value=0,
                max_value=4,
                value=1,
                help="Time to review and consolidate knowledge"
            )
        
        with col2:
            st.subheader("🎯 Learning Preferences")
            
            learning_style = st.selectbox(
                "Learning Style",
                ["Visual", "Hands-on", "Theoretical", "Mixed"],
                index=3
            )
            
            difficulty_preference = st.slider(
                "Preferred Challenge Level",
                min_value=1,
                max_value=10,
                value=6,
                help="1 = Easy, 10 = Very Challenging"
            )
            
            certification_priority = st.checkbox(
                "Prioritize Certified Courses",
                value=True,
                help="Focus on courses offering certificates"
            )
        
        # Generate customized recommendations
        if st.button("🔄 Regenerate Path with Preferences", type="primary"):
            regenerate_customized_path(learning_path, {
                'study_pace': study_pace,
                'preferred_days': preferred_days,
                'break_weeks': break_weeks,
                'learning_style': learning_style,
                'difficulty_preference': difficulty_preference,
                'certification_priority': certification_priority
            })

def regenerate_customized_path(original_path: Dict[str, Any], preferences: Dict[str, Any]) -> None:
    """Regenerate learning path based on user preferences."""
    
    with st.spinner("🔄 Customizing your learning path..."):
        # Simulate path regeneration (in real implementation, this would call the backend)
        st.success("✅ Learning path updated based on your preferences!")
        
        # Show what changed
        st.info(f"""
        **Updated based on your preferences:**
        - Study pace: {preferences['study_pace']}
        - Preferred days: {', '.join(preferences['preferred_days'])}
        - Learning style: {preferences['learning_style']}
        - Challenge level: {preferences['difficulty_preference']}/10
        """)
        
        # Update session state to trigger re-render
        st.rerun()
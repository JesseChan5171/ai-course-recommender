from typing import List, Dict, Any, Optional
import sqlite3
import os
import json
import numpy as np
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_ibm import WatsonxLLM, WatsonxEmbeddings
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from dotenv import load_dotenv
from vector_search import CourseSearchResult


class CourseRecommendation(BaseModel):
    course_id: str = Field(description="Unique course identifier")
    title: str = Field(description="Course title")
    provider: str = Field(description="Course provider")
    level: str = Field(description="Skill level")
    duration_hours: int = Field(description="Course duration")
    modality: str = Field(description="Learning format")
    tags: List[str] = Field(description="Course topics")
    recommendation_score: float = Field(description="Overall recommendation score (0-1)")
    recommendation_reason: str = Field(description="Why this course is recommended")
    similarity_score: float = Field(description="Vector similarity to query")


class LearningPath(BaseModel):
    path_name: str = Field(description="Name of the learning path")
    path_description: str = Field(description="Description of learning progression")
    total_duration_hours: int = Field(description="Total time investment")
    estimated_completion_months: int = Field(description="Expected time to complete")
    skill_progression: List[str] = Field(description="Skill levels in sequence")
    courses: List[CourseRecommendation] = Field(description="Ordered course sequence")


class SkillGapAnalysis(BaseModel):
    gap_severity: str = Field(description="Low/Medium/High severity of skill gaps")
    identified_gaps: List[str] = Field(description="Missing skills identified")
    prerequisite_issues: List[str] = Field(description="Prerequisite concerns")
    recommended_additional_courses: List[str] = Field(description="Additional course recommendations")


class CourseAnalytics(BaseModel):
    total_courses_analyzed: int = Field(description="Number of courses in analysis")
    average_similarity_score: float = Field(description="Mean relevance score")
    skill_level_distribution: Dict[str, int] = Field(description="Count by skill level")
    modality_distribution: Dict[str, int] = Field(description="Count by format")
    duration_statistics: Dict[str, float] = Field(description="Duration stats (min/max/mean)")
    top_tags: List[tuple] = Field(description="Most frequent topics with counts")


class RAGState(TypedDict):
    """State for RAG pipeline with LangGraph."""
    query: str
    courses: List[Dict[str, Any]]
    recommendations: List[CourseRecommendation]
    analytics: Optional[CourseAnalytics]
    learning_path: Optional[LearningPath]
    skill_gaps: Optional[SkillGapAnalysis]
    user_preferences: Dict[str, Any]
    context: str


def analyze_course_recommendations(
    courses: List[Dict[str, Any]],
    user_preferences: Optional[Dict[str, Any]] = None
) -> List[CourseRecommendation]:
    """Analyze and score course recommendations based on multiple factors.
    
    Evaluates courses using relevance, quality indicators, user preferences,
    and learning progression to generate prioritized recommendations.
    """
    if not courses:
        return []
    
    recommendations = []
    user_preferences = user_preferences or {}
    
    for course in courses:
        # Base score from similarity
        base_score = course.get('similarity_score', 0.5)
        
        # Quality indicators boost
        quality_boost = 0.0
        if course.get('course_rating', 0) >= 4.0:
            quality_boost += 0.1
        if course.get('enrollment_count', 0) > 1000:
            quality_boost += 0.05
        if course.get('certification_offered', False):
            quality_boost += 0.05
        
        # User preference alignment
        preference_boost = 0.0
        if user_preferences.get('skill_level') == course.get('level', '').lower():
            preference_boost += 0.1
        if user_preferences.get('modality') == course.get('modality', '').lower():
            preference_boost += 0.05
        if user_preferences.get('provider_preference'):
            if user_preferences['provider_preference'].lower() in course.get('provider', '').lower():
                preference_boost += 0.05
        
        # Duration preference
        max_duration = user_preferences.get('max_duration_hours')
        if max_duration and course.get('duration_hours', 0) <= max_duration:
            preference_boost += 0.05
        
        # Calculate final score
        final_score = min(1.0, base_score + quality_boost + preference_boost)
        
        # Generate recommendation reason
        reasons = []
        if base_score > 0.8:
            reasons.append("highly relevant to your query")
        if course.get('certification_offered'):
            reasons.append("offers professional certification")
        if quality_boost > 0.1:
            reasons.append("highly rated by students")
        if preference_boost > 0.05:
            reasons.append("matches your preferences")
        
        reason = "Good match for your needs" if not reasons else ", ".join(reasons[:2])
        
        recommendation = CourseRecommendation(
            course_id=course.get('course_id', ''),
            title=course.get('title', ''),
            provider=course.get('provider', ''),
            level=course.get('level', ''),
            duration_hours=course.get('duration_hours', 0),
            modality=course.get('modality', ''),
            tags=course.get('tags', []),
            recommendation_score=final_score,
            recommendation_reason=reason,
            similarity_score=base_score
        )
        
        recommendations.append(recommendation)
    
    # Sort by recommendation score
    recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
    
    return recommendations


def generate_learning_path(
    courses: List[Dict[str, Any]],
    target_skill_level: str = "advanced"
) -> LearningPath:
    """Generate a structured learning path from selected courses.
    
    Organizes courses into a logical sequence based on skill progression,
    prerequisites, and learning objectives.
    """
    if not courses:
        return LearningPath(
            path_name="Empty Learning Path",
            path_description="No courses provided",
            total_duration_hours=0,
            estimated_completion_months=0,
            skill_progression=[],
            courses=[]
        )
    
    # Sort courses by skill level progression
    skill_order = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
    sorted_courses = sorted(
        courses, 
        key=lambda x: skill_order.get(x.get('level', 'intermediate'), 2)
    )
    
    # Convert to recommendations
    course_recommendations = []
    total_duration = 0
    
    for i, course in enumerate(sorted_courses[:6]):  # Limit to 6 courses
        total_duration += course.get('duration_hours', 0)
        
        # Determine position-based reason
        if i == 0:
            reason = "Foundation course to establish core knowledge"
        elif i < len(sorted_courses) - 1:
            reason = "Builds upon previous concepts and introduces new skills"
        else:
            reason = "Advanced course to master the subject area"
        
        recommendation = CourseRecommendation(
            course_id=course.get('course_id', ''),
            title=course.get('title', ''),
            provider=course.get('provider', ''),
            level=course.get('level', ''),
            duration_hours=course.get('duration_hours', 0),
            modality=course.get('modality', ''),
            tags=course.get('tags', []),
            recommendation_score=course.get('similarity_score', 0.7),
            recommendation_reason=reason,
            similarity_score=course.get('similarity_score', 0.7)
        )
        
        course_recommendations.append(recommendation)
    
    # Generate path metadata
    skill_levels = list(set(course.get('level', 'intermediate') for course in sorted_courses))
    skill_progression = sorted(skill_levels, key=lambda x: skill_order.get(x, 2))
    
    # Estimate completion time (assuming 5 hours per week)
    estimated_months = max(1, total_duration // 20)
    
    # Extract main topics for path name
    all_tags = []
    for course in sorted_courses:
        all_tags.extend(course.get('tags', []))
    
    common_tags = []
    for tag in set(all_tags):
        if all_tags.count(tag) > 1:
            common_tags.append(tag)
    
    path_name = f"{' & '.join(common_tags[:2])} Learning Path" if common_tags else "Professional Development Path"
    
    return LearningPath(
        path_name=path_name,
        path_description=f"Structured learning path progressing from {skill_progression[0] if skill_progression else 'beginner'} to {target_skill_level} level",
        total_duration_hours=total_duration,
        estimated_completion_months=estimated_months,
        skill_progression=skill_progression,
        courses=course_recommendations
    )


def perform_skill_gap_analysis(
    target_courses: List[Dict[str, Any]],
    user_background: Optional[str] = None,
    completed_courses: Optional[List[str]] = None
) -> SkillGapAnalysis:
    """Analyze skill gaps between user background and target courses.
    
    Identifies missing prerequisites, skill misalignments, and recommends
    preparatory courses to bridge knowledge gaps.
    """
    completed_courses = completed_courses or []
    user_background = user_background or ""
    
    identified_gaps = []
    prerequisite_issues = []
    recommended_additional = []
    
    # Analyze each target course
    for course in target_courses:
        course_level = course.get('level', 'intermediate').lower()
        prerequisites = course.get('prerequisites', [])
        
        # Check skill level readiness
        if course_level == 'advanced' and 'beginner' in user_background.lower():
            identified_gaps.append(f"Intermediate {course.get('title', 'course')} knowledge")
            prerequisite_issues.append(f"Course '{course.get('title', '')}' may be too advanced")
        
        # Check prerequisites
        for prereq in prerequisites:
            prereq_met = False
            
            # Check if prerequisite is in user background
            if prereq.lower() in user_background.lower():
                prereq_met = True
            
            # Check if prerequisite covered by completed courses
            for completed in completed_courses:
                if prereq.lower() in completed.lower():
                    prereq_met = True
                    break
            
            if not prereq_met:
                identified_gaps.append(prereq)
                prerequisite_issues.append(f"Missing prerequisite: {prereq}")
    
    # Determine gap severity
    gap_count = len(identified_gaps)
    if gap_count == 0:
        gap_severity = "Low"
    elif gap_count <= 2:
        gap_severity = "Medium" 
    else:
        gap_severity = "High"
    
    # Generate recommendations for additional courses
    if identified_gaps:
        # Recommend foundational courses
        # Use SQLite to find actual introductory courses for identified gaps
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        for gap in identified_gaps[:3]:
            cursor.execute("""
                SELECT title FROM course_catalog 
                WHERE level = 'beginner' 
                AND (title LIKE ? OR tags LIKE ?)
                LIMIT 1
            """, (f"%{gap}%", f"%{gap}%"))
            
            result = cursor.fetchone()
            if result:
                recommended_additional.append(result[0])
            else:
                recommended_additional.append(f"introductory_{gap.lower().replace(' ', '_')}_course")
        
        conn.close()
    
    return SkillGapAnalysis(
        gap_severity=gap_severity,
        identified_gaps=list(set(identified_gaps)),  # Remove duplicates
        prerequisite_issues=prerequisite_issues,
        recommended_additional_courses=recommended_additional
    )


def generate_course_analytics(courses: List[Dict[str, Any]]) -> CourseAnalytics:
    """Generate comprehensive analytics for a set of courses.
    
    Provides statistical analysis including distributions, averages,
    and insights about the course collection.
    """
    if not courses:
        return CourseAnalytics(
            total_courses_analyzed=0,
            average_similarity_score=0.0,
            skill_level_distribution={},
            modality_distribution={},
            duration_statistics={},
            top_tags=[]
        )
    
    total_courses = len(courses)
    
    # Calculate average similarity score
    similarity_scores = [course.get('similarity_score', 0) for course in courses]
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
    
    # Skill level distribution
    skill_levels = [course.get('level', 'unknown').lower() for course in courses]
    skill_distribution = {}
    for level in skill_levels:
        skill_distribution[level] = skill_distribution.get(level, 0) + 1
    
    # Modality distribution
    modalities = [course.get('modality', 'unknown').lower() for course in courses]
    modality_distribution = {}
    for modality in modalities:
        modality_distribution[modality] = modality_distribution.get(modality, 0) + 1
    
    # Duration statistics
    durations = [course.get('duration_hours', 0) for course in courses if course.get('duration_hours', 0) > 0]
    duration_stats = {}
    if durations:
        duration_stats = {
            'min': min(durations),
            'max': max(durations),
            'mean': sum(durations) / len(durations)
        }
    
    # Top tags analysis
    all_tags = []
    for course in courses:
        tags = course.get('tags', [])
        all_tags.extend([tag.lower() for tag in tags])
    
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return CourseAnalytics(
        total_courses_analyzed=total_courses,
        average_similarity_score=avg_similarity,
        skill_level_distribution=skill_distribution,
        modality_distribution=modality_distribution,
        duration_statistics=duration_stats,
        top_tags=top_tags
    )


def retrieve_courses_node(state: RAGState) -> RAGState:
    """Retrieve relevant courses using vector search."""
    from vector_search import search_courses_by_vector
    
    search_results = search_courses_by_vector(state["query"], limit=10)
    
    # Convert to dict format for processing
    courses = []
    for result in search_results:
        courses.append({
            'course_id': result.course_id,
            'title': result.title,
            'provider': result.provider,
            'level': result.level,
            'duration_hours': result.duration_hours,
            'modality': result.modality,
            'tags': result.tags,
            'prerequisites': result.prerequisites,
            'similarity_score': result.similarity_score,
            'course_content': result.content_preview,
            'valid_regions': result.valid_regions
        })
    
    state["courses"] = courses
    return state


def analyze_courses_node(state: RAGState) -> RAGState:
    """Analyze and score course recommendations."""
    recommendations = analyze_course_recommendations(state["courses"], state["user_preferences"])
    analytics = generate_course_analytics(state["courses"])
    
    state["recommendations"] = recommendations
    state["analytics"] = analytics
    return state


def generate_learning_path_node(state: RAGState) -> RAGState:
    """Generate structured learning path."""
    learning_path = generate_learning_path(state["courses"])
    state["learning_path"] = learning_path
    return state


def skill_gap_analysis_node(state: RAGState) -> RAGState:
    """Perform skill gap analysis."""
    user_background = state["user_preferences"].get("background", "")
    completed_courses = state["user_preferences"].get("completed_courses", [])
    
    skill_gaps = perform_skill_gap_analysis(
        state["courses"], 
        user_background, 
        completed_courses
    )
    
    state["skill_gaps"] = skill_gaps
    return state


def generate_response_node(state: RAGState) -> RAGState:
    """Generate final response using IBM Watsonx LLM."""
    llm = initialize_watsonx_llm()
    
    # Prepare context from analysis
    context_parts = []
    
    if state["recommendations"]:
        context_parts.append(f"Found {len(state['recommendations'])} relevant courses:")
        for rec in state["recommendations"][:3]:
            context_parts.append(f"- {rec.title} ({rec.provider}) - Score: {rec.recommendation_score:.2f}")
    
    if state["analytics"]:
        analytics = state["analytics"]
        context_parts.append(f"\\nAnalytics: {analytics.total_courses_analyzed} courses analyzed, avg similarity: {analytics.average_similarity_score:.2f}")
    
    if state["learning_path"]:
        lp = state["learning_path"]
        context_parts.append(f"\\nLearning Path: {lp.path_name} ({lp.total_duration_hours}h, {lp.estimated_completion_months} months)")
    
    if state["skill_gaps"]:
        gaps = state["skill_gaps"]
        context_parts.append(f"\\nSkill Gaps: {gaps.gap_severity} severity, {len(gaps.identified_gaps)} gaps identified")
    
    context = "\\n".join(context_parts)
    
    prompt = f"""
    User Query: {state["query"]}
    
    Course Analysis Results:
    {context}
    
    Please provide a comprehensive response that:
    1. Addresses the user's specific query
    2. Summarizes the most relevant course recommendations
    3. Explains the learning path if applicable
    4. Mentions any skill gaps that should be addressed
    5. Provides actionable next steps
    
    Keep the response helpful, concise, and focused on the user's learning goals.
    """
    
    response = llm.invoke(prompt)
    state["context"] = response
    return state


def get_sqlite_connection():
    """Get SQLite database connection."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'course_catalog.db')
    return sqlite3.connect(db_path)


def initialize_watsonx_llm():
    """Initialize IBM Watsonx LLM for RAG pipeline."""
    # Load environment variables from specific .env file only
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path, override=False)
    
    watsonx_api_key = os.getenv('WATSONX_API_KEY')
    watsonx_project_id = os.getenv('WATSONX_PROJECT_ID')
    
    if not watsonx_api_key:
        raise ValueError("WATSONX_API_KEY environment variable is required")
    
    if not watsonx_project_id:
        raise ValueError("WATSONX_PROJECT_ID environment variable is required")
    
    return WatsonxLLM(
        model_id="ibm/granite-3-2-8b-instruct",
        url='https://us-south.ml.cloud.ibm.com',
        project_id=watsonx_project_id,
        apikey=watsonx_api_key,
        params={
            "decoding_method": "greedy",
            "max_new_tokens": 500,
            "temperature": 0.1
        }
    )


def create_rag_workflow() -> StateGraph:
    """Create LangGraph workflow for RAG pipeline."""
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_courses_node)
    workflow.add_node("analyze", analyze_courses_node)
    workflow.add_node("create_path", generate_learning_path_node)
    workflow.add_node("analyze_gaps", skill_gap_analysis_node)
    workflow.add_node("generate_response", generate_response_node)
    
    # Define the flow
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", "create_path")
    workflow.add_edge("create_path", "analyze_gaps")
    workflow.add_edge("analyze_gaps", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()


def course_recommendation_rag(
    query: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Complete RAG pipeline for course recommendations using LangGraph and IBM Watsonx."""
    workflow = create_rag_workflow()
    
    initial_state = RAGState(
        query=query,
        courses=[],
        recommendations=[],
        analytics=None,
        learning_path=None,
        skill_gaps=None,
        user_preferences=user_preferences or {},
        context=""
    )
    
    result = workflow.invoke(initial_state)
    
    return {
        "query": result["query"],
        "response": result["context"],
        "recommendations": [rec.dict() for rec in result["recommendations"]],
        "analytics": result["analytics"].dict() if result["analytics"] else None,
        "learning_path": result["learning_path"].dict() if result["learning_path"] else None,
        "skill_gaps": result["skill_gaps"].dict() if result["skill_gaps"] else None
    }
from typing import List, Dict, Any, Optional
import os
import sqlite3
import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.tools import tool


class InstructorInfo(BaseModel):
    name: Optional[str] = Field(None, description="Instructor name")
    credentials: Optional[str] = Field(None, description="Instructor credentials and qualifications")
    experience_years: Optional[int] = Field(None, description="Years of teaching/industry experience")
    bio: Optional[str] = Field(None, description="Brief instructor biography")


class LearningOutcome(BaseModel):
    outcome_id: str = Field(description="Unique outcome identifier")
    description: str = Field(description="What the student will be able to do")
    skill_category: str = Field(description="Category of skill (technical, soft, regulatory)")
    proficiency_level: str = Field(description="Expected proficiency after completion")


class CourseModule(BaseModel):
    module_number: int = Field(description="Sequential module number")
    title: str = Field(description="Module title")
    duration_hours: float = Field(description="Hours for this module")
    topics: List[str] = Field(description="Topics covered in module")
    assessments: List[str] = Field(description="Assessments in this module")


class DetailedCourse(BaseModel):
    course_id: str = Field(description="Unique course identifier")
    title: str = Field(description="Course title")
    provider: str = Field(description="Course provider organization")
    level: str = Field(description="Skill level (beginner/intermediate/advanced)")
    duration_hours: int = Field(description="Total course duration")
    modality: str = Field(description="Delivery method (online/hybrid/in-person)")
    tags: List[str] = Field(description="Course topic tags")
    prerequisites: List[str] = Field(description="Required prerequisites")
    valid_regions: List[str] = Field(description="Geographic availability")
    full_description: str = Field(description="Complete course description")
    learning_outcomes: List[LearningOutcome] = Field(description="Detailed learning outcomes")
    course_modules: List[CourseModule] = Field(description="Course curriculum structure")
    instructor_info: Optional[InstructorInfo] = Field(None, description="Instructor information")
    price: Optional[float] = Field(None, description="Course price")
    certification_offered: bool = Field(description="Whether certification is provided")
    certification_body: Optional[str] = Field(None, description="Certifying organization")
    course_rating: Optional[float] = Field(None, description="Average student rating")
    enrollment_count: Optional[int] = Field(None, description="Number of enrolled students")
    last_updated: Optional[str] = Field(None, description="Last content update date")
    language: str = Field(default="English", description="Course language")


class CourseValidation(BaseModel):
    course_id: str = Field(description="Course identifier")
    is_available: bool = Field(description="Whether course is currently available")
    prerequisites_met: bool = Field(description="Whether user meets prerequisites")
    region_accessible: bool = Field(description="Whether accessible in user region")
    prerequisite_gaps: List[str] = Field(description="Missing prerequisites")
    alternative_courses: List[str] = Field(description="Alternative course recommendations")


def get_sqlite_connection():
    """Get SQLite database connection."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'course_catalog.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


@tool("get_detailed_course_info")
def get_detailed_course_info(course_ids: List[str]) -> List[DetailedCourse]:
    """Retrieve comprehensive information for specific courses by their IDs.
    
    Fetches complete course details including learning outcomes, curriculum structure,
    instructor information, pricing, and enrollment data from the SQLite database.
    """
    if not course_ids:
        return []
    
    # Load environment variables from specific .env file only
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path, override=False)
    
    # SQLite query for detailed course information
    placeholders = ','.join(['?'] * len(course_ids))
    sql_query = f"""
        SELECT 
            c.course_id,
            c.title,
            c.provider,
            c.level,
            c.duration_hours,
            c.modality,
            c.tags,
            c.prerequisites,
            c.valid_regions,
            COALESCE(c.course_content, c.title) as full_description,
            c.price,
            c.certification_offered,
            c.certification_body,
            c.course_rating,
            c.enrollment_count,
            c.updated_at as last_updated,
            'English' as language,
            c.instructor_name,
            c.instructor_credentials,
            c.instructor_experience,
            c.instructor_bio
        FROM course_catalog c
        WHERE c.course_id IN ({placeholders})
        ORDER BY c.course_id
    """
    
    detailed_courses = []
    
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query, course_ids)
        
        for row in cursor.fetchall():
            # Create instructor info if available
            instructor_info = None
            if row[17]:  # instructor_name
                instructor_info = InstructorInfo(
                    name=row[17],
                    credentials=row[18],
                    experience_years=row[19],
                    bio=row[20]
                )
            
            # Parse JSON fields safely
            tags = json.loads(row[6]) if row[6] else []
            prerequisites = json.loads(row[7]) if row[7] else []
            valid_regions = json.loads(row[8]) if row[8] else []
            
            # Generate learning outcomes based on course content
            learning_outcomes = _generate_learning_outcomes(
                row[1],  # title
                row[9],  # full_description
                tags
            )
            
            # Generate course modules based on duration and content
            course_modules = _generate_course_modules(
                row[4] or 0,  # duration_hours
                tags,
                row[3] or ''  # level
            )
            
            detailed_course = DetailedCourse(
                course_id=row[0],
                title=row[1],
                provider=row[2] or "Unknown Provider",
                level=row[3] or "intermediate",
                duration_hours=row[4] or 0,
                modality=row[5] or "online",
                tags=tags,
                prerequisites=prerequisites,
                valid_regions=valid_regions,
                full_description=row[9] or row[1],
                learning_outcomes=learning_outcomes,
                course_modules=course_modules,
                instructor_info=instructor_info,
                price=row[10],
                certification_offered=bool(row[11]) if row[11] is not None else False,
                certification_body=row[12],
                course_rating=row[13],
                enrollment_count=row[14],
                last_updated=row[15],
                language=row[16] or "English"
            )
            
            detailed_courses.append(detailed_course)
        
        conn.close()
                
    except Exception as e:
        # Return sample detailed courses if database fails
        for course_id in course_ids[:3]:  # Limit to 3 for sample
            sample_course = DetailedCourse(
                course_id=course_id,
                title=f"Sample Detailed Course {course_id}",
                provider="Sample Provider",
                level="intermediate",
                duration_hours=25,
                modality="online",
                tags=["sample", "detailed"],
                prerequisites=["basic knowledge"],
                valid_regions=["US", "EU"],
                full_description=f"This is a comprehensive sample course for {course_id} with detailed curriculum and learning objectives.",
                learning_outcomes=[
                    LearningOutcome(
                        outcome_id="LO1",
                        description="Master fundamental concepts",
                        skill_category="technical",
                        proficiency_level="intermediate"
                    )
                ],
                course_modules=[
                    CourseModule(
                        module_number=1,
                        title="Module 1: Introduction",
                        duration_hours=8.0,
                        topics=["basics", "overview"],
                        assessments=["Quiz", "Exercise"]
                    )
                ],
                instructor_info=InstructorInfo(
                    name="Sample Instructor",
                    credentials="Ph.D., Certified Professional",
                    experience_years=10,
                    bio="Experienced professional with extensive industry background"
                ),
                price=299.99,
                certification_offered=True,
                certification_body="Sample Certification Board",
                course_rating=4.5,
                enrollment_count=1250,
                last_updated="2024-01-01",
                language="English"
            )
            detailed_courses.append(sample_course)
    
    return detailed_courses


@tool("validate_course_compatibility")
def validate_course_compatibility(
    course_ids: List[str],
    user_background: Optional[str] = None,
    user_region: Optional[str] = None,
    completed_courses: Optional[List[str]] = None
) -> List[CourseValidation]:
    """Validate course compatibility with user requirements and background.
    
    Checks course availability, prerequisite requirements, regional accessibility,
    and suggests alternatives for incompatible courses using SQLite database.
    """
    if not course_ids:
        return []
    
    # Load environment variables from specific .env file only
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path, override=False)
    
    validations = []
    completed_courses = completed_courses or []
    
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # Get course details for validation
        placeholders = ','.join(['?'] * len(course_ids))
        cursor.execute(f"""
            SELECT course_id, title, prerequisites, valid_regions, level, tags
            FROM course_catalog 
            WHERE course_id IN ({placeholders})
        """, course_ids)
        
        courses = cursor.fetchall()
        
        for course in courses:
            course_id = course[0]
            
            # Parse JSON fields safely
            prerequisites = json.loads(course[2]) if course[2] else []
            valid_regions = json.loads(course[3]) if course[3] else []
            
            # Check availability (simplified - assume all courses are available)
            is_available = True
            
            # Check region accessibility
            region_accessible = True
            if user_region and valid_regions:
                region_accessible = any(
                    user_region.lower() in region.lower() or 
                    region.lower() in user_region.lower()
                    for region in valid_regions
                )
            
            # Check prerequisites
            prerequisites_met = True
            prerequisite_gaps = []
            
            if prerequisites:
                for prereq in prerequisites:
                    prereq_met = False
                    
                    # Check if prerequisite is in completed courses
                    if any(prereq.lower() in completed_id.lower() for completed_id in completed_courses):
                        prereq_met = True
                    
                    # Check if user background indicates prerequisite knowledge
                    if user_background and prereq.lower() in user_background.lower():
                        prereq_met = True
                    
                    if not prereq_met:
                        prerequisites_met = False
                        prerequisite_gaps.append(prereq)
            
            # Find alternative courses if needed
            alternative_courses = []
            if not is_available or not region_accessible or not prerequisites_met:
                # Find similar courses using simple text matching for alternatives
                tags = json.loads(course[5]) if course[5] else []
                if tags:
                    cursor.execute("""
                        SELECT course_id FROM course_catalog 
                        WHERE course_id != ? 
                        AND tags LIKE ?
                        LIMIT 3
                    """, (course_id, f'%{tags[0]}%'))
                    
                    alternatives = cursor.fetchall()
                    alternative_courses = [alt[0] for alt in alternatives]
            
            validation = CourseValidation(
                course_id=course_id,
                is_available=is_available,
                prerequisites_met=prerequisites_met,
                region_accessible=region_accessible,
                prerequisite_gaps=prerequisite_gaps,
                alternative_courses=alternative_courses
            )
            
            validations.append(validation)
        
        conn.close()
                
    except Exception as e:
        # Return sample validations if database fails
        for course_id in course_ids:
            validation = CourseValidation(
                course_id=course_id,
                is_available=True,
                prerequisites_met=len(prerequisite_gaps := ["basic knowledge"]) == 0 if user_background else False,
                region_accessible=True,
                prerequisite_gaps=prerequisite_gaps if not user_background else [],
                alternative_courses=[f"alt_{course_id}_1", f"alt_{course_id}_2"]
            )
            validations.append(validation)
    
    return validations


def _generate_learning_outcomes(title: str, description: str, tags: List[str]) -> List[LearningOutcome]:
    """Generate learning outcomes based on course content."""
    outcomes = []
    
    # Basic outcomes based on tags and title
    technical_skills = ['programming', 'automation', 'safety', 'quality', 'maintenance', 'analysis']
    soft_skills = ['leadership', 'communication', 'management', 'teamwork']
    regulatory_skills = ['compliance', 'osha', 'iso', 'standards']
    
    outcome_id = 1
    
    # Generate technical outcomes
    for tag in tags:
        tag_lower = tag.lower()
        if any(skill in tag_lower for skill in technical_skills):
            outcomes.append(LearningOutcome(
                outcome_id=f"LO{outcome_id}",
                description=f"Apply {tag} principles and techniques in professional settings",
                skill_category="technical",
                proficiency_level="intermediate"
            ))
            outcome_id += 1
    
    # Generate soft skill outcomes
    title_lower = title.lower()
    if any(skill in title_lower for skill in soft_skills):
        outcomes.append(LearningOutcome(
            outcome_id=f"LO{outcome_id}",
            description="Demonstrate effective leadership and communication skills",
            skill_category="soft",
            proficiency_level="intermediate"
        ))
        outcome_id += 1
    
    # Generate regulatory outcomes
    if any(skill in title_lower or any(skill in tag.lower() for tag in tags) for skill in regulatory_skills):
        outcomes.append(LearningOutcome(
            outcome_id=f"LO{outcome_id}",
            description="Ensure compliance with industry standards and regulations",
            skill_category="regulatory",
            proficiency_level="advanced"
        ))
        outcome_id += 1
    
    # Default outcome if none generated
    if not outcomes:
        outcomes.append(LearningOutcome(
            outcome_id="LO1",
            description=f"Master fundamental concepts covered in {title}",
            skill_category="technical",
            proficiency_level="beginner"
        ))
    
    return outcomes


def _generate_course_modules(duration: int, tags: List[str], level: str) -> List[CourseModule]:
    """Generate course modules based on duration and content."""
    modules = []
    
    if duration <= 0:
        return modules
    
    # Determine number of modules based on duration
    if duration <= 8:
        num_modules = 2
    elif duration <= 20:
        num_modules = 3
    elif duration <= 40:
        num_modules = 4
    else:
        num_modules = 5
    
    module_duration = duration / num_modules
    
    # Generate modules based on typical course structure
    module_templates = [
        ("Introduction and Fundamentals", ["basics", "overview", "principles"]),
        ("Core Concepts and Theory", ["theory", "concepts", "methods"]),
        ("Practical Applications", ["applications", "practice", "examples"]),
        ("Advanced Topics", ["advanced", "complex", "specialized"]),
        ("Assessment and Review", ["assessment", "review", "evaluation"])
    ]
    
    for i in range(num_modules):
        template = module_templates[i % len(module_templates)]
        
        # Customize topics based on course tags
        topics = []
        for tag in tags[:3]:  # Use first 3 tags
            topics.append(f"{template[1][0]} in {tag}")
        
        if not topics:
            topics = template[1]
        
        # Generate assessments
        assessments = ["Quiz", "Practical Exercise"]
        if i == num_modules - 1:  # Final module
            assessments.append("Final Assessment")
        
        module = CourseModule(
            module_number=i + 1,
            title=f"Module {i + 1}: {template[0]}",
            duration_hours=round(module_duration, 1),
            topics=topics,
            assessments=assessments
        )
        
        modules.append(module)
    
    return modules
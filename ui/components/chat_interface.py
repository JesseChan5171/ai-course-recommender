"""
Chat Interface Components for Streamlit UI
Provides conversational AI interface for course recommendations.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time

def render_chat_interface() -> None:
    """
    Render the main chat interface for conversational course recommendations.
    """
    st.markdown("### 💬 AI Learning Advisor Chat")
    st.caption("Ask me anything about courses, learning paths, or career guidance!")
    
    # Initialize chat if not exists
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI Learning Advisor. I can help you find the perfect courses based on your goals, background, and preferences. What would you like to learn today?",
                "timestamp": datetime.now()
            }
        ]
    
    # Chat container with custom styling
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        render_chat_history()
        
        # Quick suggestion buttons
        render_quick_suggestions()
        
        # Chat input area
        render_chat_input()
        
        # Chat controls
        render_chat_controls()

def render_chat_history() -> None:
    """Render the chat message history with proper styling."""
    
    # Create scrollable chat area
    with st.container():
        for i, message in enumerate(st.session_state.chat_messages):
            render_chat_message(message, i)

def render_chat_message(message: Dict[str, Any], index: int) -> None:
    """
    Render a single chat message with appropriate styling.
    
    Args:
        message: Message dictionary with role, content, and timestamp
        index: Message index for unique keys
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    timestamp = message.get("timestamp", datetime.now())
    
    # Message container with role-based styling
    if role == "user":
        # User message (right aligned, blue theme)
        st.markdown(f"""
        <div class="chat-message user-message">
            <div style="text-align: right;">
                <strong>🧑‍💼 You</strong>
                <small style="color: #666; margin-left: 10px;">
                    {timestamp.strftime("%H:%M")}
                </small>
            </div>
            <div style="margin-top: 5px; text-align: right;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Assistant message (left aligned, dark theme)
        st.markdown(f"""
        <div class="chat-message ai-message">
            <div>
                <strong>🤖 AI Learning Advisor</strong>
                <small style="color: #cbd5e0; margin-left: 10px;">
                    {timestamp.strftime("%H:%M")}
                </small>
            </div>
            <div style="margin-top: 5px;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add action buttons for AI responses
        render_message_actions(message, index)

def render_message_actions(message: Dict[str, Any], index: int) -> None:
    """
    Render action buttons for AI messages.
    
    Args:
        message: AI message dictionary
        index: Message index for unique keys
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👍", key=f"like_{index}", help="Helpful response"):
            rate_message(message, "positive")
    
    with col2:
        if st.button("👎", key=f"dislike_{index}", help="Not helpful"):
            rate_message(message, "negative")
    
    with col3:
        if st.button("🔄", key=f"regenerate_{index}", help="Regenerate response"):
            regenerate_response(index)
    
    with col4:
        if st.button("📋", key=f"copy_{index}", help="Copy response"):
            copy_to_clipboard(message["content"])

def render_quick_suggestions() -> None:
    """Render quick suggestion buttons for common queries."""
    st.markdown("**💡 Quick Questions:**")
    
    suggestions = [
        "I'm new to programming, where should I start?",
        "Best courses for data science career transition?",
        "How to learn machine learning in 3 months?",
        "What skills do I need for web development?",
        "Recommend courses for cloud computing?",
        "Best Python courses for automation?"
    ]
    
    # Display suggestions in rows of 3
    for i in range(0, len(suggestions), 3):
        cols = st.columns(3)
        for j, suggestion in enumerate(suggestions[i:i+3]):
            with cols[j]:
                if st.button(suggestion, key=f"chat_suggestion_{i+j}", use_container_width=True):
                    send_chat_message(suggestion)

def render_chat_input() -> None:
    """Render the chat input area with advanced features."""
    
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "Type your message...",
                placeholder="Ask me about courses, learning paths, skills, career advice, or anything related to your learning journey!",
                height=100,
                key="chat_input",
                help="Tip: Be specific about your goals, current level, and preferences for better recommendations!"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            send_button = st.form_submit_button("Send 📤", use_container_width=True, type="primary")
            
            # Advanced options
            with st.expander("⚙️ Options"):
                include_context = st.checkbox("Include search context", value=True)
                response_style = st.selectbox(
                    "Response style",
                    ["Detailed", "Concise", "Step-by-step", "Conversational"],
                    index=0
                )
                max_courses = st.slider("Max courses to suggest", 1, 10, 5)
        
        # Process message when sent
        if send_button and user_input.strip():
            send_chat_message(
                user_input,
                include_context=include_context,
                response_style=response_style,
                max_courses=max_courses
            )

def render_chat_controls() -> None:
    """Render chat control buttons and options."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_chat_history()
    
    with col2:
        if st.button("💾 Export Chat", use_container_width=True):
            export_chat_history()
    
    with col3:
        if st.button("📊 Chat Stats", use_container_width=True):
            show_chat_statistics()
    
    with col4:
        if st.button("🎯 New Topic", use_container_width=True):
            start_new_topic()

def send_chat_message(
    message: str,
    include_context: bool = True,
    response_style: str = "Detailed",
    max_courses: int = 5
) -> None:
    """
    Send a chat message and get AI response.
    
    Args:
        message: User's message
        include_context: Whether to include search context
        response_style: Style of AI response
        max_courses: Maximum courses to include in response
    """
    # Add user message to history
    add_message_to_history("user", message)
    
    # Show typing indicator
    with st.spinner("🤖 AI is thinking..."):
        try:
            # Get AI response using RAG pipeline
            response = get_ai_chat_response(
                message,
                include_context=include_context,
                response_style=response_style,
                max_courses=max_courses
            )
            
            # Add AI response to history
            add_message_to_history("assistant", response)
            
            # Rerun to update chat display
            st.rerun()
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}. Please try rephrasing your question."
            add_message_to_history("assistant", error_msg)
            st.error("Chat service temporarily unavailable.")

def get_ai_chat_response(
    message: str,
    include_context: bool = True,
    response_style: str = "Detailed",
    max_courses: int = 5
) -> str:
    """
    Get AI response using the course recommendation RAG pipeline.
    
    Args:
        message: User's message
        include_context: Whether to include search context
        response_style: Style of response
        max_courses: Maximum courses to include
        
    Returns:
        AI response string
    """
    try:
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        src_path = os.path.join(project_root, 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from course_analytics import course_recommendation_rag
        
        # Prepare user preferences from session state
        user_preferences = st.session_state.get('user_profile', {})
        
        # Add chat-specific preferences
        user_preferences.update({
            'response_style': response_style,
            'max_courses': max_courses,
            'include_context': include_context
        })
        
        # Get RAG response
        result = course_recommendation_rag(
            query=message,
            user_preferences=user_preferences
        )
        
        # Format response based on style
        ai_response = result.get('response', 'I apologize, but I could not generate a response.')
        
        # Add course recommendations if available
        if result.get('recommendations') and max_courses > 0:
            recommendations = result['recommendations'][:max_courses]
            
            if response_style == "Concise":
                course_summary = f"\n\n**Top {len(recommendations)} Recommendations:**\n"
                for i, rec in enumerate(recommendations, 1):
                    course_summary += f"{i}. {rec['title']} ({rec['provider']}) - Score: {rec['recommendation_score']:.2f}\n"
                ai_response += course_summary
                
            elif response_style == "Step-by-step":
                ai_response += f"\n\n**📚 Step-by-Step Learning Path:**\n"
                for i, rec in enumerate(recommendations, 1):
                    ai_response += f"\n**Step {i}: {rec['title']}**\n"
                    ai_response += f"- Provider: {rec['provider']}\n"
                    ai_response += f"- Level: {rec['level'].title()}\n"
                    ai_response += f"- Duration: {rec['duration_hours']} hours\n"
                    ai_response += f"- Why: {rec['recommendation_reason']}\n"
        
        # Add learning path info if available
        if result.get('learning_path') and response_style != "Concise":
            lp = result['learning_path']
            ai_response += f"\n\n**🎯 Suggested Learning Path: {lp['path_name']}**\n"
            ai_response += f"- Total Duration: {lp['total_duration_hours']} hours\n"
            ai_response += f"- Estimated Completion: {lp['estimated_completion_months']} months\n"
        
        # Add skill gaps if high severity
        if result.get('skill_gaps') and result['skill_gaps']['gap_severity'] in ['Medium', 'High']:
            gaps = result['skill_gaps']
            ai_response += f"\n\n**⚠️ Skill Gap Alert ({gaps['gap_severity']} severity):**\n"
            if gaps.get('identified_gaps'):
                ai_response += f"Consider strengthening: {', '.join(gaps['identified_gaps'][:3])}\n"
        
        return ai_response
        
    except Exception as e:
        return f"I apologize, but I'm having trouble accessing the course database right now. Error: {str(e)}\n\nPlease try asking a different question or check back in a moment."

def add_message_to_history(role: str, content: str) -> None:
    """
    Add a message to the chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
    """
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    }
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    st.session_state.chat_messages.append(message)
    
    # Limit chat history to prevent memory issues
    if len(st.session_state.chat_messages) > 50:
        st.session_state.chat_messages = st.session_state.chat_messages[-40:]

def rate_message(message: Dict[str, Any], rating: str) -> None:
    """
    Rate an AI message for feedback.
    
    Args:
        message: Message dictionary
        rating: 'positive' or 'negative'
    """
    if 'message_ratings' not in st.session_state:
        st.session_state.message_ratings = {}
    
    message_id = f"{message['timestamp']}_{message['content'][:50]}"
    st.session_state.message_ratings[message_id] = rating
    
    if rating == "positive":
        st.success("👍 Thanks for the feedback!")
    else:
        st.info("👎 Feedback noted. I'll try to improve!")

def regenerate_response(message_index: int) -> None:
    """
    Regenerate the AI response for a given message.
    
    Args:
        message_index: Index of the message to regenerate
    """
    if message_index > 0 and message_index < len(st.session_state.chat_messages):
        # Get the previous user message
        user_message = st.session_state.chat_messages[message_index - 1]
        
        if user_message["role"] == "user":
            # Remove the current AI response
            st.session_state.chat_messages.pop(message_index)
            
            # Regenerate response
            send_chat_message(user_message["content"])

def copy_to_clipboard(text: str) -> None:
    """
    Copy text to clipboard (simulation with display).
    
    Args:
        text: Text to copy
    """
    # Since we can't actually copy to clipboard in Streamlit,
    # we'll show the text in a text area for manual copying
    st.info("📋 Text ready to copy:")
    st.text_area("Copy this text:", value=text, height=100)

def clear_chat_history() -> None:
    """Clear the entire chat history."""
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": "Chat cleared! How can I help you with your learning journey today?",
            "timestamp": datetime.now()
        }
    ]
    st.success("🗑️ Chat history cleared!")
    st.rerun()

def export_chat_history() -> None:
    """Export chat history as JSON."""
    if 'chat_messages' not in st.session_state or not st.session_state.chat_messages:
        st.warning("No chat history to export.")
        return
    
    # Prepare export data
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_messages": len(st.session_state.chat_messages),
        "user_profile": st.session_state.get('user_profile', {}),
        "messages": []
    }
    
    for msg in st.session_state.chat_messages:
        export_data["messages"].append({
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg["timestamp"].isoformat()
        })
    
    # Create download
    json_str = json.dumps(export_data, indent=2)
    filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    st.download_button(
        label="💾 Download Chat History",
        data=json_str,
        file_name=filename,
        mime="application/json"
    )

def show_chat_statistics() -> None:
    """Show chat statistics and analytics."""
    if 'chat_messages' not in st.session_state or not st.session_state.chat_messages:
        st.info("No chat data available for statistics.")
        return
    
    with st.expander("📊 Chat Statistics", expanded=True):
        messages = st.session_state.chat_messages
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_messages = len(messages)
            user_messages = len([m for m in messages if m["role"] == "user"])
            st.metric("Total Messages", total_messages)
            st.metric("Your Messages", user_messages)
        
        with col2:
            ai_messages = len([m for m in messages if m["role"] == "assistant"])
            avg_length = sum(len(m["content"]) for m in messages) / len(messages)
            st.metric("AI Responses", ai_messages)
            st.metric("Avg Message Length", f"{avg_length:.0f} chars")
        
        with col3:
            if messages:
                session_duration = messages[-1]["timestamp"] - messages[0]["timestamp"]
                st.metric("Session Duration", f"{session_duration.seconds // 60} min")
            
            ratings = st.session_state.get('message_ratings', {})
            positive_ratings = len([r for r in ratings.values() if r == "positive"])
            st.metric("Positive Ratings", positive_ratings)

def start_new_topic() -> None:
    """Start a new conversation topic with context separator."""
    separator_message = {
        "role": "assistant",
        "content": "---\n\n🎯 **New Topic Started**\n\nWhat would you like to explore next? I'm here to help with course recommendations, learning paths, or any educational guidance you need!",
        "timestamp": datetime.now()
    }
    
    st.session_state.chat_messages.append(separator_message)
    st.success("🎯 New topic started!")
    st.rerun()
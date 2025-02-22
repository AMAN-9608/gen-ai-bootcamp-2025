import streamlit as st
from typing import Dict
import json
from collections import Counter
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.chat import GeminiChat
from backend.get_transcript import YouTubeTranscriptDownloader
from backend.structured_data import TranscriptStructurer
from backend.vector_store import QuestionVectorStore
from backend.question_generator import QuestionGenerator

# Page config
st.set_page_config(
    page_title="Japanese Learning Assistant",
    page_icon="🎌",
    layout="wide"
)

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'url' not in st.session_state:
    st.session_state.url = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'question_generator' not in st.session_state:
    st.session_state.question_generator = QuestionGenerator()
# if 'audio_generator' not in st.session_state:
#     st.session_state.audio_generator = AudioGenerator()
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None
if 'current_practice_type' not in st.session_state:
    st.session_state.current_practice_type = None
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None


def render_header():
    """Render the header section"""
    st.title("🎌 Japanese Learning Assistant")
    st.markdown("""
    Transform YouTube transcripts into interactive Japanese learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - Amazon Bedrock Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with Nova",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        # Stage descriptions
        stage_info = {
            "1. Chat with Nova": """
            **Current Focus:**
            - Basic Japanese learning
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - Bedrock embeddings
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        }
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage

def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with Nova")

    # Initialize BedrockChat instance if not in session state
    if 'bedrock_chat' not in st.session_state:
        pass
        # st.session_state.bedrock_chat = BedrockChat()

    # Initialize GeminiChat instance if not in session state
    if 'gemini_chat' not in st.session_state:
        st.session_state.gemini_chat = GeminiChat()

    # Introduction text
    st.markdown("""
    Start by exploring Nova's base Japanese language capabilities. Try asking questions about Japanese grammar, 
    vocabulary, or cultural aspects.
    """)

    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about Japanese language..."):
        # Process the user input
        process_message(prompt)

    # Example questions in sidebar
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "How do I say 'Where is the train station?' in Japanese?",
            "Explain the difference between は and が",
            "What's the polite form of 食べる?",
            "How do I count objects in Japanese?",
            "What's the difference between こんにちは and こんばんは?",
            "How do I ask for directions politely?"
        ]
        
        for q in example_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        # response = st.session_state.bedrock_chat.generate_response(message)
        response = st.session_state.gemini_chat.generate_response(message)
        if response:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def count_characters(text):
    """Count Japanese and total characters in text"""
    if not text:
        return 0, 0
        
    def is_japanese(char):
        return any([
            '\u4e00' <= char <= '\u9fff',  # Kanji
            '\u3040' <= char <= '\u309f',  # Hiragana
            '\u30a0' <= char <= '\u30ff',  # Katakana
        ])
    
    jp_chars = sum(1 for char in text if is_japanese(char))
    return jp_chars, len(text)

def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Japanese lesson YouTube URL"
    )
    st.session_state.url = url
    
    # Download button and processing
    if url:
        if st.button("Download Transcript"):
            try:
                downloader = YouTubeTranscriptDownloader()
                transcript = downloader.get_transcript(url)
                if transcript:
                    # Store the raw transcript text in session state
                    transcript_text = "\n".join([entry['text'] for entry in transcript])
                    st.session_state.transcript = transcript_text
                    downloader.save_transcript(transcript, downloader.extract_video_id(url))
                    st.success("Transcript downloaded successfully!")
                else:
                    st.error("No transcript found for this video.")
            except Exception as e:
                st.error(f"Error downloading transcript: {str(e)}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript,
                height=400,
                disabled=True
            )
    
        else:
            st.info("No transcript loaded yet")
    
    with col2:
        st.subheader("Transcript Stats")
        if st.session_state.transcript:
            # Calculate stats
            jp_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("Japanese Characters", jp_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    
    # Instantiate the TranscriptStructurer
    structurer = TranscriptStructurer()
    downloader = YouTubeTranscriptDownloader()

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dialogue Extraction")
        # Example of loading a transcript and extracting dialogue
        if 'url' in st.session_state and st.session_state.url:
            transcript = structurer.load_transcript(f"backend/transcripts/{downloader.extract_video_id(st.session_state.url)}.txt")  # Update the path as needed
            dialogue = structurer.structure_transcript(transcript)[2]
            conversation_tags = re.findall(r"Conversation:\s*\[(.*?)\]\s*Question", dialogue, re.DOTALL)  # Updated regex pattern
            st.session_state.transcript = transcript
            for tag in conversation_tags:
                st.info(tag)
            # st.info(dialogue)  # Display the extracted dialogue
        else:
            st.warning("No transcript found or could not load.")

    with col2:
        st.subheader("Data Structure")
        # Example of displaying structured data
        if st.session_state.transcript:
            structured_data = structurer.structure_transcript(transcript) 
            st.json(structured_data)  # Display structured data in JSON format
        else:
            st.warning("No structured data available.")

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG System")
    
    # Instantiate the QuestionVectorStore
    vector_store = QuestionVectorStore()
    
    # Query input
    query = st.text_input(
        "Test Query",
        placeholder="Enter a question about Japanese..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        
        if query:
            # Retrieve relevant context using the vector store
            retrieved_contexts = vector_store.search_similar_questions(2, query)  # Implement this method
            
            if retrieved_contexts:
                for context in retrieved_contexts:
                    st.info(context)  # Display each retrieved context
            else:
                st.warning("No relevant contexts found.")
        
    with col2:
        st.subheader("Generated Response")
        conversations = ""
        if query and retrieved_contexts:
            # Generate a response using the LLM
            for context in retrieved_contexts:
                conversation = context.get('Conversation', '')
                if conversation:  
                    conversations += conversation

            response = GeminiChat().generate_response(query+conversations)  # Implement this function
            
            if response:
                st.info(response)  # Display the generated response
            else:
                st.warning("Failed to generate a response.")
        else:
            st.info("Enter a query to generate a response.")

def render_interactive_stage():
    """Render the interactive learning stage"""
    st.header("Interactive Learning")
    
    # question_generator = QuestionGenerator()
    # Practice type selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Phrase Matching"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Practice Scenario")
        # Placeholder for scenario
        # Topic selection
        topics = {
            "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
            "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
        }
        
        topic = st.selectbox(
            "Select Topic",
            topics[practice_type]
        )

        if st.button("Generate New Question"):
            section_num = 2 if practice_type == "Dialogue Practice" else 3
            new_question = st.session_state.question_generator.generate_similar_question(
                section_num, topic
            )
            st.session_state.current_question = new_question
            st.session_state.current_practice_type = practice_type
            st.session_state.current_topic = topic
            st.session_state.feedback = None

        if st.session_state.current_question:
            st.write("**Question:**")
            st.write(st.session_state.current_question['Question'])

            if practice_type == "Dialogue Practice":
                st.write("**Introduction:**")
                st.write(st.session_state.current_question['Introduction'])
                st.write("**Conversation:**")
                st.write(st.session_state.current_question['Conversation'])
            else:
                st.write("**Situation:**")
                st.write(st.session_state.current_question['Situation'])
        
            options = st.session_state.current_question['Options']
            # If we have feedback, show which answers were correct/incorrect
            if st.session_state.feedback:
                correct = st.session_state.feedback.get('correct', False)
                # correct_answer = st.session_state.feedback.get('correct_answer', 1) - 1
                correct_answer = st.session_state.feedback.get('correct_answer', 1)
                if isinstance(correct_answer, int):
                    correct_answer -= 1
                else:
                    correct_answer = -1  # Handle missing/invalid correct_answer

                selected_index = st.session_state.selected_answer - 1 if hasattr(st.session_state, 'selected_answer') else -1
                
                st.write("\n**Your Answer:**")
                for i, option in enumerate(options):
                    if i == correct_answer and i == selected_index:
                        st.success(f"{i+1}. {option} ✓ (Correct!)")
                    elif i == correct_answer:
                        st.success(f"{i+1}. {option} ✓ (This was the correct answer)")
                    elif i == selected_index:
                        st.error(f"{i+1}. {option} ✗ (Your answer)")
                    else:
                        st.write(f"{i+1}. {option}")
                
                # Show explanation
                st.write("\n**Explanation:**")
                explanation = st.session_state.feedback.get('explanation', 'No feedback available')
                if correct:
                    st.success(explanation)
                else:
                    st.error(explanation)
                
                # Add button to try new question
                if st.button("Try Another Question"):
                    st.session_state.feedback = None
                    st.rerun()
            else:
                # Display options as radio buttons when no feedback yet
                selected = st.radio(
                    "Choose your answer:",
                    options,
                    index=None,
                    format_func=lambda x: f"{options.index(x) + 1}. {x}"
                )
                
                # Submit answer button
                if selected and st.button("Submit Answer"):
                    selected_index = options.index(selected) + 1
                    st.session_state.selected_answer = selected_index
                    st.session_state.feedback = st.session_state.question_generator.get_feedback(
                        st.session_state.current_question,
                        selected_index
                    )
                    # st.write(st.session_state.feedback)
                    st.rerun()

    with col2:
        st.subheader("Audio")
        # Placeholder for audio player
        st.info("Audio will appear here") 
        

def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with Nova":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages)
        })

if __name__ == "__main__":
    main()
import streamlit as st
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
from bson import ObjectId
import json

# Load environment variables
load_dotenv()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client.get_database("Product_Intake")
question_collection = db.aci_questionnaire
response_collection = db.questionnaire_responses

# Pydantic models for data validation
class QuestionResponse(BaseModel):
    question_id: str
    response: Any

class QuestionnaireResponse(BaseModel):
    respondent_id: str = Field(..., description="Unique identifier for the respondent")
    responses: List[QuestionResponse]
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the response")

# Initialize session state
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'respondent_id' not in st.session_state:
    st.session_state.respondent_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def get_questions() -> List[Dict[str, Any]]:
    """Fetch all questions from the database."""
    return list(question_collection.find().sort("order", 1))

def save_response(respondent_id: str, responses: Dict[str, Any]) -> str:
    """Save responses to the database."""
    response_doc = {
        "respondent_id": respondent_id,
        "responses": [{"question_id": qid, "response": resp} for qid, resp in responses.items()],
        "metadata": {
            "user_agent": st.experimental_get_query_params().get("user_agent", [""])[0],
            "ip": st.experimental_get_query_params().get("ip", [""])[0]
        },
        "submitted_at": datetime.utcnow()
    }
    
    result = response_collection.insert_one(response_doc)
    return str(result.inserted_id)

def render_question(question: Dict[str, Any]) -> Any:
    """Render the appropriate input field based on question type."""
    question_id = str(question["_id"])
    question_text = f"**{question['order']}. {question['question']}**"
    question_type = question.get("type", "text")
    
    if question.get("description"):
        question_text += f"\n*{question['description']}*"
    
    # Get current response if it exists
    current_response = st.session_state.responses.get(question_id, "")
    
    # Handle different question types
    if question_type == "boolean":
        return st.radio(
            question_text,
            options=["Yes", "No"],
            index=0 if not current_response else (1 if current_response == "Yes" else 0),
            key=f"q_{question_id}"
        )
    
    elif question_type in ["select", "multiple_choice"]:
        options = question.get("options", [])
        if not options:
            st.warning("No options provided for this question.")
            return None
        
        # Add "Other" option if needed
        if question.get("has_other") and "Other" not in options:
            options = options + ["Other"]
        
        # Use radio buttons for single select
        selected = st.radio(
            question_text,
            options=options,
            key=f"q_{question_id}"
        )
        
        # Handle "Other" option
        if selected == "Other" and question.get("has_other"):
            other_text = st.text_input(
                "Please specify:",
                key=f"{question_id}_other"
            )
            if other_text:
                return f"Other: {other_text}"
                
        return selected
        
    elif question_type == "multiselect":
        options = question.get("options", [])
        if not options:
            st.warning("No options provided for this question.")
            return []
            
        # Add "Other" option if needed
        if question.get("has_other") and "Other" not in options:
            options = options + ["Other"]
            
        # Get current selections if they exist
        current_selections = current_response if isinstance(current_response, list) else []
            
        selected = st.multiselect(
            question_text,
            options=options,
            default=current_selections,
            key=f"q_{question_id}"
        )
        
        # Handle "Other" option
        if "Other" in selected and question.get("has_other"):
            other_text = st.text_input(
                "Please specify:",
                key=f"{question_id}_other"
            )
            if other_text:
                selected = [opt for opt in selected if opt != "Other"]
                selected.append(f"Other: {other_text}")
        
        return selected
        
    elif question_type == "checkbox":
        return st.checkbox(
            question_text,
            value=bool(current_response) if current_response != "" else False,
            key=f"q_{question_id}"
        )
        
    elif question_type == "number":
        return st.number_input(
            question_text,
            value=int(current_response) if current_response != "" else 0,
            key=f"q_{question_id}"
        )
    
    # Default to text area for any other type
    return st.text_area(
        question_text,
        value=current_response,
        key=f"q_{question_id}"
    )

def main():
    st.set_page_config(
        page_title="Lab Intake Questionnaire",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main .block-container {
            max-width: 900px;
            padding: 2rem;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
        .stButton > button {
            width: 100%;
            border-radius: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Lab Intake Questionnaire")
    st.markdown("Please complete the following questions to help us understand your lab requirements.")
    
    # Get questions from database
    questions = get_questions()
    
    if not questions:
        st.error("No questions found in the database. Please check your connection.")
        return
    
    # Progress bar
    progress = (st.session_state.current_question + 1) / len(questions)
    st.progress(progress)
    st.caption(f"Question {st.session_state.current_question + 1} of {len(questions)}")
    
    # Current question
    current_q = questions[st.session_state.current_question]
    
    # Display question
    response = render_question(current_q)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("← Previous"):
                st.session_state.current_question -= 1
                st.experimental_rerun()
    
    with col2:
        if st.session_state.current_question < len(questions) - 1:
            if st.button("Next →"):
                # Save response
                question_id = str(current_q["_id"])
                st.session_state.responses[question_id] = response
                st.session_state.current_question += 1
                st.experimental_rerun()
        else:
            if st.button("Submit"):
                # Save final response
                question_id = str(current_q["_id"])
                st.session_state.responses[question_id] = response
                
                # Save all responses to database
                try:
                    response_id = save_response(
                        st.session_state.respondent_id,
                        st.session_state.responses
                    )
                    
                    st.success("Thank you for completing the questionnaire!")
                    st.balloons()
                    
                    # Show summary
                    st.subheader("Your Responses")
                    for q in questions:
                        qid = str(q["_id"])
                        if qid in st.session_state.responses:
                            st.write(f"**{q['question']}**")
                            st.write(f"*{st.session_state.responses[qid]}*")
                            st.write("---")
                    
                    # Reset for new response
                    if st.button("Start New Response"):
                        st.session_state.current_question = 0
                        st.session_state.responses = {}
                        st.session_state.respondent_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        st.experimental_rerun()
                        
                except Exception as e:
                    st.error(f"Error saving responses: {str(e)}")
    
    # Debug info (can be removed in production)
    with st.expander("Debug Info"):
        st.write("Current responses:", st.session_state.responses)
        st.write("Current question index:", st.session_state.current_question)

if __name__ == "__main__":
    main()

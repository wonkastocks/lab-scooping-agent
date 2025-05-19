import streamlit as st
from pathlib import Path

def load_questions():
    questions = []
    current_question = {}
    
    file_path = Path("questionnaire_edit_guide.txt")
    if not file_path.exists():
        return []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('# ===== QUESTION'):
            if current_question:
                questions.append(current_question)
            current_question = {}
        elif line.startswith('ORDER:'):
            current_question['order'] = int(line.split('ORDER:')[1].strip())
        elif line.startswith('TYPE:'):
            current_question['type'] = line.split('TYPE:')[1].strip()
        elif line.startswith('REQUIRED:'):
            current_question['required'] = line.split('REQUIRED:')[1].strip().lower() == 'true'
        elif line.startswith('QUESTION:'):
            current_question['question'] = line.split('QUESTION:')[1].strip()
        elif line.startswith('DESCRIPTION:'):
            desc = line.split('DESCRIPTION:')[1].strip()
            if desc and desc != '|':
                current_question['description'] = desc
        elif line.startswith('OPTIONS:'):
            current_question['options'] = []
        elif line.startswith(' - ') and 'options' in current_question:
            current_question['options'].append(line[3:].strip())
        elif line.startswith('HAS_OTHER:'):
            current_question['has_other'] = line.split('HAS_OTHER:')[1].strip().lower() == 'true'
    
    if current_question:
        questions.append(current_question)
    
    return questions

def main():
    st.set_page_config(
        page_title="Lab Setup Questionnaire",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for compact layout
    st.markdown("""
    <style>
        .main .block-container {
            padding: 0.5rem 1rem !important;
            max-width: 900px !important;
        }
        .stTextInput, .stTextArea, .stNumberInput, .stRadio, .stMultiSelect, .stSelectbox {
            margin: 0.1rem 0 0.3rem 0 !important;
        }
        h1 {
            font-size: 1.5rem !important;
            margin: 0.5rem 0 0.5rem 0 !important;
        }
        h3 {
            font-size: 1rem !important;
            margin: 0.1rem 0 0.1rem 0 !important;
        }
        .stMarkdown {
            margin: 0 !important;
        }
        .stTextArea textarea {
            min-height: 50px !important;
            max-height: 100px !important;
        }
        .stButton>button {
            width: 100% !important;
            margin: 0.5rem 0 1rem 0 !important;
        }
        .stForm {
            margin-top: 0.5rem !important;
        }
        .stForm form {
            padding: 0.5rem 0 !important;
        }
        .stRadio > div {
            gap: 0.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Lab Setup Questionnaire")
    
    # Load questions
    questions = load_questions()
    
    if not questions:
        st.warning("No questions found. Please check the questionnaire file.")
        return
    
    # Sort questions by order
    questions = sorted(questions, key=lambda x: x.get('order', 0))
    
    # Initialize session state
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    
    if not st.session_state.submitted:
        with st.form("questionnaire_form"):
            for i, q in enumerate(questions):
                with st.container():
                    # Question text
                    question_text = q.get('question', '')
                    required = q.get('required', False)
                    
                    # Display question with required indicator
                    st.markdown(f"**{question_text}**" + (" *" if required else ""), unsafe_allow_html=True)
                    
                    # Description if exists
                    if 'description' in q and q['description']:
                        st.caption(q['description'])
                    
                    # Handle different question types
                    q_type = q.get('type', 'text')
                    q_key = f"q_{i}"
                    
                    # Initialize response in session state if not exists
                    if q_key not in st.session_state.responses:
                        st.session_state.responses[q_key] = "" if q_type != 'multiselect' else []
                    
                    # Debug: Print question info
                    # st.write(f"Question {i+1}:", q)
                    
                    # Render input field based on type
                    if q_type == 'text':
                        response = st.text_input(
                            "", 
                            key=f"input_{q_key}",
                            value=st.session_state.responses.get(q_key, ""),
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response
                        
                    elif q_type == 'textarea':
                        response = st.text_area(
                            "", 
                            key=f"input_{q_key}",
                            value=st.session_state.responses.get(q_key, ""),
                            height=60,
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response
                        
                    elif q_type == 'number':
                        response = st.number_input(
                            "",
                            key=f"input_{q_key}",
                            value=int(st.session_state.responses.get(q_key, 0) or 0),
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response
                        
                    elif q_type == 'boolean':
                        response = st.radio(
                            "",
                            ["Yes", "No"],
                            key=f"input_{q_key}",
                            index=0 if st.session_state.responses.get(q_key) == "Yes" else 1,
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response == "Yes"
                        
                    elif q_type == 'select':
                        options = q.get('options', []).copy()  # Make a copy to avoid modifying the original
                        has_other = q.get('has_other', False)
                        
                        if has_other:
                            options.append("Other (please specify)")
                        
                        response = st.radio(
                            "",
                            options,
                            key=f"input_{q_key}",
                            index=0 if not st.session_state.responses.get(q_key) else options.index(st.session_state.responses.get(q_key, '')),
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response
                        
                        if has_other and response == "Other (please specify)":
                            other_key = f"{q_key}_other"
                            other_response = st.text_input(
                                "Please specify:", 
                                key=f"input_{other_key}",
                                value=st.session_state.responses.get(other_key, "")
                            )
                            st.session_state.responses[other_key] = other_response
                            
                    elif q_type == 'multiselect':
                        options = q.get('options', []).copy()  # Make a copy to avoid modifying the original
                        has_other = q.get('has_other', False)
                        
                        if has_other:
                            options.append("Other (please specify)")
                        
                        # Get current response, ensuring it's a list
                        current_response = st.session_state.responses.get(q_key, [])
                        if not isinstance(current_response, list):
                            current_response = [current_response] if current_response else []
                        
                        response = st.multiselect(
                            "",
                            options,
                            key=f"input_{q_key}",
                            default=current_response,
                            label_visibility="collapsed"
                        )
                        st.session_state.responses[q_key] = response
                        
                        if has_other and "Other (please specify)" in response:
                            other_key = f"{q_key}_other"
                            other_response = st.text_input(
                                "Please specify:", 
                                key=f"input_{other_key}",
                                value=st.session_state.responses.get(other_key, "")
                            )
                            st.session_state.responses[other_key] = other_response
                
                # Add a small space between questions
                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
            
            # Add some space before the submit button
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            
            # Create a container for the submit button at the bottom
            _, col, _ = st.columns([1, 2, 1])
            with col:
                submitted = st.form_submit_button("SUBMIT QUESTIONNAIRE", 
                                               type="primary",
                                               use_container_width=True)
            
            if submitted:
                # Validate required fields
                missing = []
                for i, q in enumerate(questions):
                    if q.get('required', False):
                        q_key = f"q_{i}"
                        response = st.session_state.responses.get(q_key)
                        if not response or (isinstance(response, (list, dict)) and not response):
                            missing.append(q.get('question', f"Question {i+1}"))
                
                if missing:
                    st.error(f"Please fill in all required fields: {', '.join(missing)}")
                    st.rerun()
                else:
                    st.session_state.submitted = True
                    st.rerun()
    else:
        st.success("✅ Thank you for completing the questionnaire!")
        
        if st.button("Edit Responses"):
            st.session_state.submitted = False
            st.rerun()

if __name__ == "__main__":
    main()

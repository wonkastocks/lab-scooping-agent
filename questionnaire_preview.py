import streamlit as st
import json
from pathlib import Path

# Load questions from the text file
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
        elif line.startswith('DESCRIPTION:') and '|' not in line:  # Simple description
            desc = line.split('DESCRIPTION:')[1].strip()
            if desc:  # Only add if not empty
                current_question['description'] = desc
        elif line.startswith('OPTIONS:'):
            current_question['options'] = []
        elif line.startswith(' - ') and 'options' in current_question:
            current_question['options'].append(line[3:].strip())
        elif line.startswith('HAS_OTHER:'):
            current_question['has_other'] = line.split('HAS_OTHER:')[1].strip().lower() == 'true'
    
    if current_question:  # Add the last question
        questions.append(current_question)
    
    return questions


def main():
    st.set_page_config(layout="centered")
    questions = load_questions()
    st.title("Questionnaire Preview")
    st.write("Please answer the following questions:")

    with st.form("questionnaire"):
        for i, q in enumerate(questions):
            q_key = f"q_{i}"
            if q['type'] == 'text':
                st.text_input(q['question'], key=q_key)
            elif q['type'] == 'selectbox':
                st.selectbox(q['question'], q['options'], key=q_key)
            elif q['type'] == 'multiselect':
                st.multiselect(q['question'], q['options'], key=q_key)
            elif q['type'] == 'checkbox':
                st.checkbox(q['question'], key=q_key)
            if q.get('description'):
                st.write(q['description'])
            if q.get('has_other', False):
                st.write("Other (please specify):")
                st.text_input("", key=f"{q_key}_other")

        # Submit button
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Validate required fields
            missing = []
            for i, q in enumerate(questions):
                if q.get('required', False):
                    q_key = f"q_{i}"
                    if not st.session_state.get(q_key, False):
                        missing.append(q.get('question', f"Question {i+1}"))
            
            if missing:
                st.error(f"Please fill in all required fields: {', '.join(missing)}")
            else:
                # Save responses (in a real app, you'd save to a database)
                st.session_state.submitted = True
                st.rerun()
    
    # Show success message after submission
    if st.session_state.get('submitted', False):
        st.success("Thank you for completing the questionnaire!")
        
        if st.button("View Responses"):
            st.json(st.session_state)
        
        if st.button("Submit Another Response"):
            st.session_state.submitted = False
            st.session_state.responses = {}
            st.rerun()

if __name__ == "__main__":
    main()

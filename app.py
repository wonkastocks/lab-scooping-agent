import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import time
import json

def load_assistant_info():
    """Load assistant information from the saved file"""
    try:
        with open('assistant_info.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'assistant_id': 'asst_6jOyAqWW9jQxHFgJfSGOze8c',
            'vector_store_id': 'vs_682b3d34985c819181e0468d38c5001e'
        }

def convert_to_text(messages):
    """Convert chat messages to plain text format"""
    text = ""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text += f"Lab Intake Assistant\n"
    text += f"Conversation Export ({current_time})\n\n"
    
    for msg in messages:
        role = msg["role"].title()
        content = msg["content"]
        
        if role == "User":
            text += f"Question:\n{content}\n\n"
        else:
            text += f"Answer:\n{content}\n\n"
    return text

# Callback to initiate processing
def start_download_processing():
    st.session_state.download_stage = 'processing'

# Function to reset download state
def reset_download_state():
    st.session_state.download_stage = 'initial'
    st.session_state.text_to_download = None

# Load environment variables
load_dotenv(override=True)

# Ensure your OpenAI key is available from .env file
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Load assistant information
assistant_info = load_assistant_info()
ASSISTANT_ID = assistant_info.get('assistant_id', 'asst_6jOyAqWW9jQxHFgJfSGOze8c')
VECTOR_STORE_ID = assistant_info.get('vector_store_id', 'vs_682b3d34985c819181e0468d38c5001e')

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "text_to_download" not in st.session_state:
    st.session_state.text_to_download = None
if "download_stage" not in st.session_state:  # 'initial', 'processing', 'ready_to_download'
    st.session_state.download_stage = 'initial'

# Streamlit UI
st.set_page_config(
    page_title="Lab Intake Assistant",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.title(" Lab Intake Assistant")
st.write("Get help with lab intake documentation and requirements.")

# Sidebar controls
st.sidebar.title("Settings")

# Clear conversation button
st.sidebar.subheader("Conversation Controls")
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.session_state.thread_id = None
    reset_download_state()  # Reset download stage
    st.rerun()

# Simplified Download Process
st.sidebar.subheader("Download Conversation")

# Stateful Download UI
if st.session_state.download_stage == 'initial':
    initial_button_disabled = not st.session_state.get("messages", [])
    st.sidebar.button(
        "Process & Download Chat (TXT)",
        on_click=start_download_processing,
        disabled=initial_button_disabled,
        key="initiate_download_process_btn"
    )
elif st.session_state.download_stage == 'processing':
    st.sidebar.info("Processing conversation... please wait.")
    # Perform the actual processing and delay here
    current_messages = st.session_state.get("messages", [])
    if current_messages:
        generated_text = convert_to_text(current_messages)
        st.session_state.text_to_download = generated_text
        time.sleep(5) # The 5-second delay
        st.session_state.download_stage = 'ready_to_download'
    else:
        # Should not happen if button was enabled, but as a fallback
        reset_download_state()
    st.rerun() # Force rerun to show the download button or revert

elif st.session_state.download_stage == 'ready_to_download':
    if st.session_state.get("text_to_download"):
        st.sidebar.download_button(
            label="Click Here to Download TXT",
            data=st.session_state.text_to_download,
            file_name="conversation_export.txt",
            mime="text/plain",
            key="final_download_action_btn",
            on_click=reset_download_state # Reset state after download click
        )
    else:
        # If somehow no text to download, revert to initial state
        st.sidebar.warning("No data to download. Please try again.")
        reset_download_state()
        st.rerun()

# Example questions
with st.sidebar.expander("Example Questions"):
    example_questions = [
        "What are the requirements for the ACI lab?",
        "What virtualization platforms are supported?",
        "List the networking requirements for the lab",
        "What are the common terms used in the lab documentation?",
        "What are the prerequisites for the InfoSec lab?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"example_{question}"):
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()

def create_thread():
    """Create a new conversation thread"""
    thread = client.beta.threads.create()
    return thread.id

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about lab requirements..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Create a new thread if one doesn't exist
    if not st.session_state.thread_id:
        st.session_state.thread_id = create_thread()
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )
        
        # Create a run with the assistant
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            instructions="You are a helpful lab intake assistant. Provide detailed, accurate information based on the provided documentation."
        )
        
        # Poll for the run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                full_response = "Sorry, I encountered an error processing your request. Please try again."
                break
            
            # Small delay to avoid hitting rate limits
            time.sleep(0.5)
        
        # Get the assistant's response
        if run_status.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            
            # Get the latest assistant message
            for message in messages.data:
                if message.role == 'assistant':
                    # Get the text value of the message
                    for content in message.content:
                        if content.type == 'text':
                            full_response = content.text.value
                            break
                    break
        
        # Display the response
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Rerun to update the UI
    st.rerun()
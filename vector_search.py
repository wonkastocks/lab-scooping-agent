import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="Document Search",
    page_icon="🔍",
    layout="centered"
)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found in .env file")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Get vector store ID from environment variables
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# Function to search vector store
def search_vector_store(query, limit=5):
    try:
        if not VECTOR_STORE_ID:
            return [{
                'id': 'no_vector_store',
                'filename': 'Error',
                'content': 'Vector store ID not found in .env file',
                'score': 0
            }]
        
        # Create an assistant with file search capability
        assistant = client.beta.assistants.create(
            name="Comprehensive Document Searcher",
            instructions="""Return ALL relevant search results from the documents. For each result:
            1. Include the full text of the matching content
            2. Separate each result with two newlines
            3. Do not summarize or combine results
            4. Include as many results as match the query
            """,
            model="gpt-4-turbo-preview",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            }
        )
        
        # Create a thread with the vector store
        thread = client.beta.threads.create(
            tool_resources={
                "file_search": {
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            }
        )
        
        # Add the user's message
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Add the user's message
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # First, create the run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            max_completion_tokens=4000,
            tool_choice={"type": "file_search"}
        )
        
        # Then poll for completion
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        
        # Wait for the run to complete
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        # Get the messages
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            order="asc"  # Get messages in chronological order
        )
        
        # Process the results
        results = []
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if content.type == "text":
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            # Split the response into individual results
                            result_texts = content.text.value.split('\n\n')
                            for i, text in enumerate(result_texts):
                                if text.strip():
                                    results.append({
                                        'id': f"{msg.id}_{i}",
                                        'filename': f"Result {len(results) + 1}",
                                        'content': text.strip(),
                                        'score': 1.0 - (i * 0.01)  # Slight score variation for sorting
                                    })
        
        # Clean up
        try:
            client.beta.assistants.delete(assistant.id)
            client.beta.threads.delete(thread.id)
        except:
            pass
            
        # Return unique results by content to avoid duplicates
        seen = set()
        unique_results = []
        for result in results:
            if result['content'] not in seen:
                seen.add(result['content'])
                unique_results.append(result)
        
        # Sort by score in descending order and limit results
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        return unique_results[:limit] if unique_results else [{
            'id': 'no_results',
            'filename': 'No Results',
            'content': 'No relevant information found in the documents.',
            'score': 0
        }]
        
    except Exception as e:
        st.error(f"Error searching vector store: {str(e)}")
        return []

# Function to get file content (not used in current implementation)
def get_file_content(file_id):
    try:
        # We can't directly download assistant files, so we'll return a placeholder
        return "[File content not directly accessible. Using assistant API for search.]"
    except Exception as e:
        st.error(f"Error getting file content: {str(e)}")
        return ""

# UI
# Add custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .stTextInput input {
        font-size: 1.1rem;
        padding: 0.75rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
        padding: 0.75rem;
        font-size: 1.1rem;
    }
    .document-list {
        margin: 2rem 0;
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔍 Document Search")
st.markdown("Search through your documents using natural language.")

# List of searchable documents
with st.container():
    st.markdown("### Available Documents")
    docs = [
        "ACI Learning Documentation",
        "Infosec Learning Materials",
        "Lab Intake Workflow",
        "Training Program Overview",
        "Technical Documentation"
    ]
    
    cols = st.columns(2)
    for i, doc in enumerate(docs):
        with cols[i % 2]:
            st.markdown(f"- {doc}")
    
    st.markdown("---")

# Search form
with st.form("search_form"):
    query = st.text_area(
        "Enter your search query:",
        placeholder="Search for information in your documents...",
        height=100,
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        limit = st.slider("Max results:", 1, 20, 5, 1)
    with col2:
        st.markdown("<div style='height: 27px; display: flex; align-items: center;'><div>Search options</div></div>", unsafe_allow_html=True)
        search_button = st.form_submit_button("Search")

# Handle search
if search_button and query:
    with st.spinner("Searching through documents..."):
        st.session_state.search_results = search_vector_store(query, limit=limit)

# Display results
if st.session_state.search_results:
    st.markdown(f"### Found {len(st.session_state.search_results)} result(s)")
    
    for i, result in enumerate(st.session_state.search_results):
        # Display result directly without expander
        st.markdown(f"#### Result {i+1}")
        st.markdown(result['content'])
        
        # Add a download button for the content
        st.download_button(
            label=f"Download Result {i+1}",
            data=result['content'],
            file_name=f"search_result_{i+1}.txt",
            mime="text/plain",
            key=f"download_{i}",
            use_container_width=True
        )
        
        # Add a divider between results
        if i < len(st.session_state.search_results) - 1:
            st.markdown("---")

# Add some custom CSS
st.markdown("""
<style>
    .stTextArea [data-baseweb=base-input] {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stExpander {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

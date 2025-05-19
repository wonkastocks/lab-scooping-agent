import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Lab Database Chat",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .user-message {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .assistant-message {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Connect to MongoDB
def get_db():
    try:
        connection_string = os.getenv("MONGODB_URI")
        if not connection_string:
            st.error("MongoDB connection string not found in .env file")
            st.stop()
        
        client = MongoClient(connection_string)
        client.admin.command('ping')  # Test connection
        return client.get_database("Product_Intake")
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()

def get_questionnaire_questions(db):
    """Get all questionnaire questions from the database"""
    return list(db.questionnaire_questions.find().sort("order", 1))

def get_labs_count(db):
    """Get total number of labs"""
    return db.labs.count_documents({})

def get_categories(db):
    """Get all unique categories"""
    return db.labs.distinct("categories")

def search_labs(db, query: str, limit: int = 5):
    """Search for labs matching the query"""
    return list(db.labs.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit))

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I can help you explore the lab database. Ask me anything about the labs, categories, or questionnaire questions."}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about the lab database..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get database connection
    db = get_db()
    
    # Process the query
    response = ""
    
    # Check for common queries
    if "questionnaire" in prompt.lower() or "questions" in prompt.lower():
        questions = get_questionnaire_questions(db)
        response = "## Questionnaire Questions\n\n"
        for i, q in enumerate(questions, 1):
            response += f"{i}. {q.get('question', '')}\n"
            if 'options' in q and q['options']:
                response += "   Options: " + ", ".join(q['options']) + "\n"
    
    elif "how many labs" in prompt.lower() or "total labs" in prompt.lower():
        count = get_labs_count(db)
        response = f"There are {count} labs in the database."
    
    elif "categories" in prompt.lower() or "types of labs" in prompt.lower():
        categories = get_categories(db)
        response = "## Lab Categories\n\n" + "\n".join(f"- {cat}" for cat in sorted(categories))
    
    elif "search" in prompt.lower() or "find labs" in prompt.lower():
        # Extract search terms from the query
        search_terms = prompt.lower().replace("search", "").replace("find", "").replace("labs", "").strip()
        if search_terms:
            labs = search_labs(db, search_terms)
            if labs:
                response = "## Matching Labs\n\n"
                for lab in labs:
                    response += f"### {lab.get('title', 'Untitled')}\n"
                    response += f"Type: {lab.get('content_type', 'N/A')}\n"
                    response += f"Categories: {', '.join(lab.get('categories', ['None']))}\n\n"
            else:
                response = "No matching labs found. Try different search terms."
        else:
            response = "Please specify what you're looking for. For example: 'Search for security labs'"
    
    else:
        response = """I can help you with:
        - Listing all questionnaire questions
        - Showing the total number of labs
        - Listing all lab categories
        - Searching for specific labs
        
        Try asking something like:
        - 'Show me all questionnaire questions'
        - 'How many labs are there?'
        - 'List all lab categories'
        - 'Search for security labs'"""
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# Add some helpful buttons
st.sidebar.markdown("### Quick Actions")
if st.sidebar.button("Show Questionnaire Questions"):
    db = get_db()
    questions = get_questionnaire_questions(db)
    response = "## Questionnaire Questions\n\n"
    for i, q in enumerate(questions, 1):
        response += f"{i}. {q.get('question', '')}\n"
        if 'options' in q and q['options']:
            response += "   Options: " + ", ".join(q['options']) + "\n\n"
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

if st.sidebar.button("Show Lab Count"):
    db = get_db()
    count = get_labs_count(db)
    st.session_state.messages.append({"role": "assistant", "content": f"There are {count} labs in the database."})
    st.rerun()

if st.sidebar.button("Show Categories"):
    db = get_db()
    categories = get_categories(db)
    response = "## Lab Categories\n\n" + "\n".join(f"- {cat}" for cat in sorted(categories))
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Add a clear chat button
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = [
        {"role": "assistant", "content": "Chat cleared. How can I help you with the lab database?"}
    ]
    st.rerun()

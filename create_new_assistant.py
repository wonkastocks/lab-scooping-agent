import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_assistant_with_files():
    """Create a new assistant with the specified files."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # File IDs to include (from previous cleanup)
    file_ids = [
        'file-Q5XKs6ohkKSmn7cJX7rrKG',  # Common-Terms.md
        'file-Xw1FQAcrjQZDXFWnWWibDV',  # ACILEARNING.md
        'file-3oE39dubfLPVxYBpVeWjaz',  # Infoseclearning.md
        'file-2oUFfeV69xcxveGcE3WeXU',  # rag_questionnaire.md
        'file-CwGJWeDaJtcPdeVBhftyHp',  # rag_vmware_virtualization.md
        'file-6vkpHnRfEJGQPvfZyD4T1Q',  # rag_linux_windows_networking.md
        'file-KHCYvyWXcfFM8KwG5hLpsE',  # rag_terms_glossary.md
        'file-52cw2UCSKBdkeZPDpynq58'   # aci_lab_questionnaire_full.md
    ]
    
    # Instructions for the assistant
    instructions = """
    You are an assistant that helps with lab intake documentation. 
    You have access to various lab-related documents including requirements, 
    questionnaires, and technical specifications.
    
    Provide detailed, accurate information based on the documentation.
    """
    
    # Create the assistant
    url = "https://api.openai.com/v1/assistants"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "assistants=v2"  # Use the latest API version
    }
    
    # First create a vector store with the files
    print("Creating vector store...")
    vector_store = requests.post(
        "https://api.openai.com/v1/vector_stores",
        headers=headers,
        json={
            "name": "Lab Intake Documents",
            "file_ids": file_ids
        }
    ).json()
    
    if "error" in vector_store:
        print(f"Error creating vector store: {vector_store['error']['message']}")
        return
    
    vector_store_id = vector_store["id"]
    print(f"Created vector store: {vector_store_id}")
    
    # Now create the assistant with the vector store
    print("Creating assistant...")
    assistant_data = {
        "name": "Lab Intake Assistant (Updated)",
        "instructions": instructions,
        "tools": [{"type": "file_search"}],
        "tool_resources": {
            "file_search": {
                "vector_store_ids": [vector_store_id]
            }
        },
        "model": "gpt-4-turbo-preview"
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=assistant_data
    )
    
    if response.status_code == 200:
        assistant = response.json()
        print(f"✅ Assistant created successfully!")
        print(f"Assistant ID: {assistant['id']}")
        print(f"Vector Store ID: {vector_store_id}")
        
        # Save the IDs to a file
        with open('assistant_info.json', 'w') as f:
            json.dump({
                'assistant_id': assistant['id'],
                'vector_store_id': vector_store_id,
                'file_ids': file_ids
            }, f, indent=2)
        
        print("\n✅ Assistant information saved to 'assistant_info.json'")
    else:
        print(f"❌ Error creating assistant: {response.text}")

if __name__ == "__main__":
    print("=== Create New Lab Intake Assistant ===")
    create_assistant_with_files()
    
    print("\n=== NEXT STEPS ===")
    print("1. Test the new assistant in the OpenAI Playground")
    print("2. Update any code that references the old assistant ID")

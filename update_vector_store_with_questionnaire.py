import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pymongo import MongoClient
from pathlib import Path
from typing import List, Dict, Any
import tempfile

# Load environment variables
load_dotenv()

# Initialize clients
client = OpenAI()
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client.get_database("Product_Intake")

def get_questionnaire_data() -> List[Dict[str, Any]]:
    """Retrieve questionnaire data from MongoDB."""
    questions = list(db.aci_questionnaire.find().sort("order", 1))
    return questions

def format_question_for_embedding(question: Dict[str, Any]) -> Dict[str, str]:
    """Format a single question for embedding."""
    formatted = {
        "question_id": str(question["_id"]),
        "order": question["order"],
        "question": question["question"],
        "type": question["type"],
        "options": ", ".join(question.get("options", [])) or "N/A"
    }
    return formatted

def create_temporary_file(questions: List[Dict[str, Any]]) -> Path:
    """Create a temporary file with the questionnaire data."""
    # Format questions for embedding
    formatted_questions = [format_question_for_embedding(q) for q in questions]
    
    # Create a temporary file with .txt extension
    temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8')
    
    # Write formatted text (one question per line with options)
    for q in formatted_questions:
        temp_file.write(f"Question {q['order']}: {q['question']}\n")
        if q['options'] != "N/A":
            temp_file.write(f"Options: {q['options']}\n")
        temp_file.write("\n" + "-" * 50 + "\n\n")
    
    temp_file.close()
    return Path(temp_file.name)

def upload_to_vector_store(file_path: Path) -> str:
    """Upload the file to OpenAI's vector store."""
    try:
        # Upload the file
        with open(file_path, "rb") as f:
            file = client.files.create(file=f, purpose="assistants")
        
        print(f"✅ File uploaded with ID: {file.id}")
        
        # Create an assistant with file search capability
        print("Creating assistant with file search capability...")
        
        assistant = client.beta.assistants.create(
            name="Lab Intake Questionnaire Assistant",
            instructions="""You are a helpful assistant that provides information about the lab intake questionnaire.
            Use the provided file to answer questions about the questionnaire structure and content.
            
            When providing information, be clear and specific about which question you're referring to.
            """,
            tools=[{"type": "file_search"}],
            model="gpt-4-turbo-preview"
        )
        
        print(f"✅ Assistant created with ID: {assistant.id}")
        
        # Save the assistant and file IDs
        ids_file = Path("vector_store_ids.json")
        if ids_file.exists():
            with open(ids_file, 'r') as f:
                ids = json.load(f)
        else:
            ids = {}
        
        ids['questionnaire'] = {
            'assistant_id': assistant.id,
            'file_id': file.id,
            'description': 'Lab intake questionnaire with questions and options',
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(ids_file, 'w') as f:
            json.dump(ids, f, indent=2)
        
        print(f"✅ Configuration saved to {ids_file}")
        return assistant.id
        
    except Exception as e:
        print(f"❌ Error updating vector store: {e}")
        raise

def main():
    print("🚀 Starting vector store update with questionnaire data...")
    
    try:
        # 1. Get questionnaire data from MongoDB
        print("\n📋 Retrieving questionnaire data from MongoDB...")
        questions = get_questionnaire_data()
        print(f"✅ Retrieved {len(questions)} questions")
        
        # 2. Create temporary file with formatted data
        print("\n📄 Creating temporary file with formatted data...")
        temp_file = create_temporary_file(questions)
        print(f"✅ Temporary file created at: {temp_file}")
        
        # 3. Upload to vector store
        print("\n⬆️  Uploading to vector store...")
        vector_store_id = upload_to_vector_store(temp_file)
        
        print(f"\n🎉 Success! Vector store updated with questionnaire data.")
        print(f"   Vector Store ID: {vector_store_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary file
        if 'temp_file' in locals() and temp_file.exists():
            try:
                temp_file.unlink()
                print(f"\n🧹 Cleaned up temporary file: {temp_file}")
            except Exception as e:
                print(f"\n⚠️  Warning: Could not remove temporary file: {e}")

if __name__ == "__main__":
    main()

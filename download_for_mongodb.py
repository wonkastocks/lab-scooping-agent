import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create MONGO_DB_FILES directory if it doesn't exist
MONGO_DB_FILES = Path("MONGO_DB_FILES")
MONGO_DB_FILES.mkdir(exist_ok=True)

def download_file(file_id: str, file_name: str) -> Optional[Path]:
    """Download a file from OpenAI and save it to the MONGO_DB_FILES directory"""
    try:
        # Get the file content
        file_content = client.files.content(file_id)
        
        # Ensure the file has a proper extension
        if not any(file_name.lower().endswith(ext) for ext in ['.txt', '.md', '.json', '.pdf', '.docx']):
            file_name += '.txt'
            
        # Save the file
        file_path = MONGO_DB_FILES / file_name
        
        # Ensure unique filename
        counter = 1
        original_name = file_path.stem
        while file_path.exists():
            file_path = MONGO_DB_FILES / f"{original_name}_{counter}{file_path.suffix}"
            counter += 1
            
        file_path.write_bytes(file_content.content)
        print(f"Downloaded: {file_name} -> {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading file {file_id}: {str(e)}")
        return None

def create_mongodb_document(file_path: Path, file_info: Any) -> Dict[str, Any]:
    """Create a MongoDB document for the file"""
    try:
        # Read file content if it's a text file
        if file_path.suffix.lower() in ['.txt', '.md', '.json', '.csv']:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        else:
            content = "[BINARY FILE]"
            
        return {
            "_id": file_info.id,  # Using file_id as the _id for MongoDB
            "filename": file_path.name,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "created_at": file_info.created_at,
            "local_path": str(file_path.relative_to(Path.cwd())),
            "size_bytes": file_path.stat().st_size,
            "content": content if len(content) < 1000000 else "[CONTENT TOO LARGE]"
        }
    except Exception as e:
        print(f"Error creating document for {file_path}: {str(e)}")
        return {}

def main():
    print("Fetching assistant information...")
    
    # Load assistant information
    assistant_id = 'asst_6jOyAqWW9jQxHFgJfSGOze8c'
    
    try:
        # Get the assistant
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"Assistant: {assistant.id} - {assistant.name}")
        
        # Get all files associated with the assistant
        files = client.files.list()
        print(f"Found {len(files.data)} files in total")
        
        # Filter files that are likely part of the assistant's knowledge
        assistant_files = [f for f in files.data if f.purpose in ['assistants', 'assistants_output']]
        print(f"Found {len(assistant_files)} files associated with the assistant")
        
        # Download and process each file
        documents = []
        for file_info in assistant_files:
            try:
                print(f"\nProcessing: {file_info.filename} ({file_info.id})")
                
                # Download the file
                saved_path = download_file(file_info.id, file_info.filename)
                if saved_path:
                    # Create MongoDB document
                    doc = create_mongodb_document(Path(saved_path), file_info)
                    if doc:  # Only add if document was created successfully
                        documents.append(doc)
                        print(f"Added to MongoDB documents")
            except Exception as e:
                print(f"Error processing file {file_info.id}: {str(e)}")
        
        if documents:
            # Create a timestamp for the output file
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save documents to a JSON file for MongoDB import
            output_file = MONGO_DB_FILES / f"lab_intake_documents_{timestamp}.json"
            
            # Save as a JSON array
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, default=str)
            
            # Also save individual JSON files for each document
            for i, doc in enumerate(documents):
                doc_file = MONGO_DB_FILES / f"doc_{i+1:03d}_{doc['_id']}.json"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    json.dump(doc, f, indent=2, default=str)
            
            print(f"\n✅ Successfully processed {len(documents)} files.")
            print(f"📄 MongoDB documents saved to: {output_file}")
            print("\nTo import into MongoDB, you can use:")
            print(f"mongoimport --db lab_intake --collection documents --file {output_file} --jsonArray")
            print("\nOr for individual files:")
            print(f"for f in MONGO_DB_FILES/doc_*.json; do mongoimport --db lab_intake --collection documents --file $f; done")
        else:
            print("\n❌ No documents were processed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

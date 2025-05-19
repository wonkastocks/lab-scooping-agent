import os
import json
import asyncio
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import time

def convert_jsonl_to_txt(jsonl_file: Path) -> Path:
    """Convert a JSONL file to a text file for upload."""
    # Read the JSONL file
    data = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    
    # Create a temporary file for the text
    temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8')
    temp_file_path = Path(temp_file.name)
    
    # Save as formatted text
    for item in data:
        # Format each item as key-value pairs
        for key, value in item.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                temp_file.write(f"{key}:\n")
                for k, v in value.items():
                    temp_file.write(f"  {k}: {v}\n")
            else:
                temp_file.write(f"{key}: {value}\n")
        temp_file.write("\n---\n\n")
    
    temp_file.close()
    return temp_file_path

def upload_to_vector_store():
    """Upload the processed data to OpenAI's vector store."""
    # Load environment variables
    load_dotenv()
    
    # Initialize the OpenAI client
    client = OpenAI()
    
    try:
        # Find the most recent vector file
        output_dir = Path("output")
        vector_files = list(output_dir.glob("openai_vectors_*.jsonl"))
        if not vector_files:
            print("No vector files found in the output directory.")
            return
            
        latest_file = max(vector_files, key=lambda x: x.stat().st_mtime)
        print(f"Found vector file: {latest_file}")
        
        # Convert JSONL to TXT
        print("Converting JSONL to TXT...")
        txt_file = convert_jsonl_to_txt(latest_file)
        print(f"Temporary TXT file created at: {txt_file}")
        
        try:
            # Upload the file to OpenAI
            print("Uploading file to OpenAI...")
            with open(txt_file, "rb") as f:
                file = client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            print(f"File uploaded with ID: {file.id}")
            print(f"Description: Combined data from source files:")
            print(f"- Constellation Lab Tracker(Conversion Tracker) (2).csv")
            print(f"- infosec_learning-content_export-2025-05-19t07-07-04.csv")
            
            # Create the assistant with file search capability
            print("Creating assistant with file search capability...")
            
            # Create the assistant with file search capability
            assistant = client.beta.assistants.create(
                name="Lab and Course Assistant",
                instructions="""You are a helpful assistant that provides information about labs and courses. 
                You have access to a knowledge base of lab instructions, course materials, and related information.
                Use this information to answer questions about labs, courses, and related topics.

                When providing information, please include which source file the information came from.

                Source files:
                - Constellation Lab Tracker(Conversion Tracker) (2).csv: Contains lab information including lab IDs, names, VM requirements, and internet requirements
                - infosec_learning-content_export-2025-05-19t07-07-04.csv: Contains course information including titles, content types, and status""",
                tools=[{"type": "file_search"}],
                model="gpt-4-1106-preview"
            )
            
            print(f"Assistant created with ID: {assistant.id}")
            
            # Create a thread
            print("Creating a thread...")
            thread = client.beta.threads.create()
            
            # Create a message with the file attachment
            print("Creating a message with file attachment...")
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content="Please analyze the attached lab and course data. When providing information, always mention which source file it came from.",
                attachments=[
                    {
                        "file_id": file.id,
                        "tools": [{"type": "file_search"}]
                    }
                ]
            )
            
            print(f"Thread created with ID: {thread.id}")
            print(f"Message with file attachment created with ID: {message.id}")
            
            # Save the IDs and metadata for future reference
            ids = {
                "file_id": file.id,
                "assistant_id": assistant.id,
                "thread_id": thread.id,
                "message_id": message.id,
                "original_files": [
                    "Constellation Lab Tracker(Conversion Tracker) (2).csv",
                    "infosec_learning-content_export-2025-05-19t07-07-04.csv"
                ],
                "uploaded_file": file.filename,
                "model": "gpt-4-1106-preview",
                "timestamp": pd.Timestamp.now().isoformat(),
                "tools": ["file_search"],
                "description": "Combined lab and course data from source files"
            }
            
            # Save the IDs to a file
            with open("vector_store_ids.json", "w") as f:
                json.dump(ids, f, indent=2)
                
            print("\nIDs saved to vector_store_ids.json")
            print("\nYou can now use the assistant with the following ID:", assistant.id)
            
        except Exception as e:
            print(f"Error: {e}")
            print(f"\nFull error:")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up the temporary file
            if 'txt_file' in locals():
                try:
                    os.unlink(txt_file)
                    print(f"Temporary file {txt_file} removed")
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {txt_file}: {e}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print("\nFull error:")
        print(traceback.format_exc())

if __name__ == "__main__":
    upload_to_vector_store()

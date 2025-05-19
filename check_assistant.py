import os
import json
from openai import OpenAI
from dotenv import load_dotenv

def check_assistant():
    # Load environment variables
    load_dotenv()
    
    # Initialize the client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Load the saved IDs
    try:
        with open("vector_store_ids.json", "r") as f:
            ids = json.load(f)
        
        assistant_id = ids["assistant_id"]
        file_id = ids["file_id"]
        
        print(f"Checking assistant: {assistant_id}")
        
        # Get the assistant details
        assistant = client.beta.assistants.retrieve(assistant_id)
        print("\nAssistant details:")
        print(f"Name: {assistant.name}")
        print(f"Model: {assistant.model}")
        print(f"Instructions: {assistant.instructions}")
        print("Tools:", [tool.type for tool in assistant.tools])
        
        # Check if the file is attached to the assistant
        print("\nFiles attached to assistant:")
        if hasattr(assistant, 'file_ids'):
            for fid in assistant.file_ids:
                try:
                    file = client.files.retrieve(fid)
                    print(f"- {file.filename} (ID: {file.id})")
                except Exception as e:
                    print(f"- Error retrieving file {fid}: {str(e)}")
        else:
            print("No files attached to assistant")
        
        # Check the file details
        print(f"\nFile details for {file_id}:")
        try:
            file = client.files.retrieve(file_id)
            print(f"Filename: {file.filename}")
            print(f"Purpose: {file.purpose}")
            print(f"Created at: {file.created_at}")
            print(f"Bytes: {file.bytes}")
        except Exception as e:
            print(f"Error retrieving file: {str(e)}")
        
    except FileNotFoundError:
        print("Error: vector_store_ids.json not found. Please run upload_to_vector_store.py first.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    check_assistant()

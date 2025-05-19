import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AssistantUpdater:
    def __init__(self, assistant_id=None):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = assistant_id
        self.assistant = None
        self.vector_store_id = None
        self.report = {
            'current_files': [],
            'new_assistant_id': None,
            'vector_store_id': None,
            'errors': []
        }
    
    def get_assistant(self):
        """Retrieve the current assistant."""
        try:
            if not self.assistant_id:
                raise ValueError("No assistant ID provided")
                
            self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            print(f"Current Assistant: {self.assistant.name} ({self.assistant.id})")
            
            # Get current file IDs
            current_file_ids = getattr(self.assistant, 'file_ids', [])
            if current_file_ids:
                print("\nCurrent files in assistant:")
                for file_id in current_file_ids:
                    try:
                        file_info = self.client.files.retrieve(file_id)
                        print(f"- {getattr(file_info, 'filename', 'unknown')} ({file_id})")
                        self.report['current_files'].append({
                            'id': file_id,
                            'filename': getattr(file_info, 'filename', 'unknown')
                        })
                    except Exception as e:
                        error = f"Error retrieving file {file_id}: {str(e)}"
                        print(f"  ❌ {error}")
                        self.report['errors'].append(error)
            else:
                print("No files currently attached to the assistant.")
                
            return True
            
        except Exception as e:
            error = f"Error retrieving assistant: {str(e)}"
            print(f"❌ {error}")
            self.report['errors'].append(error)
            return False
    
    def create_vector_store(self, file_ids, name="Lab Intake Documents"):
        """Create a new vector store with the given files."""
        try:
            print(f"\nCreating vector store with {len(file_ids)} files...")
            
            # Create the vector store
            vector_store = self.client.beta.vector_stores.create(
                name=name,
                file_ids=file_ids
            )
            
            self.vector_store_id = vector_store.id
            self.report['vector_store_id'] = vector_store.id
            print(f"✅ Vector store created: {vector_store.id}")
            
            return vector_store.id
            
        except Exception as e:
            error = f"Error creating vector store: {str(e)}"
            print(f"❌ {error}")
            self.report['errors'].append(error)
            return None
    
    def update_assistant(self, vector_store_id):
        """Update the assistant with the new vector store."""
        try:
            print("\nUpdating assistant with new vector store...")
            
            # Update the assistant with the new vector store
            updated_assistant = self.client.beta.assistants.update(
                self.assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            
            print(f"✅ Assistant updated successfully!")
            print(f"New tool_resources: {updated_assistant.tool_resources}")
            
            return updated_assistant
            
        except Exception as e:
            error = f"Error updating assistant: {str(e)}"
            print(f"❌ {error}")
            self.report['errors'].append(error)
            return None
    
    def create_new_assistant(self, name, instructions, file_ids):
        """Create a new assistant with the given files."""
        try:
            print(f"\nCreating new assistant with {len(file_ids)} files...")
            
            # First create the vector store
            vector_store_id = self.create_vector_store(file_ids, name=f"{name} Documents")
            if not vector_store_id:
                raise Exception("Failed to create vector store")
            
            # Then create the assistant with the vector store
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                },
                model="gpt-4-turbo-preview"
            )
            
            self.report['new_assistant_id'] = assistant.id
            print(f"✅ Assistant created: {assistant.id}")
            
            return assistant
            
        except Exception as e:
            error = f"Error creating assistant: {str(e)}"
            print(f"❌ {error}")
            self.report['errors'].append(error)
            return None
    
    def save_report(self):
        """Save the report to a file."""
        with open('assistant_update_report.json', 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\nReport saved to 'assistant_update_report.json'")

def main():
    # Lab Intake Assistant ID
    assistant_id = "asst_cqEaz3Mj84w9WuOPDVr9mbch"
    
    print("=== Lab Intake Assistant Updater ===")
    print("This script will help you update your Lab Intake Assistant with the latest files.")
    
    # Initialize the updater
    updater = AssistantUpdater(assistant_id)
    
    # Get current assistant info
    if not updater.get_assistant():
        print("\nFailed to retrieve assistant. Check the errors above.")
        updater.save_report()
        return
    
    # Get the list of file IDs to keep (from previous cleanup)
    # These are the files we want to include in the updated assistant
    file_ids_to_keep = [
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
    
    # Ask user what to do
    print("\nOptions:")
    print("1. Create a new assistant with the cleaned files")
    print("2. Update the existing assistant with a new vector store")
    print("3. Just show the current files (no changes)")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        # Create a new assistant
        new_assistant = updater.create_new_assistant(
            name="Lab Intake Assistant (Updated)",
            instructions=instructions,
            file_ids=file_ids_to_keep
        )
        
        if new_assistant:
            print(f"\n✅ New assistant created successfully!")
            print(f"Assistant ID: {new_assistant.id}")
            
            # Option to delete the old assistant
            delete_old = input("\nDelete the old assistant? (y/n): ")
            if delete_old.lower() == 'y':
                try:
                    updater.client.beta.assistants.delete(assistant_id)
                    print(f"✅ Deleted old assistant: {assistant_id}")
                except Exception as e:
                    print(f"❌ Error deleting old assistant: {str(e)}")
    
    elif choice == "2":
        # Update existing assistant with a new vector store
        vector_store_id = updater.create_vector_store(
            file_ids=file_ids_to_keep,
            name="Lab Intake Documents"
        )
        
        if vector_store_id:
            updated = updater.update_assistant(vector_store_id)
            if updated:
                print(f"\n✅ Assistant updated successfully!")
    
    elif choice == "3":
        print("\nCurrent files have been listed above. No changes were made.")
    
    else:
        print("\nInvalid choice. No changes were made.")
    
    # Save the report
    updater.save_report()
    
    print("\n=== NEXT STEPS ===")
    print("1. Review 'assistant_update_report.json' for details")
    print("2. Test the updated assistant in the OpenAI Playground")
    print("3. Update any code that references the assistant ID if needed")

if __name__ == "__main__":
    main()

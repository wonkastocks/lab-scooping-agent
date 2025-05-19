import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

class VectorDBOrganizer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.ids_file = "vector_store_ids.json"
        self.ids = self._load_ids()
        
    def _load_ids(self):
        """Load existing vector store IDs from file."""
        if os.path.exists(self.ids_file):
            with open(self.ids_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_ids(self):
        """Save current vector store IDs to file."""
        with open(self.ids_file, 'w') as f:
            json.dump(self.ids, f, indent=2)
    
    def cleanup_temp_files(self):
        """Remove temporary files from the vector database."""
        print("Cleaning up temporary files...")
        files = self.client.files.list()
        temp_keywords = ['tmp', 'combined_content']
        deleted = 0
        
        for file in files.data:
            filename = getattr(file, 'filename', '').lower()
            if any(keyword in filename for keyword in temp_keywords):
                print(f"Deleting temporary file: {filename} ({file.id})")
                try:
                    self.client.files.delete(file.id)
                    deleted += 1
                except Exception as e:
                    print(f"  Error deleting {file.id}: {str(e)}")
        
        print(f"\nDeleted {deleted} temporary files.")
        return deleted
    
    def create_assistant(self, name, instructions, tools=None):
        """Create a new assistant."""
        if tools is None:
            tools = []
            
        try:
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model="gpt-4-1106-preview"
            )
            print(f"Created assistant: {assistant.id} - {name}")
            return assistant
        except Exception as e:
            print(f"Error creating assistant {name}: {str(e)}")
            return None
    
    def organize_projects(self):
        """Organize files into projects and create assistants."""
        print("\nOrganizing projects...")
        
        # Create project structure
        projects = {
            'bible_study': {
                'name': 'Bible Study Assistant',
                'instructions': """
                You are a helpful assistant for Bible study. You can help with:
                - Explaining Bible verses and passages
                - Providing historical context
                - Finding related scriptures
                - Answering theological questions
                """,
                'tools': [{"type": "retrieval"}],
                'file_keywords': ['bible', 'kjv', 'niv', 'nt', 'strongs', 'concordance', 'nlt', 'amplified', 'jerusalem']
            },
            'lab_intake': {
                'name': 'Lab Intake Assistant',
                'instructions': """
                You are an assistant that helps with lab intake documentation. 
                You have access to various lab-related documents including requirements, 
                questionnaires, and technical specifications.
                """,
                'tools': [{"type": "retrieval"}],
                'file_keywords': [
                    'infoseclearning', 'rag_questionnaire', 'aci_lab_questionnaire', 
                    'acilearning', 'common-terms', 'intake-questionaire', 'workflow',
                    'linux_windows_networking', 'terms_glossary', 'vmware_virtualization',
                    'constellation', 'lab tracker', 'learning-content_export'
                ]
            }
        }
        
        # Get all files
        files = self.client.files.list()
        
        # Initialize project files
        for project in projects.values():
            project['files'] = []
        
        # Categorize files
        for file in files.data:
            if file.purpose != 'assistants':
                continue
                
            filename = getattr(file, 'filename', '').lower()
            
            # Skip temporary files (they should be deleted by now)
            if 'tmp' in filename or 'combined_content' in filename:
                continue
                
            # Find which project this file belongs to
            file_assigned = False
            for project in projects.values():
                if any(keyword.lower() in filename for keyword in project['file_keywords']):
                    project['files'].append(file)
                    file_assigned = True
                    break
            
            if not file_assigned:
                print(f"Note: File not assigned to any project: {filename} ({file.id})")
        
        # Create assistants and attach files
        for project_id, project in projects.items():
            if not project['files']:
                print(f"\nNo files found for {project['name']}. Skipping assistant creation.")
                continue
                
            print(f"\n=== {project['name'].upper()} ===")
            print(f"Files: {len(project['files'])}")
            
            # Create assistant
            assistant = self.create_assistant(
                name=project['name'],
                instructions=project['instructions'],
                tools=project['tools']
            )
            
            if not assistant:
                continue
                
            # Save assistant ID
            if 'assistants' not in self.ids:
                self.ids['assistants'] = {}
                
            self.ids['assistants'][project_id] = {
                'id': assistant.id,
                'name': project['name'],
                'created': datetime.now(timezone.utc).isoformat(),
                'file_ids': [f.id for f in project['files']]
            }
            
            # Print file list
            print("\nAttached files:")
            for file in project['files']:
                print(f"  - {getattr(file, 'filename', 'unknown')} ({file.id})")
        
        # Save all IDs
        self._save_ids()
        print("\nOrganization complete!")

def main():
    organizer = VectorDBOrganizer()
    
    # Step 1: Clean up temporary files
    print("=== STEP 1: Cleaning up temporary files ===")
    organizer.cleanup_temp_files()
    
    # Step 2: Organize projects and create assistants
    print("\n=== STEP 2: Organizing projects ===")
    organizer.organize_projects()
    
    print("\n=== COMPLETE ===")
    print("1. Temporary files have been cleaned up")
    print("2. Projects have been organized")
    print("3. Assistants have been created")
    print("\nCheck vector_store_ids.json for assistant and file references.")

if __name__ == "__main__":
    main()

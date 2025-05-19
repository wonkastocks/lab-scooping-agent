import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

class ProjectOrganizer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.ids_file = "project_organization.json"
        self.organization = self._load_organization()
    
    def _load_organization(self):
        """Load existing organization data."""
        if os.path.exists(self.ids_file):
            with open(self.ids_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_organization(self):
        """Save organization data to file."""
        with open(self.ids_file, 'w') as f:
            json.dump(self.organization, f, indent=2)
    
    def list_all_files(self):
        """List all files in the vector database."""
        files = self.client.files.list()
        return [f for f in files.data if f.purpose == 'assistants']
    
    def create_assistant(self, name, instructions, file_ids=None):
        """Create a new assistant with optional file attachments."""
        if file_ids is None:
            file_ids = []
            
        try:
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=[{"type": "file_search"}],
                model="gpt-4-1106-preview"
            )
            
            print(f"✅ Created assistant: {assistant.id} - {name}")
            
            # Create a vector store for the files
            if file_ids:
                vector_store = self.client.beta.vector_stores.create(
                    name=f"{name} - {datetime.now().strftime('%Y-%m-%d')}",
                    file_ids=file_ids
                )
                
                # Update the assistant with the vector store
                self.client.beta.assistants.update(
                    assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
                )
                
                print(f"  - Added {len(file_ids)} files to vector store: {vector_store.id}")
                
                return {
                    'assistant_id': assistant.id,
                    'vector_store_id': vector_store.id,
                    'file_ids': file_ids,
                    'created': datetime.now(timezone.utc).isoformat()
                }
            
            return {'assistant_id': assistant.id}
            
        except Exception as e:
            print(f"❌ Error creating assistant {name}: {str(e)}")
            return None
    
    def organize_projects(self):
        """Organize files into projects and create assistants."""
        print("\n🔍 Scanning vector database...")
        
        # Define projects
        projects = {
            'bible_study': {
                'name': 'Bible Study Assistant',
                'description': 'Assistant for Bible study and theological questions',
                'instructions': """
                You are a helpful assistant for Bible study. You can help with:
                - Explaining Bible verses and passages
                - Providing historical context
                - Finding related scriptures
                - Answering theological questions
                
                Always provide scriptural references for your answers.
                """,
                'file_keywords': ['bible', 'kjv', 'niv', 'nt', 'strongs', 'concordance', 'nlt', 'amplified', 'jerusalem']
            },
            'lab_intake': {
                'name': 'Lab Intake Assistant',
                'description': 'Assistant for lab documentation and requirements',
                'instructions': """
                You are an assistant that helps with lab intake documentation. 
                You have access to various lab-related documents including requirements, 
                questionnaires, and technical specifications.
                
                Provide detailed, accurate information based on the documentation.
                """,
                'file_keywords': [
                    'infoseclearning', 'rag_questionnaire', 'aci_lab_questionnaire', 
                    'acilearning', 'common-terms', 'intake-questionaire', 'workflow',
                    'linux_windows_networking', 'terms_glossary', 'vmware_virtualization',
                    'constellation', 'lab tracker', 'learning-content_export'
                ]
            }
        }
        
        # Get all files
        all_files = self.list_all_files()
        
        # Categorize files
        for project_id, project in projects.items():
            project_files = []
            
            for file in all_files:
                filename = getattr(file, 'filename', '').lower()
                if any(keyword.lower() in filename for keyword in project['file_keywords']):
                    project_files.append(file)
            
            project['files'] = project_files
        
        # Create assistants and organize files
        self.organization['projects'] = {}
        
        for project_id, project in projects.items():
            print(f"\n=== {project['name'].upper()} ===")
            print(f"Description: {project['description']}")
            
            if not project['files']:
                print("  No files found for this project.")
                continue
            
            print(f"  Found {len(project['files'])} files:")
            for file in project['files']:
                print(f"  - {getattr(file, 'filename', 'unknown')} ({file.id})")
            
            # Create assistant for this project
            file_ids = [f.id for f in project['files']]
            assistant_data = self.create_assistant(
                name=project['name'],
                instructions=project['instructions'],
                file_ids=file_ids
            )
            
            if assistant_data:
                self.organization['projects'][project_id] = {
                    'name': project['name'],
                    'description': project['description'],
                    'assistant_id': assistant_data.get('assistant_id'),
                    'vector_store_id': assistant_data.get('vector_store_id'),
                    'file_ids': assistant_data.get('file_ids', []),
                    'created': datetime.now(timezone.utc).isoformat()
                }
        
        # Save organization data
        self._save_organization()
        
        print("\n✅ Organization complete!")
        print(f"Project details saved to: {self.ids_file}")

def main():
    print("=== PROJECT ORGANIZER ===")
    print("This script will help organize your vector database into projects.")
    
    organizer = ProjectOrganizer()
    organizer.organize_projects()
    
    print("\n=== NEXT STEPS ===")
    print("1. Review the project_organization.json file")
    print("2. Use the assistant IDs to interact with each project")
    print("3. To clean up, you can delete old assistants/files as needed")

if __name__ == "__main__":
    main()

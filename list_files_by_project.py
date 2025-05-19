import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

def list_files_by_project():
    """List all files in the vector database, grouped by project."""
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # List all files
        files = client.files.list()
        
        # Define project groups
        projects = {
            'lab_intake': [
                'Infoseclearning.md',
                'rag_questionnaire.md',
                'aci_lab_questionnaire_full.md',
                'ACILEARNING.md',
                'Common-Terms.md',
                'ACI-INTAKE-QUESTIONAIRE.rtf',
                'aci_lab_intake_workflow.json',
                'rag_linux_windows_networking.md',
                'rag_terms_glossary.md',
                'Constellation Lab Tracker',
                'rag_vmware_virtualization.md',
                'infosec_learning-content_export'
            ],
            'bible_study': [
                'bible', 'kjv', 'niv', 'nt', 'strongs', 'concordance', 'nlt', 
                'amplified', 'jerusalem', 'kjv-strongs', 'dictionary'
            ]
        }
        
        # Initialize project groups
        file_groups = defaultdict(list)
        other_files = []
        
        print("Scanning vector database...\n")
        
        for file in files.data:
            if file.purpose != 'assistants':
                continue
                
            filename = getattr(file, 'filename', '').lower()
            file_info = {
                'id': file.id,
                'filename': getattr(file, 'filename', 'unknown'),
                'created': file.created_at,
                'size': getattr(file, 'bytes', 0)
            }
            
            # Check which project this file belongs to
            found_project = False
            
            for project, keywords in projects.items():
                if any(keyword.lower() in filename for keyword in keywords):
                    file_groups[project].append(file_info)
                    found_project = True
                    break
            
            if not found_project:
                other_files.append(file_info)
        
        # Print results
        for project, files in file_groups.items():
            print(f"\n=== {project.upper()} PROJECT ({len(files)} files) ===")
            for file in sorted(files, key=lambda x: x['created'], reverse=True):
                print(f"ID: {file['id']}")
                print(f"  Filename: {file['filename']}")
                print(f"  Created: {file['created']}")
                print(f"  Size: {file['size']} bytes")
        
        if other_files:
            print("\n=== OTHER FILES (not in defined projects) ===")
            for file in sorted(other_files, key=lambda x: x['created'], reverse=True):
                print(f"ID: {file['id']}")
                print(f"  Filename: {file['filename']}")
                print(f"  Created: {file['created']}")
                print(f"  Size: {file['size']} bytes")
        
        print("\nSummary:")
        for project, files in file_groups.items():
            print(f"- {project}: {len(files)} files")
        print(f"- Other: {len(other_files)} files")
        print("\nNote: Files are grouped based on filename keywords.")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    list_files_by_project()

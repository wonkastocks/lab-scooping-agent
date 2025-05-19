import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LabIntakeCleanup:
    def __init__(self, assistant_id):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = assistant_id
        self.assistant = None
        self.files = {}
        self.cleanup_report = {
            'removed_files': [],
            'kept_files': [],
            'errors': []
        }
    
    def get_assistant(self):
        """Retrieve the assistant and its files."""
        try:
            self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            print(f"Assistant: {self.assistant.name} ({self.assistant.id})")
            return True
        except Exception as e:
            self.cleanup_report['errors'].append(f"Error retrieving assistant: {str(e)}")
            return False
    
    def get_all_files(self):
        """Retrieve all files from the OpenAI account."""
        try:
            all_files = self.client.files.list()
            self.files = {f.id: f for f in all_files.data if f.purpose == 'assistants'}
            print(f"Found {len(self.files)} assistant files in total.")
            return True
        except Exception as e:
            self.cleanup_report['errors'].append(f"Error retrieving files: {str(e)}")
            return False
    
    def identify_files_to_clean(self):
        """Identify files that need cleanup."""
        # Files to keep (with standardized names)
        keep_files = {}
        
        # Files to remove (duplicates, typos, etc.)
        remove_files = []
        
        # Group files by base name
        file_groups = {}
        for file_id, file in self.files.items():
            name = getattr(file, 'filename', '').lower()
            base_name = name.split('_')[0].split('.')[0]
            
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append(file)
        
        # Process each group
        for base_name, files in file_groups.items():
            if len(files) == 1:
                # Single file, keep as is
                keep_files[files[0].id] = files[0]
            else:
                # Multiple files with similar names
                if base_name == 'aci':
                    # Keep the one without typo ('full' not 'fulll')
                    selected = next((f for f in files if 'fulll' not in getattr(f, 'filename', '')), files[0])
                    keep_files[selected.id] = selected
                    
                    # Mark others for removal
                    for f in files:
                        if f.id != selected.id:
                            remove_files.append(f)
                else:
                    # For other groups, keep all but standardize names if needed
                    for f in files:
                        keep_files[f.id] = f
        
        return keep_files, remove_files
    
    def remove_file(self, file_id, filename):
        """Remove a file from the assistant and delete it."""
        try:
            # Remove from assistant (if applicable)
            if hasattr(self.assistant, 'file_ids') and file_id in self.assistant.file_ids:
                # Note: In the current API, we can't directly modify file associations
                # We'll need to recreate the assistant with the correct files
                pass
            
            # Delete the file
            self.client.files.delete(file_id)
            self.cleanup_report['removed_files'].append({
                'id': file_id,
                'filename': filename,
                'reason': 'Duplicate or typo in filename'
            })
            print(f"✅ Removed: {filename} ({file_id})")
            return True
            
        except Exception as e:
            error_msg = f"Error removing file {filename} ({file_id}): {str(e)}"
            print(f"❌ {error_msg}")
            self.cleanup_report['errors'].append(error_msg)
            return False
    
    def update_assistant_files(self, keep_file_ids):
        """Update the assistant with the cleaned file set."""
        try:
            # In the current API, we need to create a new assistant with the correct files
            # and delete the old one
            new_assistant = self.client.beta.assistants.create(
                name=f"{self.assistant.name} (Cleaned)",
                instructions=self.assistant.instructions,
                tools=[{"type": "file_search"}],
                model="gpt-4-1106-preview",
                file_ids=list(keep_file_ids)
            )
            
            # Delete the old assistant
            self.client.beta.assistants.delete(self.assistant_id)
            
            print(f"✅ Created new assistant: {new_assistant.id}")
            print(f"✅ Deleted old assistant: {self.assistant_id}")
            
            return new_assistant.id
            
        except Exception as e:
            error_msg = f"Error updating assistant: {str(e)}"
            print(f"❌ {error_msg}")
            self.cleanup_report['errors'].append(error_msg)
            return None
    
    def cleanup(self):
        """Run the cleanup process."""
        print("=== Lab Intake Cleanup ===")
        
        # Get assistant and files
        if not self.get_assistant() or not self.get_all_files():
            print("Failed to retrieve assistant or files. Check errors below.")
            self.save_report()
            return
        
        # Identify files to keep and remove
        keep_files, remove_files = self.identify_files_to_clean()
        
        print(f"\n=== FILES TO KEEP ({len(keep_files)}) ===")
        for file_id, file in keep_files.items():
            print(f"- {getattr(file, 'filename', 'unknown')} ({file_id})")
            self.cleanup_report['kept_files'].append({
                'id': file_id,
                'filename': getattr(file, 'filename', 'unknown')
            })
        
        print(f"\n=== FILES TO REMOVE ({len(remove_files)}) ===")
        for file in remove_files:
            print(f"- {getattr(file, 'filename', 'unknown')} ({file.id})")
        
        # Ask for confirmation
        confirm = input("\nProceed with cleanup? (y/n): ")
        if confirm.lower() != 'y':
            print("Cleanup cancelled.")
            return
        
        # Remove files
        for file in remove_files:
            self.remove_file(file.id, getattr(file, 'filename', 'unknown'))
        
        # Update assistant with kept files
        new_assistant_id = self.update_assistant_files(keep_files.keys())
        if new_assistant_id:
            self.cleanup_report['new_assistant_id'] = new_assistant_id
        
        # Save report
        self.save_report()
        
        print("\n✅ Cleanup complete!")
    
    def save_report(self):
        """Save the cleanup report to a file."""
        with open('lab_intake_cleanup_report.json', 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        print(f"\nCleanup report saved to 'lab_intake_cleanup_report.json'")

def main():
    # Lab Intake Assistant ID
    assistant_id = "asst_cqEaz3Mj84w9WuOPDVr9mbch"
    
    # Run cleanup
    cleaner = LabIntakeCleanup(assistant_id)
    cleaner.cleanup()
    
    print("\n=== NEXT STEPS ===")
    print("1. Review 'lab_intake_cleanup_report.json' for details")
    print("2. Verify the new assistant has the correct files")
    print("3. Update any code that references the old assistant ID")

if __name__ == "__main__":
    main()

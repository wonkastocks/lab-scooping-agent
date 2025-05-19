import os
import json
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

class LabIntakeAnalyzer:
    def __init__(self, assistant_id):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = assistant_id
        self.assistant = None
        self.files = {}
        self.content_hashes = defaultdict(list)
        
    def get_assistant_files(self):
        """Retrieve all files associated with the assistant."""
        try:
            self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            print(f"Assistant: {self.assistant.name} ({self.assistant.id})")
            
            # Get all files in the organization (since we can't directly get files from assistant)
            all_files = self.client.files.list()
            
            # Get file IDs from the assistant's metadata
            file_ids = []
            if hasattr(self.assistant, 'file_ids'):
                file_ids = self.assistant.file_ids
            
            # Filter files that belong to this assistant
            self.files = {
                f.id: f for f in all_files.data 
                if f.id in file_ids and f.purpose == 'assistants'
            }
            
            print(f"Found {len(self.files)} files in the assistant.")
            return self.files
            
        except Exception as e:
            print(f"Error retrieving assistant files: {str(e)}")
            return {}
    
    def download_file_content(self, file_id):
        """Download and return the content of a file."""
        try:
            content = self.client.files.content(file_id)
            return content.text
        except Exception as e:
            print(f"Error downloading file {file_id}: {str(e)}")
            return None
    
    def calculate_content_hash(self, content):
        """Calculate a hash of the content for duplicate detection."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def analyze_duplicates(self):
        """Analyze files for duplicate content."""
        if not self.files:
            print("No files to analyze. Run get_assistant_files() first.")
            return
        
        print("\nAnalyzing files for duplicate content...")
        
        # Download and hash all files
        for file_id, file in self.files.items():
            filename = getattr(file, 'filename', 'unknown')
            print(f"Analyzing: {filename} ({file_id})")
            
            content = self.download_file_content(file_id)
            if content:
                content_hash = self.calculate_content_hash(content)
                self.content_hashes[content_hash].append({
                    'file_id': file_id,
                    'filename': filename,
                    'size': len(content),
                    'content': content[:500] + '...' if len(content) > 500 else content  # Store preview
                })
        
        # Find duplicates
        duplicates = {h: files for h, files in self.content_hashes.items() if len(files) > 1}
        
        if duplicates:
            print("\n⚠️  Found duplicate content in the following files:")
            for hash_val, files in duplicates.items():
                print(f"\nHash: {hash_val[:8]}...")
                for file in files:
                    print(f"  - {file['filename']} ({file['file_id']})")
                    print(f"    Size: {file['size']} bytes")
                    print(f"    Preview: {file['content'][:200]}...")
        else:
            print("\n✅ No duplicate content found.")
        
        return duplicates
    
    def suggest_consolidation(self):
        """Suggest consolidation strategy."""
        if not self.files:
            print("No files to analyze. Run get_assistant_files() first.")
            return
            
        print("\n=== CONSOLIDATION SUGGESTIONS ===")
        
        # Group files by name similarity
        file_groups = defaultdict(list)
        for file in self.files.values():
            name = getattr(file, 'filename', 'unknown')
            # Basic grouping by filename prefix
            group_key = name.split('_')[0].lower()
            file_groups[group_key].append({
                'id': file.id,
                'filename': name,
                'size': getattr(file, 'bytes', 0)
            })
        
        # Print suggestions
        for group, files in file_groups.items():
            if len(files) > 1:
                print(f"\n🔍 Similar files (group: {group}):")
                for file in files:
                    print(f"  - {file['filename']} ({file['id']}) - {file['size']} bytes")
                
                # Check if these might be duplicates
                if len(files) == 2 and all(f['size'] == files[0]['size'] for f in files):
                    print("  🚨 Possible exact duplicates - consider keeping only one")
                else:
                    print("  ℹ️  Similar filenames - review for content duplication")
        
        # Check for large files that might need splitting
        large_files = [f for f in self.files.values() if getattr(f, 'bytes', 0) > 1024 * 1024]  # >1MB
        if large_files:
            print("\n📏 Large files that might need splitting:")
            for file in large_files:
                print(f"  - {getattr(file, 'filename', 'unknown')} ({getattr(file, 'bytes', 0) / 1024 / 1024:.1f} MB)")

def main():
    # Lab Intake Assistant ID
    assistant_id = "asst_cqEaz3Mj84w9WuOPDVr9mbch"
    
    print(f"Analyzing Lab Intake Assistant: {assistant_id}")
    
    analyzer = LabIntakeAnalyzer(assistant_id)
    
    # Step 1: Get all files in the assistant
    files = analyzer.get_assistant_files()
    
    if not files:
        print("No files found in the assistant.")
        return
    
    # Step 2: Analyze for duplicates
    duplicates = analyzer.analyze_duplicates()
    
    # Step 3: Suggest consolidation strategy
    analyzer.suggest_consolidation()
    
    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Total files analyzed: {len(files)}")
    print(f"Duplicate content groups found: {len(duplicates) if duplicates else 0}")

if __name__ == "__main__":
    main()

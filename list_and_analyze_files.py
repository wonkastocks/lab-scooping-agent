import os
import json
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

class FileAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.files = {}
        self.content_hashes = defaultdict(list)
        
    def get_all_files(self):
        """Retrieve all files from the OpenAI account."""
        try:
            all_files = self.client.files.list()
            # Only include assistant files
            self.files = {f.id: f for f in all_files.data if f.purpose == 'assistants'}
            print(f"Found {len(self.files)} assistant files in total.")
            return self.files
        except Exception as e:
            print(f"Error retrieving files: {str(e)}")
            return {}
    
    def download_file_content(self, file_id):
        """Download and return the content of a file."""
        try:
            content = self.client.files.content(file_id)
            return content.text
        except Exception as e:
            print(f"Error downloading file {file_id}: {str(e)}")
            return None
    
    def analyze_files(self):
        """Analyze files for duplicates and content."""
        if not self.files:
            print("No files to analyze. Run get_all_files() first.")
            return
            
        print("\nAnalyzing files...")
        
        # Lab intake file patterns to look for
        lab_intake_patterns = [
            'infoseclearning', 'rag_questionnaire', 'aci_lab_questionnaire', 
            'acilearning', 'common-terms', 'intake-questionaire', 'workflow',
            'linux_windows_networking', 'terms_glossary', 'vmware_virtualization',
            'constellation', 'lab tracker', 'learning-content_export'
        ]
        
        lab_files = {}
        
        # First pass: identify lab intake files
        for file_id, file in self.files.items():
            filename = getattr(file, 'filename', '').lower()
            if any(pattern.lower() in filename for pattern in lab_intake_patterns):
                lab_files[file_id] = file
        
        print(f"\nFound {len(lab_files)} lab intake files:")
        for file_id, file in lab_files.items():
            print(f"- {getattr(file, 'filename', 'unknown')} ({file_id})")
        
        # Second pass: analyze content of lab files
        print("\nAnalyzing content for duplicates...")
        for file_id, file in lab_files.items():
            filename = getattr(file, 'filename', 'unknown')
            print(f"Analyzing: {filename}")
            
            content = self.download_file_content(file_id)
            if content:
                # Clean content for better comparison
                clean_content = ' '.join(content.split()).lower()
                content_hash = hashlib.md5(clean_content.encode('utf-8')).hexdigest()
                
                self.content_hashes[content_hash].append({
                    'file_id': file_id,
                    'filename': filename,
                    'size': len(content),
                    'content_preview': clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
                })
        
        # Find duplicates (same content hash)
        duplicates = {h: files for h, files in self.content_hashes.items() if len(files) > 1}
        
        # Find similar filenames (potential duplicates with different names)
        filename_groups = defaultdict(list)
        for file in lab_files.values():
            name = getattr(file, 'filename', '').lower()
            # Group by first part of filename (before first _ or .)
            base_name = name.split('_')[0].split('.')[0]
            filename_groups[base_name].append(file)
        
        # Generate report
        report = {
            'total_files': len(lab_files),
            'duplicate_groups': [],
            'similar_filenames': [],
            'files': []
        }
        
        # Add duplicate groups to report
        for hash_val, files in duplicates.items():
            group = {
                'hash': hash_val[:8] + '...',
                'files': []
            }
            for file in files:
                group['files'].append({
                    'id': file['file_id'],
                    'filename': file['filename'],
                    'size': file['size']
                })
            report['duplicate_groups'].append(group)
        
        # Add similar filename groups to report
        for base_name, files in filename_groups.items():
            if len(files) > 1:  # Only include groups with multiple files
                group = {
                    'base_name': base_name,
                    'files': [{'id': f.id, 'filename': getattr(f, 'filename', 'unknown')} for f in files]
                }
                report['similar_filenames'].append(group)
        
        # Add all files to report
        for file_id, file in lab_files.items():
            report['files'].append({
                'id': file_id,
                'filename': getattr(file, 'filename', 'unknown'),
                'size': getattr(file, 'bytes', 0),
                'created': getattr(file, 'created_at', 0)
            })
        
        # Save report
        with open('lab_intake_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nAnalysis complete. Report saved to 'lab_intake_analysis.json'")
        
        # Print summary
        print(f"\n=== SUMMARY ===")
        print(f"Total lab intake files: {len(lab_files)}")
        print(f"Duplicate content groups: {len(duplicates)}")
        print(f"Similar filename groups: {len([g for g in filename_groups.values() if len(g) > 1])}")
        
        if duplicates:
            print("\n⚠️  Duplicate content found in:")
            for i, (hash_val, files) in enumerate(duplicates.items(), 1):
                print(f"\nGroup {i} (hash: {hash_val[:8]}...):")
                for file in files:
                    print(f"  - {file['filename']} ({file['file_id']})")
        
        similar_groups = {k: v for k, v in filename_groups.items() if len(v) > 1}
        if similar_groups:
            print("\n🔍 Files with similar names (potential duplicates):")
            for base_name, files in similar_groups.items():
                print(f"\nGroup '{base_name}':")
                for file in files:
                    print(f"  - {getattr(file, 'filename', 'unknown')} ({file.id})")

def main():
    print("=== Lab Intake Files Analysis ===")
    print("This script will analyze files in the Lab Intake Assistant for duplicates.")
    
    analyzer = FileAnalyzer()
    
    # Get all files
    print("\nFetching all files...")
    files = analyzer.get_all_files()
    
    if not files:
        print("No files found.")
        return
    
    # Analyze files
    analyzer.analyze_files()
    
    print("\n=== NEXT STEPS ===")
    print("1. Review 'lab_intake_analysis.json' for detailed analysis")
    print("2. Check for duplicate files with similar content")
    print("3. Consider consolidating or removing duplicates")
    print("4. Update the assistant with the cleaned file set")

if __name__ == "__main__":
    main()

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
SOURCE_DIR = Path("Courses/INTAKE-DOCS")
OUTPUT_DIR = Path("MONGO_DB_FILES")
OUTPUT_DIR.mkdir(exist_ok=True)

def read_file_content(file_path: Path, max_size_mb: int = 16) -> Optional[str]:
    """Read file content with proper error handling and size limit"""
    try:
        # Check file size
        file_size = file_path.stat().st_size
        max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
        
        # Read the file in binary mode first to avoid encoding issues
        with open(file_path, 'rb') as f:
            content_bytes = f.read(min(file_size, max_size))
            
            # Try to decode as UTF-8, fall back to latin-1 if that fails
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return content_bytes.decode('latin-1')
                except Exception as e:
                    print(f"Warning: Could not decode {file_path} with UTF-8 or latin-1: {str(e)}")
                    return "[Binary content - could not decode]"
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def create_mongodb_document(file_path: Path) -> Dict[str, Any]:
    """Create a MongoDB document from a file"""
    try:
        # Resolve to absolute path first
        abs_path = file_path.resolve()
        file_stat = abs_path.stat()
        
        # For large files, we'll store the content in a separate file
        doc_id = f"doc_{abs_path.stem}"
        content_file = None
        content = ""
        
        try:
            # Try to read the full content first
            content = read_file_content(abs_path)
            if content is None:
                return {}
                
            # If content is too large, save to separate file
            if len(content) > 1024 * 1024:  # 1MB
                content_file = OUTPUT_DIR / f"{doc_id}_content.txt"
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                content = f"[Content stored in {content_file.name}]"
                
        except Exception as e:
            print(f"Error processing content for {abs_path}: {str(e)}")
            return {}
            
        doc = {
            "_id": doc_id,
            "filename": abs_path.name,
            "file_type": abs_path.suffix.lower().lstrip('.'),
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "size_bytes": file_stat.st_size,
            "relative_path": str(abs_path.relative_to(Path.cwd())),
            "content": content,
            "metadata": {
                "source": "lab_intake_docs",
                "processing_time": datetime.utcnow().isoformat(),
                "has_external_content": content_file is not None,
                "content_file": str(content_file.name) if content_file else None
            }
        }
        
        return doc
    except Exception as e:
        print(f"Error creating document for {file_path}: {str(e)}")
        return {}

def main():
    print("Starting document processing...")
    
    # Get all markdown files
    markdown_files = []
    for ext in ['*.md', '*.txt', '*.markdown']:
        markdown_files.extend(SOURCE_DIR.glob(ext))
    print(f"Found {len(markdown_files)} markdown files in {SOURCE_DIR}")
    
    # Process files
    documents = []
    for file_path in markdown_files:
        print(f"Processing: {file_path.name}")
        doc = create_mongodb_document(file_path)
        if doc:
            documents.append(doc)
    
    if documents:
        # Create a timestamp for the output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as a single JSON array
        output_file = OUTPUT_DIR / f"lab_intake_documents_{timestamp}.json"
        # Save as a JSON array with proper encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            json_str = json.dumps(documents, indent=2, ensure_ascii=False)
            f.write(json_str)
        
        # Also save individual JSON files
        for doc in documents:
            doc_file = OUTPUT_DIR / f"doc_{doc['_id']}.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json_str = json.dumps(doc, indent=2, ensure_ascii=False)
                f.write(json_str)
        
        print(f"\n✅ Successfully processed {len(documents)} files.")
        print(f"📄 MongoDB documents saved to: {output_file}")
        print("\nTo import into MongoDB, you can use:")
        print(f"mongoimport --db lab_intake --collection documents --file {output_file} --jsonArray")
        print("\nOr for individual files:")
        print(f"for f in {OUTPUT_DIR}/doc_*.json; do mongoimport --db lab_intake --collection documents --file $f; done")
    else:
        print("\n❌ No documents were processed successfully.")

if __name__ == "__main__":
    main()

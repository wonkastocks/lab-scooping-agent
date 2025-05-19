import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
SOURCE_DIR = Path("Courses/INTAKE-DOCS")
OUTPUT_DIR = Path("MONGO_EXPORT_ORIGINAL_NAMES")
OUTPUT_DIR.mkdir(exist_ok=True)

def read_file_content(file_path: Path, max_size_mb: int = 16) -> Optional[str]:
    """Read file content with proper error handling and size limit"""
    try:
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

def create_document_metadata(file_path: Path) -> Dict[str, Any]:
    """Create document metadata without the content"""
    try:
        abs_path = file_path.resolve()
        file_stat = abs_path.stat()
        
        return {
            "_id": f"doc_{abs_path.stem}",
            "filename": abs_path.name,
            "file_type": abs_path.suffix.lower().lstrip('.'),
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "size_bytes": file_stat.st_size,
            "relative_path": str(abs_path.relative_to(Path.cwd())),
            "metadata": {
                "source": "lab_intake_docs",
                "processing_time": datetime.utcnow().isoformat(),
                "exported_at": datetime.now().strftime("%Y-%m-%d_%H%M%S")
            }
        }
    except Exception as e:
        print(f"Error creating metadata for {file_path}: {str(e)}")
        return {}

def main():
    print("Starting document export with original filenames...")
    
    # Get all markdown and text files
    files = []
    for ext in ['*.md', '*.txt', '*.markdown']:
        files.extend(SOURCE_DIR.glob(ext))
    
    print(f"Found {len(files)} files in {SOURCE_DIR}")
    
    # Create a manifest of all files
    manifest = {
        "export_date": datetime.utcnow().isoformat(),
        "total_files": len(files),
        "files": []
    }
    
    # Process files
    for file_path in files:
        try:
            print(f"Processing: {file_path.name}")
            
            # Create metadata
            metadata = create_document_metadata(file_path)
            if not metadata:
                continue
                
            # Add to manifest
            file_info = {
                "original_name": file_path.name,
                "exported_name": f"{metadata['_id']}.json",
                "size_bytes": metadata["size_bytes"],
                "exported_at": datetime.utcnow().isoformat()
            }
            manifest["files"].append(file_info)
            
            # Export the original file
            dest_file = OUTPUT_DIR / file_path.name
            try:
                content = read_file_content(file_path)
                if content is not None:
                    with open(dest_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  → Exported to: {dest_file}")
                else:
                    print(f"  → Skipped (no content): {file_path.name}")
            except Exception as e:
                print(f"  → Error exporting {file_path.name}: {str(e)}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Save the manifest
    manifest_file = OUTPUT_DIR / "_export_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Successfully processed {len(files)} files.")
    print(f"📄 Files exported to: {OUTPUT_DIR}")
    print(f"📋 Manifest file: {manifest_file}")

if __name__ == "__main__":
    main()

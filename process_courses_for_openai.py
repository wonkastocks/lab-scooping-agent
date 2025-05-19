import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import tiktoken
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
OUTPUT_DIR = Path("output")
EMBEDDING_MODEL = "text-embedding-3-small"  # Using the latest embedding model
MAX_TOKENS = 8000  # Maximum context length for the embedding model
CHUNK_SIZE = 1000  # Number of characters per chunk for long text

def clean_text(text: Any) -> str:
    """Clean and convert text to string, handling NaN and other non-string types."""
    if pd.isna(text) or text is None:
        return ""
    return str(text).strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks of specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def process_lab_tracker(file_path: Path) -> List[Dict[str, Any]]:
    """Process the Constellation Lab Tracker CSV file."""
    try:
        logger.info(f"Processing lab tracker file: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='warn')
        
        # Clean column names and handle missing columns
        df.columns = [col.strip() if isinstance(col, str) else str(col) for col in df.columns]
        
        # Ensure required columns exist, create empty ones if they don't
        required_columns = ["Lab #", "Lab Name", "VMs Required", "Internet Required?"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        records = []
        for _, row in df.iterrows():
            # Create a clean record with only non-empty fields
            record = {
                "source": "lab_tracker",
                "source_file": file_path.name,  # Add original filename
                "lab_id": clean_text(row.get("Lab #", "")),
                "title": clean_text(row.get("Lab Name", "")),
                "vms_required": clean_text(row.get("VMs Required", "")),
                "internet_required": clean_text(row.get("Internet Required?", "")),
                "metadata": {}
            }
            
            # Add all other non-empty columns to metadata
            for col in df.columns:
                if col not in ["Lab #", "Lab Name", "VMs Required", "Internet Required?"]:
                    value = clean_text(row.get(col, ""))
                    if value:  # Only add non-empty values
                        record["metadata"][col] = value
            
            records.append(record)
        
        logger.info(f"Processed {len(records)} records from lab tracker")
        return records
    except Exception as e:
        logger.error(f"Error processing lab tracker file: {e}")
        return []

def process_course_export(file_path: Path) -> List[Dict[str, Any]]:
    """Process the infosec learning content export CSV file."""
    try:
        logger.info(f"Processing course export file: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='warn')
        
        # Clean column names
        df.columns = [col.strip() if isinstance(col, str) else str(col) for col in df.columns]
        
        records = []
        for _, row in df.iterrows():
            # Create a clean record with only non-empty fields
            record = {
                "source": "course_export",
                "source_file": file_path.name,  # Add original filename
                "title": clean_text(row.get("Title", "")),
                "content_type": clean_text(row.get("Content type", "")),
                "status": clean_text(row.get("Status", "")),
                "last_updated": clean_text(row.get("Updated", "")),
                "metadata": {}
            }
            
            # Add all other non-empty columns to metadata
            for col in df.columns:
                if col not in ["Title", "Content type", "Status", "Updated"]:
                    value = clean_text(row.get(col, ""))
                    if value:  # Only add non-empty values
                        record["metadata"][col] = value
            
            records.append(record)
        
        logger.info(f"Processed {len(records)} records from course export")
        return records
    except Exception as e:
        logger.error(f"Error processing course export file: {e}")
        return []

def create_embeddings(records: List[Dict[str, Any]], client: OpenAI) -> List[Dict[str, Any]]:
    """Create embeddings for the records."""
    logger.info(f"Creating embeddings for {len(records)} records")
    
    # Prepare text for embedding
    texts_to_embed = []
    for record in records:
        # Create a meaningful text representation of the record
        text_parts = [
            f"Title: {record.get('title', '')}",
            f"Content Type: {record.get('content_type', '')}",
            f"Source: {record.get('source', '')}",
            f"Status: {record.get('status', '')}",
            f"Last Updated: {record.get('last_updated', '')}",
            f"Lab ID: {record.get('lab_id', '')}",
            f"VMs Required: {record.get('vms_required', '')}",
            f"Internet Required: {record.get('internet_required', '')}",
            "Metadata: " + ", ".join(f"{k}: {v}" for k, v in record.get('metadata', {}).items())
        ]
        text = "\n".join(part for part in text_parts if part and not part.endswith(": ") and not part.endswith(":"))
        
        # Chunk the text if it's too long
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            texts_to_embed.append({
                "record": record,
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
    
    # Batch process texts to create embeddings
    batch_size = 100  # Adjust based on rate limits
    embedded_records = []
    
    for i in range(0, len(texts_to_embed), batch_size):
        batch = texts_to_embed[i:i + batch_size]
        batch_texts = [item["text"] for item in batch]
        
        try:
            response = client.embeddings.create(
                input=batch_texts,
                model=EMBEDDING_MODEL
            )
            
            # Combine embeddings with record data
            for j, embedding in enumerate(response.data):
                record_data = batch[j]["record"].copy()
                record_data.update({
                    "text": batch[j]["text"],
                    "embedding": embedding.embedding,
                    "chunk_index": batch[j]["chunk_index"],
                    "total_chunks": batch[j]["total_chunks"],
                    "model": EMBEDDING_MODEL,
                    "created_at": datetime.utcnow().isoformat()
                })
                embedded_records.append(record_data)
                
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts_to_embed)-1)//batch_size + 1}")
            
        except Exception as e:
            logger.error(f"Error creating embeddings for batch {i//batch_size + 1}: {e}")
    
    return embedded_records

def save_to_jsonl(records: List[Dict[str, Any]], output_file: Path) -> None:
    """Save records to a JSONL file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(records)} records to {output_file}")
    except Exception as e:
        logger.error(f"Error saving to {output_file}: {e}")

def main():
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Process files
    lab_tracker_path = Path("Courses/Constellation Lab Tracker(Conversion Tracker) (2).csv")
    course_export_path = Path("Courses/infosec_learning-content_export-2025-05-19t07-07-04.csv")
    
    # Process records
    lab_records = process_lab_tracker(lab_tracker_path)
    course_records = process_course_export(course_export_path)
    
    # Combine records
    all_records = lab_records + course_records
    
    # Create embeddings
    embedded_records = create_embeddings(all_records, client)
    
    # Save to JSONL file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"openai_vectors_{timestamp}.jsonl"
    save_to_jsonl(embedded_records, output_file)
    
    logger.info(f"Processing complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()

import pymongo
import re
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
from striprtf.striprtf import rtf_to_text

# Load environment variables
load_dotenv()

def convert_rtf_to_text(rtf_path):
    """Convert RTF file to plain text using striprtf"""
    try:
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            rtf_content = f.read()
        text = rtf_to_text(rtf_content)
        return text
    except Exception as e:
        print(f"Error converting RTF: {e}")
        return ""

def extract_questions(text: str) -> List[Dict[str, Any]]:
    """Extract questions with their possible answers from the text"""
    # Split into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    questions = []
    current_question = ""
    current_options = []
    question_number = 0
    
    for line in lines:
        # Look for numbered questions (e.g., "1.", "2.", etc.)
        if re.match(r'^\d+\.', line):
            # Save previous question if exists
            if current_question:
                questions.append({
                    'number': question_number,
                    'question': clean_question_text(current_question),
                    'options': current_options.copy()
                })
                current_options = []
            
            # Start new question
            question_number = int(re.match(r'^(\d+)\.', line).group(1))
            current_question = line
        # Look for checkboxes (options)
        elif '\u9745' in line or '☐' in line or line.strip().startswith('-'):
            option = re.sub(r'^[\s☐\-•*]+', '', line).strip()
            option = re.sub(r'\s+', ' ', option)  # Normalize spaces
            if option:  # Only add non-empty options
                current_options.append(option)
        elif current_question:  # Continue current question
            current_question += " " + line
    
    # Add the last question
    if current_question:
        questions.append({
            'number': question_number,
            'question': clean_question_text(current_question),
            'options': current_options
        })
    
    return questions

def clean_question_text(question: str) -> str:
    """Clean up question text"""
    # Remove leading number and any special characters
    question = re.sub(r'^\d+\.\s*', '', question)
    # Remove any example text in italics
    question = re.sub(r'\*.*?\*', '', question)
    # Remove any text after ':' if it's just an example
    question = re.sub(r':\s*e\.g\..*$', '', question, flags=re.IGNORECASE)
    # Remove any text in parentheses that's just an example
    question = re.sub(r'\s*\(e\.g\..*?\)', '', question, flags=re.IGNORECASE)
    # Normalize whitespace
    question = re.sub(r'\s+', ' ', question).strip()
    return question

def import_to_mongodb(questions: List[Dict[str, Any]]) -> bool:
    """Import questions with options to MongoDB"""
    try:
        # Connect to MongoDB
        connection_string = os.getenv("MONGODB_URI")
        client = pymongo.MongoClient(connection_string)
        db = client.get_database("Product_Intake")
        
        # Clear existing questions
        db.aci_questionnaire.delete_many({})
        
        # Insert new questions with options
        question_docs = []
        for q in questions:
            # Determine question type based on options
            q_type = "multiple_choice" if q['options'] else "text"
            
            question_docs.append({
                "order": q['number'],
                "question": q['question'],
                "options": q['options'],
                "type": q_type,
                "category": "ACI Intake"
            })
        
        # Sort by question number before inserting
        question_docs.sort(key=lambda x: x['order'])
        
        # Insert all questions
        if question_docs:
            result = db.aci_questionnaire.insert_many(question_docs)
            print(f"✅ Successfully imported {len(result.inserted_ids)} questions")
            
            # Verify
            count = db.aci_questionnaire.count_documents({})
            print(f"📊 Total questions in database: {count}")
            
            # Print sample of imported data
            print("\n📋 Sample questions:")
            for q in db.aci_questionnaire.find().sort("order", 1).limit(3):
                print(f"\n{q['order']}. {q['question']}")
                if q['options']:
                    print(f"   Options: {', '.join(q['options'][:3])}..." if len(q['options']) > 3 
                          else f"   Options: {', '.join(q['options'])}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error importing to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    rtf_path = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/ACI-INTAKE-QUESTIONAIRE.rtf"
    
    print("🔍 Converting RTF to text...")
    text = convert_rtf_to_text(rtf_path)
    
    if not text:
        print("❌ Failed to convert RTF file")
        return
    
    print("📝 Extracting questions and options...")
    questions = extract_questions(text)
    
    if not questions:
        print("❌ No questions found in the document")
        return
    
    print(f"✅ Found {len(questions)} questions with options")
    
    # Print sample of extracted data
    print("\n📋 Sample extracted questions:")
    for q in questions[:3]:
        print(f"\n{q['number']}. {q['question']}")
        if q['options']:
            print(f"   Options: {', '.join(q['options'][:3])}..." if len(q['options']) > 3 
                  else f"   Options: {', '.join(q['options'])}")
    
    print("\n💾 Importing to MongoDB...")
    if import_to_mongodb(questions):
        print("\n🎉 Import completed successfully!")
    else:
        print("\n❌ Import failed")

if __name__ == "__main__":
    main()

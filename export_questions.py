import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client.get_database("Product_Intake")
question_collection = db.aci_questionnaire

# Export questions to a JSON file
def export_questions():
    # Get all questions, sorted by order
    questions = list(question_collection.find().sort("order", 1))
    
    # Convert ObjectId to string for JSON serialization
    for q in questions:
        q['_id'] = str(q['_id'])
    
    # Write to file
    with open('questions_export.json', 'w') as f:
        json.dump(questions, f, indent=2)
    
    print(f"Exported {len(questions)} questions to questions_export.json")

if __name__ == "__main__":
    export_questions()

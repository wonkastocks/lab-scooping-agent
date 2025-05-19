from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client.get_database("Product_Intake")
question_collection = db.aci_questionnaire

# List of question IDs or keywords that should have an "Other" option
questions_needing_other = [
    "lab environment",
    "network requirements",
    "storage requirements",
    "security requirements",
    "specific software"
]

def update_questions():
    """Update questions to include the 'has_other' flag where needed."""
    # Get all questions
    questions = list(question_collection.find({}))
    updated_count = 0
    
    for question in questions:
        # Check if this question should have an "Other" option
        needs_other = any(keyword in question["question"].lower() for keyword in questions_needing_other)
        
        if needs_other and not question.get("has_other", False):
            # Update the question to include the has_other flag
            question_collection.update_one(
                {"_id": question["_id"]},
                {"$set": {"has_other": True}}
            )
            print(f"Updated question: {question['question']}")
            updated_count += 1
    
    return updated_count

if __name__ == "__main__":
    print("Updating questions with 'Other' option...")
    count = update_questions()
    print(f"Updated {count} questions with 'Other' option")

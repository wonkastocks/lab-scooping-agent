from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB
try:
    connection_string = os.getenv("MONGODB_URI")
    client = MongoClient(connection_string)
    db = client.get_database("Product_Intake")
    
    # Count questions in questionnaire_questions collection
    question_count = db.questionnaire_questions.count_documents({})
    print(f"Number of questions in database: {question_count}")
    
    # Print all questions
    print("\nList of questions:")
    for i, q in enumerate(db.questionnaire_questions.find().sort("order", 1), 1):
        print(f"{i}. {q.get('question', 'No question text')}")
        
except Exception as e:
    print(f"Error: {e}")

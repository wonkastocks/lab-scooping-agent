from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("Product_Intake")
question_collection = db.aci_questionnaire

# Get all questions
questions = list(question_collection.find().sort("order", 1))

# Print question structure
for i, q in enumerate(questions, 1):
    print(f"\nQuestion {i}:")
    print(f"Text: {q['question']}")
    print(f"Type: {q['type']}")
    print(f"Options: {q.get('options', 'No options')}")
    print(f"Has Other: {q.get('has_other', False)}")
    print("-" * 50)

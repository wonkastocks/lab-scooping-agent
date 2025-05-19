from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("Product_Intake")

# Get question 3
question = db.aci_questionnaire.find_one({"order": 3})

if question:
    print(f"Question 3:")
    print(f"ID: {question['_id']}")
    print(f"Type: {question.get('type', 'Not specified')}")
    print(f"Question: {question['question']}")
    print(f"Options: {question.get('options', 'No options')}")
    print(f"Has Other: {question.get('has_other', False)}")
    print(f"All fields: {list(question.keys())}")
else:
    print("Question 3 not found")

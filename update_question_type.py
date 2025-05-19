from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("Product_Intake")

# Update question 3 to use "select" type instead of "multiple_choice"
result = db.aci_questionnaire.update_one(
    {"order": 3},
    {"$set": {"type": "select"}}
)

if result.modified_count > 0:
    print("Successfully updated question 3 to use 'select' type")
else:
    print("No changes were made. Question 3 may already be of type 'select' or doesn't exist.")

# Verify the change
question = db.aci_questionnaire.find_one({"order": 3})
if question:
    print(f"\nQuestion 3 type is now: {question['type']}")
    print(f"Question: {question['question']}")
    print(f"Options: {question.get('options', [])}")

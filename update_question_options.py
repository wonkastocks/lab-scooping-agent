from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_database("Product_Intake")
question_collection = db.aci_questionnaire

# Define question options based on the RTF document
question_options = {
    # Question 9: How many nodes (virtual machines) per lab?
    9: {
        "type": "multiple_choice",
        "options": [
            "Stand-Alone",
            "2 Nodes",
            "3 Nodes",
            "5 Nodes",
            "10+ Nodes",
            "Other"
        ],
        "has_other": True
    },
    # Question 10: What is the typical duration of lab access for each student?
    10: {
        "type": "multiple_choice",
        "options": [
            "3 Months (Half-Semester)",
            "6 Months (Full Semester)",
            "1 Year",
            "2 Years",
            "Unlimited",
            "Other"
        ],
        "has_other": True
    },
    # Question 11: How long should each lab session last?
    11: {
        "type": "multiple_choice",
        "options": [
            "1 Hour",
            "2 Hours",
            "4 Hours",
            "8 Hours",
            "Other"
        ],
        "has_other": True
    }
}

# Update questions in the database
for order, updates in question_options.items():
    question_collection.update_one(
        {"order": order},
        {"$set": updates}
    )
    print(f"Updated question {order} with options")

print("Question options updated successfully!")

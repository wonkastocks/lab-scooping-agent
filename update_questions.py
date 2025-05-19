from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Questions from the questionnaire
questions = [
    "Organization Name",
    "Primary Contact Name & Email",
    "Who is this lab being built for? (University/College, Technical/Trade School, Non-Profit, Government, Private Business, Independent Instructor, Individual Learner, Other)",
    "Briefly describe your organization's mission or educational goal for this lab",
    "What is the title of the lab?",
    "Briefly describe the purpose or learning objective of the lab",
    "How many labs will you need for this lab series?",
    "Estimated total number of virtual systems across all labs",
    "How many nodes (virtual machines) per lab?",
    "Should lab environments be persistent or reset each time?",
    "How long should students have access to the lab?",
    "How long is a typical lab session?",
    "What is the intended complexity of the lab?",
    "Do you require any specialized infrastructure?",
    "How many subnets are needed within each lab?",
    "Do students need internet access in the lab?",
    "Do you require specialized networking? (VLANs, RDP, VPN, Firewall, etc.)",
    "Is this a Server/Client or Peer-to-Peer setup?",
    "Is Active Directory required?",
    "Any specific services required on networked systems? (e.g., FileShares, SSH, Webservers, Databases)",
    "What operating systems are required?",
    "What specific software applications are needed?",
    "Are there any specific software versions required?",
    "Do you need any development environments or IDEs?",
    "Are there any specific programming languages or frameworks needed?",
    "What are the minimum system requirements for each VM?",
    "Do you need any pre-installed datasets or sample code?",
    "Are there any specific browser requirements?",
    "Do you need any browser extensions or plugins?",
    "What type of assessment will be used? (Quizzes, Practical Tasks, etc.)",
    "Do you need automated grading?",
    "What type of feedback should be provided to students?",
    "Should there be hints or solution guides?",
    "What type of progress tracking is needed?",
    "What security measures need to be in place?",
    "How should user authentication be handled?",
    "What backup and recovery options are needed?",
    "What compliance standards must be met?",
    "What is your timeline for implementation?",
    "What is your budget for this project?"
]

try:
    # Connect to MongoDB
    connection_string = os.getenv("MONGODB_URI")
    client = MongoClient(connection_string)
    db = client.get_database("Product_Intake")
    
    # Clear existing questions
    db.questionnaire_questions.delete_many({})
    
    # Insert all questions with order
    question_docs = [
        {"order": i+1, "question": q, "type": "text"} 
        for i, q in enumerate(questions)
    ]
    
    result = db.questionnaire_questions.insert_many(question_docs)
    print(f"Successfully inserted {len(result.inserted_ids)} questions")
    
    # Verify count
    count = db.questionnaire_questions.count_documents({})
    print(f"Total questions in database: {count}")
    
except Exception as e:
    print(f"Error: {e}")

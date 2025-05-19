import pymongo
from dotenv import load_dotenv
import os
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Manually defined questions and options based on the RTF file
QUESTIONNAIRE = [
    {
        "order": 1,
        "question": "Organization Name",
        "type": "text",
        "options": []
    },
    {
        "order": 2,
        "question": "Primary Contact Name & Email",
        "type": "text",
        "options": []
    },
    {
        "order": 3,
        "question": "Who is this lab being built for?",
        "type": "multiple_choice",
        "options": [
            "University / College",
            "Technical or Trade School",
            "Non-Profit Organization",
            "Government Agency",
            "Private Business / Corporation",
            "Independent Instructor / Consultant",
            "Individual Learner / Certification Prep",
            "Other (please specify)"
        ]
    },
    {
        "order": 4,
        "question": "Briefly describe your organization's mission or educational goal for this lab",
        "type": "long_text",
        "options": []
    },
    {
        "order": 5,
        "question": "What is the title of the lab?",
        "type": "text",
        "options": []
    },
    {
        "order": 6,
        "question": "Briefly describe the purpose or learning objective of the lab",
        "type": "long_text",
        "options": []
    },
    {
        "order": 7,
        "question": "How many labs will you need for this lab series?",
        "type": "number",
        "options": []
    },
    {
        "order": 8,
        "question": "Estimated total number of virtual systems across all labs",
        "type": "number",
        "options": []
    },
    {
        "order": 9,
        "question": "How many nodes (virtual machines) per lab?",
        "type": "number",
        "options": []
    },
    {
        "order": 10,
        "question": "Should lab environments be persistent or reset each time?",
        "type": "multiple_choice",
        "options": [
            "Persistent (save student work between sessions)",
            "Reset each time (fresh environment for each session)",
            "Configurable (some labs persistent, some reset)"
        ]
    },
    {
        "order": 11,
        "question": "How long should students have access to the lab?",
        "type": "multiple_choice",
        "options": [
            "1-4 hours per session",
            "1-7 days total",
            "1-4 weeks total",
            "Entire semester/term",
            "Other (please specify)"
        ]
    },
    {
        "order": 12,
        "question": "What is the intended complexity of the lab?",
        "type": "multiple_choice",
        "options": [
            "Beginner (introductory concepts)",
            "Intermediate (some technical knowledge required)",
            "Advanced (experienced users)",
            "Mixed (varies by lab)"
        ]
    },
    {
        "order": 13,
        "question": "Do you require any specialized infrastructure?",
        "type": "multiple_choice",
        "options": [
            "GPU acceleration",
            "High memory requirements",
            "High CPU requirements",
            "Specialized hardware",
            "No special requirements"
        ]
    },
    {
        "order": 14,
        "question": "How many subnets are needed within each lab?",
        "type": "number",
        "options": []
    },
    {
        "order": 15,
        "question": "Do students need internet access in the lab?",
        "type": "multiple_choice",
        "options": [
            "Yes, full internet access",
            "Yes, but restricted to specific domains",
            "No internet access required"
        ]
    },
    {
        "order": 16,
        "question": "Do you require specialized networking?",
        "type": "multiple_choice",
        "options": [
            "VLANs",
            "RDP access",
            "VPN connectivity",
            "Firewall configuration",
            "Load balancing",
            "None of the above"
        ]
    },
    {
        "order": 17,
        "question": "Is this a Server/Client or Peer-to-Peer setup?",
        "type": "multiple_choice",
        "options": [
            "Server/Client",
            "Peer-to-Peer",
            "Both",
            "Not applicable"
        ]
    },
    {
        "order": 18,
        "question": "Is Active Directory required?",
        "type": "multiple_choice",
        "options": [
            "Yes, Windows Active Directory",
            "Yes, OpenLDAP or similar",
            "No directory service required"
        ]
    },
    {
        "order": 19,
        "question": "Any specific services required on networked systems?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "File Shares (e.g., SMB/NFS)",
            "SSH Access",
            "Web Servers (e.g., Apache, Nginx, IIS)",
            "Databases (e.g., MySQL, MSSQL, PostgreSQL)",
            "Email Services",
            "DNS Services",
            "DHCP Services",
            "Other (please specify)"
        ]
    },
    {
        "order": 20,
        "question": "What operating systems are required?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Windows 10/11",
            "Windows Server 2016/2019/2022",
            "Ubuntu Linux",
            "CentOS/RHEL",
            "Kali Linux",
            "macOS",
            "Other (please specify)"
        ]
    },
    {
        "order": 21,
        "question": "What specific software applications are needed?",
        "type": "long_text",
        "options": []
    },
    {
        "order": 22,
        "question": "Are there any specific software versions required?",
        "type": "long_text",
        "options": []
    },
    {
        "order": 23,
        "question": "Do you need any development environments or IDEs?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Visual Studio Code",
            "Visual Studio",
            "Eclipse",
            "IntelliJ IDEA",
            "PyCharm",
            "Other (please specify)"
        ]
    },
    {
        "order": 24,
        "question": "Are there any specific programming languages or frameworks needed?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Python",
            "Java",
            "JavaScript/Node.js",
            ".NET/C#",
            "PHP",
            "Ruby",
            "Go",
            "Other (please specify)"
        ]
    },
    {
        "order": 25,
        "question": "What are the minimum system requirements for each VM?",
        "type": "long_text",
        "options": []
    },
    {
        "order": 26,
        "question": "Do you need any pre-installed datasets or sample code?",
        "type": "multiple_choice",
        "options": [
            "Yes, please specify below",
            "No, we'll provide our own",
            "Not sure yet"
        ]
    },
    {
        "order": 27,
        "question": "Are there any specific browser requirements?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Chrome",
            "Firefox",
            "Safari",
            "Edge",
            "Specific version required (please specify)"
        ]
    },
    {
        "order": 28,
        "question": "Do you need any browser extensions or plugins?",
        "type": "long_text",
        "options": []
    },
    {
        "order": 29,
        "question": "What type of assessment will be used?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Quizzes",
            "Practical Tasks",
            "Written Assignments",
            "Projects",
            "Exams",
            "Other (please specify)"
        ]
    },
    {
        "order": 30,
        "question": "Do you need automated grading?",
        "type": "multiple_choice",
        "options": [
            "Yes, fully automated",
            "Partially automated with manual review",
            "Fully manual grading",
            "Not sure"
        ]
    },
    {
        "order": 31,
        "question": "What type of feedback should be provided to students?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Immediate automated feedback",
            "Instructor feedback",
            "Peer feedback",
            "Rubric-based scoring",
            "Other (please specify)"
        ]
    },
    {
        "order": 32,
        "question": "Should there be hints or solution guides?",
        "type": "multiple_choice",
        "options": [
            "Yes, provide hints and solutions",
            "Hints only, no solutions",
            "No hints or solutions"
        ]
    },
    {
        "order": 33,
        "question": "What type of progress tracking is needed?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "Completion tracking",
            "Time spent on tasks",
            "Score/grade tracking",
            "Activity logging",
            "Other (please specify)"
        ]
    },
    {
        "order": 34,
        "question": "What security measures need to be in place?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "User authentication",
            "Data encryption",
            "Network isolation",
            "Audit logging",
            "Other (please specify)"
        ]
    },
    {
        "order": 35,
        "question": "How should user authentication be handled?",
        "type": "multiple_choice",
        "options": [
            "Local accounts",
            "LDAP/Active Directory",
            "OAuth (Google, Microsoft, etc.)",
            "SAML/SSO",
            "Other (please specify)"
        ]
    },
    {
        "order": 36,
        "question": "What backup and recovery options are needed?",
        "type": "multiple_choice",
        "options": [
            "Automatic daily backups",
            "Manual backup capability",
            "No backup needed",
            "Not sure"
        ]
    },
    {
        "order": 37,
        "question": "What compliance standards must be met?",
        "type": "multiple_choice",
        "multiple": True,
        "options": [
            "FERPA",
            "HIPAA",
            "GDPR",
            "PCI DSS",
            "Other (please specify)",
            "No specific compliance requirements"
        ]
    },
    {
        "order": 38,
        "question": "What is your timeline for implementation?",
        "type": "multiple_choice",
        "options": [
            "Immediate (ASAP)",
            "1-2 weeks",
            "1-3 months",
            "3-6 months",
            "6+ months"
        ]
    },
    {
        "order": 39,
        "question": "What is your budget for this project?",
        "type": "multiple_choice",
        "options": [
            "Under $5,000",
            "$5,000 - $10,000",
            "$10,000 - $25,000",
            "$25,000 - $50,000",
            "$50,000+",
            "To be determined"
        ]
    },
    {
        "order": 40,
        "question": "Is there anything else we should know about your requirements?",
        "type": "long_text",
        "options": []
    }
]

def import_to_mongodb() -> bool:
    """Import questions with options to MongoDB"""
    try:
        # Connect to MongoDB
        connection_string = os.getenv("MONGODB_URI")
        client = pymongo.MongoClient(connection_string)
        db = client.get_database("Product_Intake")
        
        # Clear existing questions
        db.aci_questionnaire.delete_many({})
        
        # Insert new questions
        result = db.aci_questionnaire.insert_many(QUESTIONNAIRE)
        print(f"✅ Successfully imported {len(result.inserted_ids)} questions")
        
        # Verify
        count = db.aci_questionnaire.count_documents({})
        print(f"📊 Total questions in database: {count}")
        
        # Print sample of imported data
        print("\n📋 Sample questions:")
        for q in db.aci_questionnaire.find().sort("order", 1).limit(5):
            print(f"\n{q['order']}. {q['question']}")
            if q.get('options'):
                print(f"   Type: {q['type']}")
                if q['options']:
                    print(f"   Options: {', '.join(q['options'][:3])}..." if len(q['options']) > 3 
                          else f"   Options: {', '.join(q['options'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting questionnaire import...")
    if import_to_mongodb():
        print("\n🎉 Import completed successfully!")
    else:
        print("\n❌ Import failed")

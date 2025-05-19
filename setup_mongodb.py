import json
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List, Dict, Any
from datetime import datetime

class MongoDBImporter:
    def __init__(self, db_name: str = "Product_Intake", connection_string: str = None):
        """Initialize MongoDB connection."""
        if not connection_string:
            raise ValueError("MongoDB connection string is required. Please set MONGODB_URI environment variable.")
        
        # Connect to MongoDB Atlas
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client.get_database(db_name)
            
            # Test the connection
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB Atlas")
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB Atlas: {e}")
            raise
    
    def setup_collections(self):
        """Create necessary collections with indexes."""
        collections = {
            'labs': [
                ('title', ASCENDING),
                ('content_type', ASCENDING),
                ('categories', ASCENDING)
            ],
            'categories': [('name', ASCENDING)],
            'questionnaire_questions': [('order', ASCENDING)],
            'user_responses': [('timestamp', DESCENDING)],
            'recommendations': [('user_id', ASCENDING)]
        }
        
        for collection_name, indexes in collections.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
                
                # Create indexes
                for field, order in indexes:
                    self.db[collection_name].create_index([(field, order)])
                    print(f"   - Created index on {field}")
    
    def import_labs_from_json(self, json_file_path: str):
        """Import labs from JSON file."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                labs = json.load(f)
            
            # Transform data for better querying
            processed_labs = []
            for lab in labs:
                # Extract categories from title (simplified example)
                categories = self._extract_categories(lab.get('Title', ''))
                
                processed_lab = {
                    'title': lab.get('Title', 'Untitled'),
                    'content_type': lab.get('Content type', 'Lab'),
                    'email': lab.get('Email', ''),
                    'status': lab.get('Status', ''),
                    'updated': lab.get('Updated', ''),
                    'last_enrollment': lab.get('Last Enrollment', ''),
                    'categories': categories,
                    'metadata': {
                        'net_price': lab.get('Net Price', ''),
                        'net_price_interval': lab.get('Net Price Interval', ''),
                        'list_prices': [
                            {'price': lab.get(f'List Price #{i}', ''), 
                             'interval': lab.get(f'List Price Interval #{i}', '')}
                            for i in range(1, 4)
                        ]
                    },
                    'imported_at': datetime.utcnow()
                }
                processed_labs.append(processed_lab)
            
            # Insert into MongoDB
            if processed_labs:
                result = self.db.labs.insert_many(processed_labs)
                print(f"✅ Imported {len(result.inserted_ids)} labs")
                
                # Update categories collection
                self._update_categories(processed_labs)
                
        except Exception as e:
            print(f"❌ Error importing labs: {str(e)}")
    
    def _extract_categories(self, title: str) -> List[str]:
        """Extract categories from lab title."""
        # This is a simplified example - you might want to enhance this
        categories = []
        title_lower = title.lower()
        
        # Map keywords to categories
        category_keywords = {
            'security': ['security', 'cyber', 'hack', 'attack', 'defense', 'threat', 'vulnerability', 'penetration'],
            'networking': ['network', 'tcp/ip', 'subnet', 'vlan', 'router', 'switch', 'firewall', 'dns', 'dhcp'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'amazon', 'microsoft', 'google', 's3', 'ec2', 'lambda'],
            'linux': ['linux', 'ubuntu', 'debian', 'centos', 'redhat', 'bash', 'shell', 'kernel', 'unix'],
            'windows': ['windows', 'active directory', 'ad', 'powershell', 'iis', 'server', 'microsoft'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                categories.append(category)
        
        return list(set(categories)) or ['uncategorized']
    
    def _update_categories(self, labs: List[Dict[str, Any]]):
        """Update categories collection based on labs."""
        # Get all unique categories from labs
        all_categories = set()
        for lab in labs:
            all_categories.update(lab.get('categories', []))
        
        # Update categories collection
        for category in all_categories:
            self.db.categories.update_one(
                {'name': category},
                {'$setOnInsert': {'created_at': datetime.utcnow()}},
                upsert=True
            )
        print(f"✅ Updated {len(all_categories)} categories")
    
    def setup_questionnaire(self):
        """Set up sample questionnaire questions."""
        questions = [
            {
                'question': 'What is your primary area of interest?',
                'field': 'primary_interest',
                'type': 'single_choice',
                'options': ['Security', 'Networking', 'Cloud', 'Programming', 'Data'],
                'order': 1
            },
            {
                'question': 'What is your skill level?',
                'field': 'skill_level',
                'type': 'single_choice',
                'options': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
                'order': 2
            },
            {
                'question': 'Which technologies are you interested in?',
                'field': 'technologies',
                'type': 'multi_choice',
                'options': ['Linux', 'Windows', 'AWS', 'Azure', 'Docker', 'Kubernetes', 'Python', 'JavaScript'],
                'order': 3
            },
            {
                'question': 'What is your goal?',
                'field': 'goal',
                'type': 'single_choice',
                'options': ['Certification', 'Career Advancement', 'Skill Development', 'Project Work'],
                'order': 4
            }
        ]
        
        # Clear existing questions
        self.db.questionnaire_questions.delete_many({})
        
        # Insert new questions
        self.db.questionnaire_questions.insert_many(questions)
        print(f"✅ Set up {len(questions)} questionnaire questions")

def main():
    # Get MongoDB connection string from environment variable
    connection_string = os.getenv('MONGODB_URI')
    if not connection_string:
        print("❌ MONGODB_URI environment variable is not set")
        print("Please set your MongoDB Atlas connection string as follows:")
        print("export MONGODB_URI='your_connection_string_here'")
        return
    
    # Initialize MongoDB connection
    try:
        mongo = MongoDBImporter(connection_string=connection_string)
    except Exception as e:
        print(f"❌ Failed to initialize MongoDB connection: {e}")
        return
    
    # Set up collections
    print("\nSetting up collections...")
    mongo.setup_collections()
    
    # Import labs
    print("\nImporting labs...")
    json_file = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/infosec_learning-content_export-2025-05-19t07-07-04.json"
    mongo.import_labs_from_json(json_file)
    
    # Set up questionnaire
    print("\nSetting up questionnaire...")
    mongo.setup_questionnaire()
    
    print("\n✅ Setup completed successfully!")

if __name__ == "__main__":
    main()

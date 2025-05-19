import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

def clean_title(title: str) -> str:
    """Clean and normalize the title text."""
    if not title:
        return ""
    # Convert to lowercase and remove special characters
    title = re.sub(r'[^\w\s-]', ' ', title.lower())
    # Replace multiple spaces with single space
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def extract_keywords(title: str, min_length: int = 4) -> List[str]:
    """Extract meaningful keywords from a title."""
    # Common words to exclude
    stop_words = {
        'with', 'using', 'from', 'this', 'that', 'these', 'those', 'then', 'than',
        'they', 'them', 'their', 'there', 'when', 'where', 'what', 'which', 'who',
        'whom', 'have', 'has', 'had', 'for', 'and', 'not', 'but', 'the', 'a', 'an',
        'lab', 'labs', 'guide', 'exercise', 'exercises', 'introduction', 'overview'
    }
    
    words = title.split()
    # Filter out short words and stop words
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    return keywords

def analyze_titles_by_type(data: List[dict]) -> Dict[str, Counter]:
    """Analyze titles by content type."""
    type_keywords = defaultdict(Counter)
    
    for item in data:
        content_type = item.get('Content type', 'unknown')
        title = item.get('Title', '')
        
        if not title:
            continue
            
        clean_t = clean_title(title)
        keywords = extract_keywords(clean_t)
        
        # Count keywords for this content type
        type_keywords[content_type].update(keywords)
    
    return type_keywords

def find_common_keywords(keyword_counts: Dict[str, Counter], top_n: int = 20) -> Dict[str, List[Tuple[str, int]]]:
    """Find the most common keywords for each content type."""
    return {
        content_type: counter.most_common(top_n)
        for content_type, counter in keyword_counts.items()
    }

def categorize_labs_by_keywords(data: List[dict], keyword_categories: Dict[str, List[str]]) -> Dict[str, List[dict]]:
    """Categorize labs based on keywords in their titles."""
    categorized = {category: [] for category in keyword_categories}
    categorized['other'] = []
    
    for item in data:
        title = item.get('Title', '').lower()
        matched = False
        
        for category, keywords in keyword_categories.items():
            if any(keyword.lower() in title for keyword in keywords):
                categorized[category].append(item)
                matched = True
                break
                
        if not matched:
            categorized['other'].append(item)
    
    return categorized

def save_keyword_analysis(common_keywords: Dict[str, List[Tuple[str, int]]], 
                         output_file: str) -> None:
    """Save the keyword analysis to a markdown file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Lab Title Keyword Analysis\n\n")
        
        for content_type, keywords in common_keywords.items():
            f.write(f"## {content_type} Labs\n\n")
            f.write(f"Top 20 most common keywords in {content_type} titles:\n\n")
            
            for word, count in keywords:
                f.write(f"- `{word}`: {count} occurrences\n")
            
            f.write("\n---\n\n")

def save_categorized_labs(categorized: Dict[str, List[dict]], 
                         output_file: str) -> None:
    """Save categorized labs to a markdown file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Categorized Labs\n\n")
        
        for category, items in categorized.items():
            f.write(f"## {category.capitalize()} ({len(items)} labs)\n\n")
            
            for item in items[:50]:  # Limit to first 50 items per category
                title = item.get('Title', 'Untitled')
                content_type = item.get('Content type', 'N/A')
                f.write(f"- **{title}** (*{content_type}*)\n")
            
            if len(items) > 50:
                f.write(f"- ... and {len(items) - 50} more\n")
                
            f.write("\n---\n\n")

def main():
    # Define file paths
    input_json = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/infosec_learning-content_export-2025-05-19t07-07-04.json"
    keywords_output = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/lab_keywords_analysis.md"
    categories_output = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/lab_categories_analysis.md"
    
    # Load the data
    print("Loading data...")
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. Analyze keywords in titles
    print("Analyzing keywords...")
    type_keywords = analyze_titles_by_type(data)
    common_keywords = find_common_keywords(type_keywords)
    save_keyword_analysis(common_keywords, keywords_output)
    
    # 2. Categorize labs by keywords
    print("Categorizing labs...")
    keyword_categories = {
        'security': ['security', 'cyber', 'hack', 'attack', 'defense', 'threat', 'vulnerability', 'penetration', 'pentest', 'malware'],
        'networking': ['network', 'tcp/ip', 'subnet', 'vlan', 'router', 'switch', 'firewall', 'dns', 'dhcp', 'vpn'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud', 'amazon', 'microsoft', 'google', 's3', 'ec2', 'lambda'],
        'linux': ['linux', 'ubuntu', 'debian', 'centos', 'redhat', 'bash', 'shell', 'kernel', 'unix'],
        'windows': ['windows', 'active directory', 'ad', 'powershell', 'iis', 'server', 'microsoft'],
        'programming': ['python', 'java', 'javascript', 'c++', 'programming', 'script', 'api', 'json', 'xml'],
        'certification': ['comptia', 'a+', 'network+', 'security+', 'cyber', 'cissp', 'ceh', 'cism', 'ccna', 'ccnp'],
        'data': ['database', 'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'data', 'analytics', 'big data'],
        'devops': ['devops', 'docker', 'kubernetes', 'ci/cd', 'jenkins', 'ansible', 'terraform', 'iac', 'infrastructure as code']
    }
    
    categorized_labs = categorize_labs_by_keywords(data, keyword_categories)
    save_categorized_labs(categorized_labs, categories_output)
    
    print(f"\nAnalysis complete!")
    print(f"- Keyword analysis saved to: {keywords_output}")
    print(f"- Categorized labs saved to: {categories_output}")

if __name__ == "__main__":
    main()

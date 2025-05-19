import json
from collections import Counter

def analyze_lab_types(json_file_path, output_file_path):
    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Extract all content types
    content_types = [item.get('Content type', 'N/A') for item in data]
    
    # Count occurrences of each content type
    type_counts = Counter(content_types)
    
    # Sort by count (descending)
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Generate markdown content
    markdown_content = "# Lab Types Analysis\n\n"
    markdown_content += f"Total labs analyzed: {len(data)}\n\n"
    markdown_content += "## Lab Types and Counts\n\n"
    
    for content_type, count in sorted_types:
        markdown_content += f"- **{content_type}**: {count} labs\n"
    
    # Add a summary of unique lab types
    markdown_content += f"\n## Summary\n\n"
    markdown_content += f"- Total unique lab types: {len(type_counts)}"
    
    # Write to markdown file
    with open(output_file_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)
    
    print(f"Analysis complete. Results written to {output_file_path}")
    return sorted_types

if __name__ == "__main__":
    # Define file paths
    input_json = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/infosec_learning-content_export-2025-05-19t07-07-04.json"
    output_md = "/Users/walterbarr_1/Projects/lab-scooping-agent/MONGO_EXPORT_ORIGINAL_NAMES/lab_types_analysis.md"
    
    # Run the analysis
    analyze_lab_types(input_json, output_md)

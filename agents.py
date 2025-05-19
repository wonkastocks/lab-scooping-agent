from typing import List, Optional
import openai
from openai import OpenAI
import os
import json
import asyncio
from datetime import datetime

class Tool:
    def __init__(self):
        self.name = self.__class__.__name__

    async def run(self, input_text: str) -> str:
        raise NotImplementedError

class WebSearchTool(Tool):
    async def run(self, input_text: str) -> str:
        # Simulate web search with OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a web search tool. Provide relevant information from the web about biblical topics, including scholarly sources and archaeological findings. Include DOIs and permanent URLs where available."},
                {"role": "user", "content": input_text}
            ]
        )
        return response.choices[0].message.content

class KnowledgeBaseTool(Tool):
    def __init__(self, bible_files: Optional[List[str]] = None):
        super().__init__()
        self.bible_files = bible_files or []

    async def run(self, input_text: str) -> str:
        # Use Bible knowledge base with OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Bible knowledge base tool. Search through the provided translations and Strong's Concordance to provide accurate biblical information. Include proper citations for all translations and references."},
                {"role": "user", "content": input_text}
            ]
        )
        return response.choices[0].message.content

class CitationFormatter:
    @staticmethod
    def format_bible_citation(book: str, chapter: int, verse: int, translation: str) -> str:
        return f"{book} {chapter}:{verse} ({translation})"
    
    @staticmethod
    def format_book_citation(author: str, year: int, title: str, publisher: str, doi: Optional[str] = None, url: Optional[str] = None) -> str:
        citation = f"{author} ({year}). {title}. {publisher}."
        if doi:
            citation += f" https://doi.org/{doi}"
        elif url:
            citation += f" {url}"
        return citation

    @staticmethod
    def format_article_citation(author: str, year: int, title: str, journal: str, volume: int, issue: Optional[int], pages: str, doi: Optional[str] = None) -> str:
        citation = f"{author} ({year}). {title}. {journal}, {volume}"
        if issue:
            citation += f"({issue})"
        citation += f", {pages}."
        if doi:
            citation += f" https://doi.org/{doi}"
        return citation

class Agent:
    def __init__(self, name, instructions):
        self.name = name
        self.instructions = instructions
        self.client = OpenAI()
        self.web_search = WebSearchTool()
        self.knowledge_base = KnowledgeBaseTool()
        self.citation_formatter = CitationFormatter()
        self.current_date = datetime.now().strftime("%Y-%m-%d")

    def format_response(self, content: str) -> str:
        """Format the response with proper citations and current date."""
        # Add access date for web resources
        if "[Current Date]" in content:
            content = content.replace("[Current Date]", self.current_date)
        return content

    async def run(self, user_input):
        """Run the agent with the given input"""
        try:
            # Determine which search methods to use based on instructions
            use_web = "Web search is enabled" in self.instructions
            use_kb = "Knowledge Base search is enabled" in self.instructions
            
            # Gather information from enabled tools
            tool_results = []
            
            if use_web:
                web_result = await self.web_search.run(user_input)
                tool_results.append("Web Search Results:\n" + web_result)
                
            if use_kb:
                kb_result = await self.knowledge_base.run(user_input)
                tool_results.append("Bible Knowledge Base Results:\n" + kb_result)
            
            # Combine results with the main query
            combined_input = f"User Query: {user_input}\n\n"
            if tool_results:
                combined_input += "\n\n".join(tool_results)
            
            # Add citation formatting instructions
            citation_instructions = """
            Format your response following these rules:
            1. Use APA 7th Edition format for all citations
            2. Include DOIs or stable URLs for all sources
            3. Provide page numbers for direct quotes
            4. Include access dates for web resources
            5. Format Bible references as: Book Chapter:Verse (Translation)
            6. Add a References section at the end
            7. Include clickable hyperlinks in appropriate format
            8. Add an Additional Resources section with relevant databases
            9. Include a note about citation compliance and source verification
            """
            
            # Get final response
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": self.instructions + citation_instructions},
                    {"role": "user", "content": combined_input}
                ]
            )
            
            # Format the response
            formatted_response = self.format_response(response.choices[0].message.content)
            return formatted_response
            
        except Exception as e:
            return f"Error running agent: {str(e)}"

class Runner:
    @staticmethod
    async def run(agent, input_text):
        """Run an agent with the given input"""
        result = await agent.run(input_text)
        return AgentResult(result)

class AgentResult:
    def __init__(self, final_output):
        self.final_output = final_output 
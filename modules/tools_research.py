import os
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path

# --- PATH FIX: Load .env from Project Root ---
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def search_web(query: str):
    """
    Searches the web using the Tavily API (Optimized for AI Agents).
    Returns a summary of the top 5 results.
    """
    if not TAVILY_API_KEY:
        return "Error: Missing TAVILY_API_KEY in .env file."

    print(f"   [Tavily Search: '{query}']")
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic", # Use 'advanced' for deeper (slower) searches
        "include_answer": True,
        "max_results": 5
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 1. Check for a direct AI answer (Tavily sometimes generates a summary)
        output = []
        if data.get("answer"):
            output.append(f"DIRECT ANSWER: {data['answer']}\n")
            
        # 2. Format the search results
        results = data.get("results", [])
        for result in results:
            title = result.get("title", "No Title")
            url = result.get("url", "No URL")
            content = result.get("content", "No Content")
            output.append(f"Source: {title}\nLink: {url}\nSummary: {content}\n")
            
        return "\n".join(output)

    except Exception as e:
        return f"Tavily Search Error: {e}"

def read_website(url: str):
    """
    Visits a specific URL and extracts the main text content.
    (Kept as a fallback for deep reading specific links).
    """
    try:
        print(f"   [Reading URL: {url}]")
        
        # Fake a browser user-agent
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cleanup
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:5000] # Limit to avoid token overflow
        
    except Exception as e:
        return f"Error reading website: {e}"
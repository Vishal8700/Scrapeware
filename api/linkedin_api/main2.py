from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:3000",  # Add your frontend's URL here
    "https://scrapeware.vercel.app",  # Add any other domains you want to allow
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Get your API key from the environment variable
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

class SearchRequest(BaseModel):
    keywords: str
    location: str

def get_company_name(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 2:
        return path_parts[2].lower()
    return None

def get_search_results(query):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 20  # Fetch up to 20 results to account for duplicates
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        unique_results = {}
        for result in data.get("organic_results", []):
            link = result.get("link")
            if link:
                company_name = get_company_name(link)
                if company_name and company_name not in unique_results:
                    unique_results[company_name] = {
                        "title": result.get("title"),
                        "link": link,
                        "snippet": result.get("snippet")
                    }
        
        return list(unique_results.values())[:15]  # Return up to 15 unique results
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching search results: {str(e)}")

@app.post("/search")
async def search_and_summarize(search_request: SearchRequest):
    try:
        # Prepare the search query
        keywords = [keyword.strip().strip('"') for keyword in search_request.keywords.split(",")]
        keyword_query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        search_query = f'site:linkedin.com/company/ ({keyword_query}) "{search_request.location}"'
        
        results = get_search_results(search_query)

        return {
            "companies": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

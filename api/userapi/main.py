

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",  # Add your frontend's URL here
    "https://your-frontend-domain.com"  # Add more allowed origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


class RoleCompanyRequest(BaseModel):
    role: str
    company_name: str


def clean_text(text):
    return ' '.join(text.split()).strip()


# Function to perform a Google search for a given query
def get_google_search_results(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch search results. Status code: {response.status_code}")

    return response.text


# Function to parse search results and extract profile details
def parse_search_results(html_content, limit=10):
    soup = BeautifulSoup(html_content, 'html.parser')
    profiles = []

    # Fetch all profile containers
    profile_divs = soup.find_all('div', class_='MjjYud')

    for div in profile_divs:
        try:
            # Extract username and LinkedIn URL
            user_info_div = div.find('div', class_='kb0PBd cvP2Ce A9Y9g jGGQ5e')
            profile_link_tag = user_info_div.find('a', href=True)
            linkedin_url = profile_link_tag['href']
            user_name_tag = profile_link_tag.find('h3', class_="LC20lb MBeuO DKV0Md")
            user_name = clean_text(user_name_tag.text)

            # Extract about section
            additional_info_div = div.find('div', class_='kb0PBd cvP2Ce A9Y9g')
            about_section_span = additional_info_div.find('div', class_='VwiC3b yXK7lf lVm3ye r025kc hJNv6b Hdw6tb')
            about_section = clean_text(about_section_span.text) if about_section_span else "About section not found"

            # Store the profile information
            profile_info = {
                "name": user_name,
                "linkedin_url": linkedin_url,
                "about_section": about_section
            }
            profiles.append(profile_info)

            # Break once we have the desired number of profiles
            if len(profiles) >= limit:
                break
        except Exception as e:
            print(f"Error parsing profile: {e}")
            continue

    return profiles


# Route for general LinkedIn profile scraping based on role and company name
@app.post("/scrape_role_profiles")
async def scrape_role_profiles(request: RoleCompanyRequest):
    try:
        # Step 1: Construct Google search query for the given role and company
        search_query = f'site:linkedin.com/in/ "{request.role}" "{request.company_name}"'

        # Step 2: Get Google search results
        search_results_html = get_google_search_results(search_query)

        # Step 3: Parse the results to extract profile details (limit to top 5)
        profiles = parse_search_results(search_results_html, limit=5)

        if not profiles:
            return {"message": f"No profiles found for {request.role} at {request.company_name}"}

        return profiles

    except Exception as e:
        return {"error": str(e)}


# To run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)

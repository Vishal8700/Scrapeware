# import requests
# from bs4 import BeautifulSoup
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import logging
#
# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)
#
# app = FastAPI()
#
# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )
#
# class RoleCompanyRequest(BaseModel):
#     role: str
#     company_name: str
#
# class TopicRequest(BaseModel):
#     topic: str
#
# def clean_text(text):
#     return ' '.join(text.split()).strip()
#
# def get_google_search_results(query):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#         "Accept-Language": "en-US,en;q=0.5",
#         "Accept-Encoding": "gzip, deflate",
#         "DNT": "1",
#         "Connection": "keep-alive",
#         "Upgrade-Insecure-Requests": "1"
#     }
#     search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
#
#     try:
#         response = requests.get(search_url, headers=headers)
#         response.raise_for_status()
#         logger.debug(f"Search URL: {search_url}")
#         logger.debug(f"Response status code: {response.status_code}")
#         return response.text
#     except requests.RequestException as e:
#         logger.error(f"Error fetching search results: {e}")
#         raise Exception(f"Failed to fetch search results: {e}")
#
# def remove_duplicates(profiles):
#     """
#     Remove duplicate profiles based on name and URL.
#     Returns a list of unique profiles.
#     """
#     seen = set()
#     unique_profiles = []
#
#     for profile in profiles:
#         # Create a tuple of name and URL to use as a unique identifier
#         profile_key = (profile['name'].lower(), profile['linkedin_url'])
#
#         # If we haven't seen this profile before, add it to our results
#         if profile_key not in seen:
#             seen.add(profile_key)
#             unique_profiles.append(profile)
#             logger.debug(f"Added unique profile: {profile['name']}")
#         else:
#             logger.debug(f"Skipped duplicate profile: {profile['name']}")
#
#     return unique_profiles
#
# def parse_profile_results(html_content, limit=15):
#     soup = BeautifulSoup(html_content, 'html.parser')
#     profiles = []
#
#     # Log the HTML structure for debugging
#     logger.debug("HTML Content Structure:")
#     logger.debug(soup.prettify()[:1000])  # First 1000 chars for brevity
#
#     # Try different possible Google result containers
#     result_divs = soup.find_all('div', {'class': ['g', 'MjjYud', 'Gx5Zad', 'tF2Cxc','LC20lb' 'MBeuO' 'DKV0Md']})
#     logger.debug(f"Found {len(result_divs)} result divs")
#
#     for div in result_divs:
#         try:
#             # Try multiple possible selectors for links and titles
#             link = None
#             title = None
#             summary = None
#
#             # Try to find the link (multiple possible structures)
#             link_candidates = [
#                 div.find('a', href=True),
#                 div.find('div', class_='yuRUbf').find('a', href=True) if div.find('div', class_='yuRUbf') else None,
#                 div.find('div', class_='vvjwJb').find('a', href=True) if div.find('div', class_='vvjwJb') else None
#             ]
#             try:
#                 link = next((l for l in link_candidates if l), None)
#             except:
#                 link = soup.find('a', jsname="UWckNb")
#
#
#             if not link or 'linkedin.com/in/' not in link['href']:
#                 continue
#
#             # Normalize the LinkedIn URL
#             linkedin_url = link['href']
#             if '?' in linkedin_url:
#                 linkedin_url = linkedin_url.split('?')[0]
#
#             # Try to find the title (multiple possible structures)
#             title_candidates = [
#                 div.find('h3', class_=lambda x: x and 'LC20lb' in x),
#                 div.find('h3', class_=lambda x: x and 'DKV0Md' in x),
#                 link.find('h3')
#             ]
#             title_element = next((t for t in title_candidates if t), None)
#             if title_element:
#                 title = clean_text(title_element.text)
#
#             # Try to find the summary (multiple possible structures)
#             summary_candidates = [
#                 div.find('div', class_=lambda x: x and 'VwiC3b' in x),
#                 div.find('div', class_='kb0PBd'),
#                 div.find('div', class_='lEBKkf')
#             ]
#             summary_element = next((s for s in summary_candidates if s), None)
#             if summary_element:
#                 summary = clean_text(summary_element.text)
#
#             if link and title:
#                 profile_info = {
#                     "name": title,
#                     "linkedin_url": linkedin_url,
#                     "about_section": summary if summary else "No summary available"
#                 }
#                 logger.debug(f"Found profile: {profile_info}")
#                 profiles.append(profile_info)
#
#         except Exception as e:
#             logger.error(f"Error parsing profile div: {e}")
#             continue
#
#     # Remove duplicates and limit results
#     unique_profiles = remove_duplicates(profiles)
#     return unique_profiles[:limit]
#
# @app.post("/scrape_role_profiles")
# async def scrape_role_profiles(request: RoleCompanyRequest):
#     try:
#         search_query = f'site:linkedin.com/in/ "{request.role}" "{request.company_name}"'
#         logger.info(f"Searching for query: {search_query}")
#
#         search_results_html = get_google_search_results(search_query)
#         profiles = parse_profile_results(search_results_html, limit=10)
#
#         if not profiles:
#             logger.warning(f"No profiles found for {request.role} at {request.company_name}")
#             return {"message": f"No profiles found for {request.role} at {request.company_name}"}
#
#         return profiles
#
#     except Exception as e:
#         logger.error(f"Error in scrape_role_profiles: {e}")
#         return {"error": str(e)}
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8006)

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class RoleCompanyRequest(BaseModel):
    role: str
    company_name: str


def clean_text(text):
    return ' '.join(text.split()).strip()


def get_google_search_results(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        logger.debug(f"Search URL: {search_url}")
        logger.debug(f"Response status code: {response.status_code}")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching search results: {e}")
        raise Exception(f"Failed to fetch search results: {e}")


def remove_duplicates(profiles):
    seen = set()
    unique_profiles = []

    for profile in profiles:
        profile_key = (profile['name'].lower(), profile['linkedin_url'])

        if profile_key not in seen:
            seen.add(profile_key)
            unique_profiles.append(profile)
            logger.debug(f"Added unique profile: {profile['name']}")
        else:
            logger.debug(f"Skipped duplicate profile: {profile['name']}")

    return unique_profiles


def parse_profile_results(html_content, limit=15):
    soup = BeautifulSoup(html_content, 'html.parser')
    profiles = []

    logger.debug("HTML Content Structure:")
    logger.debug(soup.prettify()[:1000])  # First 1000 chars for brevity

    # Corrected class names in find_all
    result_divs = soup.find_all('div', {'class': ['g', 'MjjYud', 'Gx5Zad', 'tF2Cxc', 'LC20lb', 'MBeuO', 'DKV0Md']})
    logger.debug(f"Found {len(result_divs)} result divs")

    for div in result_divs:
        try:
            link_element = div.find('a', href=True)
            if not link_element or 'linkedin.com/in/' not in link_element['href']:
                continue

            linkedin_url = link_element['href'].split('?')[0]  # Normalize URL

            title_element = div.find('h3')
            title = clean_text(title_element.text) if title_element else "No title available"

            summary_element = div.find('span', class_='aCOpRe')
            summary = clean_text(summary_element.text) if summary_element else "No summary available"

            profile_info = {
                "name": title,
                "linkedin_url": linkedin_url,
                "about_section": summary
            }
            logger.debug(f"Found profile: {profile_info}")
            profiles.append(profile_info)

        except Exception as e:
            logger.error(f"Error parsing profile div: {e}")
            continue

    unique_profiles = remove_duplicates(profiles)
    return unique_profiles[:limit]


@app.post("/scrape_role_profiles")
async def scrape_role_profiles(request: RoleCompanyRequest):
    try:
        search_query = f'site:linkedin.com/in/ "{request.role}" "{request.company_name}"'
        logger.info(f"Searching for query: {search_query}")

        search_results_html = get_google_search_results(search_query)
        profiles = parse_profile_results(search_results_html, limit=10)

        if not profiles:
            logger.warning(f"No profiles found for {request.role} at {request.company_name}")
            return {"message": f"No profiles found for {request.role} at {request.company_name}"}

        return profiles

    except Exception as e:
        logger.error(f"Error in scrape_role_profiles: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)

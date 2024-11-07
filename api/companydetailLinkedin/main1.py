# working company detail extractor
import os
import time
import re
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fastapi.middleware.cors import CORSMiddleware


# Your FastAPI app initialization
app = FastAPI()

# Set up CORS for React (or any other frontend)
origins = [
    "http://localhost:3000",  # React frontend running on localhost
    "https://your-react-app.com"  # Update with your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict specific methods like ["GET", "POST"]
    allow_headers=["*"],  # You can restrict specific headers if needed
)
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

class CompanyRequest(BaseModel):
    company_url: str

class CompanyData(BaseModel):
    overview: str = None
    website: str = None
    phone: str = None
    industry: str = None
    company_size: str = None
    headquarters: str = None
    founded: str = None
    specialties: str = None
    top_posts: list[str] = []

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add custom headers to appear as a Windows computer
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
    chrome_options.add_argument("--accept-encoding=gzip, deflate, br")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_to_linkedin(driver):
    logger.info("Logging in to LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)  # Wait for page to load

    # Fill in username and password
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    
    username_field.send_keys(LINKEDIN_USERNAME)
    password_field.send_keys(LINKEDIN_PASSWORD)

    # Click login button
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    # Wait for login to complete
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "global-nav"))
    )
    logger.info("Successfully logged in to LinkedIn")

def safe_extract(driver, selector, attribute=None, by=By.CSS_SELECTOR):
    try:
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((by, selector)))
        value = element.get_attribute(attribute) if attribute else element.text.strip()
        logger.info(f"Successfully extracted {selector}: {value}")
        return value
    except TimeoutException:
        logger.warning(f"Timeout while extracting {selector}")
    except NoSuchElementException:
        logger.warning(f"Element not found: {selector}")
    except Exception as e:
        logger.error(f"Error extracting {selector}: {str(e)}")
    return None

def scrape_about_page(driver, url):
    logger.info(f"Scraping about page: {url}/about/")
    driver.get(url + "/about/")
    
    company_data = CompanyData()

    company_data.overview = safe_extract(driver, "p.break-words")
    company_data.website = safe_extract(driver, "a[href^='http']:not([href*='linkedin.com'])", "href")
    
    # Updated phone extraction
    phone_selector = "a[href^='tel:']"
    phone_href = safe_extract(driver, phone_selector, "href")
    if phone_href:
        company_data.phone = phone_href.replace("tel:", "")

    # Use JavaScript to extract fields
    logger.info("Extracting fields using JavaScript...")
    script = """
    const extractField = (text) => {
        const element = Array.from(document.querySelectorAll('dt')).find(el => el.textContent.trim().includes(text));
        return element ? element.nextElementSibling.textContent.trim() : null;
    };
    const extractPhone = () => {
        const phoneLink = document.querySelector('a[href^="tel:"]');
        return phoneLink ? phoneLink.getAttribute('href').replace('tel:', '') : null;
    };
    return {
        industry: extractField('Industry'),
        company_size: extractField('Company size'),
        headquarters: extractField('Headquarters'),
        founded: extractField('Founded'),
        specialties: extractField('Specialties'),
        phone: extractPhone()
    };
    """
    result = driver.execute_script(script)
    for field, value in result.items():
        if not getattr(company_data, field):
            if field == "company_size" and value:
                match = re.search(r'\d+(?:-\d+)?\s*\w+', value)
                value = match.group() if match else value
            setattr(company_data, field, value)
            logger.info(f"Extracted {field}: {value}")

    return company_data

def scrape_posts(driver, url):
    logger.info(f"Scraping posts: {url}/posts/?feedView=all")
    driver.get(url + "/posts/?feedView=all")
    wait = WebDriverWait(driver, 10)

    posts = []
    try:
        post_selector = "div.feed-shared-update-v2__description-wrapper"
        post_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, post_selector)))
        
        for i, post in enumerate(post_elements[:2]):
            try:
                text = post.find_element(By.CSS_SELECTOR, "span.break-words").text
                posts.append(text)
                logger.info(f"Extracted post {i+1}: {text[:50]}...")
            except Exception as e:
                logger.error(f"Error extracting post {i+1} text: {str(e)}")
    except Exception as e:
        logger.error(f"Error scraping posts: {str(e)}")

    return posts

@app.post("/scrape-company/")
async def scrape_company(request: CompanyRequest):
    driver = setup_selenium()

    try:
        login_to_linkedin(driver)
        
        logger.info("Starting to scrape about page...")
        start_time = time.time()
        company_data = scrape_about_page(driver, request.company_url)
        logger.info(f"Finished scraping about page in {time.time() - start_time:.2f} seconds")

        logger.info("Starting to scrape posts...")
        start_time = time.time()
        company_data.top_posts = scrape_posts(driver, request.company_url)
        logger.info(f"Finished scraping posts in {time.time() - start_time:.2f} seconds")

        return company_data
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
    
# input json
# {
#     "company_url": "https://www.linkedin.com/company/the-drone-destination/"
# }
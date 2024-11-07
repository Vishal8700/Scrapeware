from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import time
import logging
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://scrapeware.vercel.app"],  # React app URL, adjust if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

class SearchRequest(BaseModel):
    search_text: str

class BidCard(BaseModel):
    bid_number: str
    link: str
    items: str
    quantity: str
    department: str
    start_date: str
    end_date: str

class SearchResponse(BaseModel):
    results: List[BidCard]

def setup_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"WebDriver exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize WebDriver: {str(e)}")

def scrape_bid_cards(driver, time_limit: int = 30) -> List[Dict]:
    bid_cards_data = []
    start_time = time.time()

    while True:
        try:
            cards = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'card'))
            )
            
            for card in cards:
                if time.time() - start_time > time_limit:
                    return bid_cards_data

                try:
                    bid_no_tag = card.find_element(By.CLASS_NAME, 'bid_no')
                    bid_no = bid_no_tag.text.strip()
                    bid_link = bid_no_tag.find_element(By.TAG_NAME, 'a').get_attribute('href')

                    col_md_4 = card.find_element(By.CLASS_NAME, 'col-md-4')
                    item_row = col_md_4.find_elements(By.CLASS_NAME, 'row')[0]
                    try:
                        items = item_row.find_element(By.TAG_NAME, 'a').get_attribute('data-content').strip()
                    except NoSuchElementException:
                        items = item_row.text.strip().replace('Items:', '').strip() if 'Items:' in item_row.text else "N/A"

                    quantity = col_md_4.find_elements(By.CLASS_NAME, 'row')[1].text.strip()

                    col_md_5 = card.find_element(By.CLASS_NAME, 'col-md-5')
                    dept_name = col_md_5.find_elements(By.CLASS_NAME, 'row')[1].text.strip()

                    col_md_3 = card.find_element(By.CLASS_NAME, 'col-md-3')
                    start_date = col_md_3.find_elements(By.CLASS_NAME, 'row')[0].find_element(By.CLASS_NAME, 'start_date').text.strip()
                    end_date = col_md_3.find_elements(By.CLASS_NAME, 'row')[1].find_element(By.CLASS_NAME, 'end_date').text.strip()

                    bid_cards_data.append({
                        "bid_number": bid_no,
                        "link": bid_link,
                        "items": items,
                        "quantity": quantity,
                        "department": dept_name,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                except Exception as e:
                    logger.error(f"Error scraping a card: {str(e)}")
                    continue

            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#light-pagination .page-link.next'))
                )
                if "disabled" in next_button.get_attribute("class"):
                    break
                next_button.click()
                time.sleep(2)
            except Exception:
                break
        except TimeoutException:
            logger.error("Timed out waiting for cards to load")
            break

    return bid_cards_data

@app.post("/search", response_model=SearchResponse)
async def search_bids(request: SearchRequest):
    driver = None
    try:
        driver = setup_driver()
        logger.info(f"Searching for: {request.search_text}")
        
        home_url = "https://bidplus.gem.gov.in/all-bids"
        driver.get(home_url)
        
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'searchBid'))
        )
        search_input.clear()
        search_input.send_keys(request.search_text)
        search_input.send_keys(Keys.RETURN)

        time.sleep(2)

        bid_cards_data = scrape_bid_cards(driver)
        return SearchResponse(results=[BidCard(**card) for card in bid_cards_data])
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

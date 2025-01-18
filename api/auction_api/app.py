from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://scrapeware.vercel.app"],  # You can specify allowed origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


class AuctionRequest(BaseModel):
    keyword: str
    page: int = 1  # Optional page number, default to 1


def get_csrf_token_and_cookies():
    url = "https://forwardauction.gem.gov.in/"
    session = requests.Session()  # Maintain the session to handle cookies
    response = session.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': '_csrf'})['value']
        return csrf_token, session.cookies
    else:
        return None, None


def scrape_auctions(keyword, page=1):
    csrf_token, cookies = get_csrf_token_and_cookies()
    if not csrf_token or not cookies:
        raise HTTPException(status_code=500, detail="Could not retrieve CSRF token or cookies.")

    url = "https://forwardauction.gem.gov.in/eprocure/ajax/search-auction"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://forwardauction.gem.gov.in/',
        'Origin': 'https://forwardauction.gem.gov.in/'
    }

    payload = {
        'keywrdSearch': keyword,
        'strDate': '',
        'location': '',
        'farmerName': '',
        'stateID': '',
        'districtID': '',
        'cityID': '',
        'pincode': '',
        'moduleType': '2',
        'searchType': '2',
        'lstType': '2',
        'deptID': '',
        'totalPages': '',
        'xStatus': '6',
        'verField': '',
        'perPage': '40',
        'currentPage': str(page),
        'catID': '',
        '_csrf': csrf_token
    }

    response = requests.post(url, data=payload, headers=headers, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        auctions = soup.find_all('div', class_='listing-content')
        auction_data = []

        for auction in auctions:
            auction_id = auction.find('div', class_='index').text.strip().replace("Auction ID : ", "")
            brief = auction.find('div', class_='brief').text.strip()
            link = auction.find('a', class_='brief')['href']

            location_icon = auction.find('i', class_='fa-map-marker')
            location = 'N/A'
            if location_icon:
                location_span = location_icon.find_next('span')
                if location_span:
                    location = location_span.text.strip()

            start_date = auction.find('span', class_='start-date')
            start_date = start_date.text.strip().replace("Start Date :", "").strip() if start_date else 'N/A'

            end_date = auction.find('span', class_='end-date')
            end_date = end_date.text.strip().replace("End Date :", "").strip() if end_date else 'N/A'

            organizer = auction.find('div', class_='department')
            organizer = organizer.text.strip() if organizer else 'N/A'

            auction_data.append({
                'Auction ID': auction_id,
                'Brief': brief,
                'Link': "https://forwardauction.gem.gov.in" + link,
                'Location': location,
                'Start Date': start_date,
                'End Date': end_date,
                'Organizer': organizer
            })

        return auction_data
    else:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve auctions: {response.status_code}")


@app.post("/scrape-auctions/")
def scrape_auction_endpoint(request: AuctionRequest):
    try:
        result = scrape_auctions(request.keyword, request.page)
        if result:
            return {"status": "success", "data": result}
        else:
            return {"status": "success", "data": [], "message": "No auctions found."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# To run the server on port 5000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
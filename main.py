import requests
from bs4 import BeautifulSoup
import re
import html5lib
from datetime import datetime, timedelta
from flask import Flask, jsonify
import schedule
import time

app = Flask(__name__)

def fetch_and_cache_html(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        # Check if request was successful
        if response.status_code == 200:
            return response.content
        else:
            print("Failed to retrieve webpage. Status code:", response.status_code)
            return None
    except Exception as e:
        print("An error occurred:", e)
        return None

def update_cache():
    # Fetch HTML content and update cache
    global cached_html
    cached_html = fetch_and_cache_html(URL)

def get_product_info():
    price_pattern = re.compile(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*€')

    if cached_html:
        soup = BeautifulSoup(cached_html, 'html5lib')
        offer_tables = soup.find_all('table', attrs={'typeof': 'OfferCatalog'})
        if not offer_tables:
            return "No offer tables found on the webpage."
        stores = []
        for table in offer_tables:
            for row in table.find_all('tr'):
                logo_div = row.find('div', style=re.compile(r'unternehmen/logos'))
                if not logo_div:
                    continue
                store_name = logo_div.get('title', '').replace(' Angebote', '')
                tds = row.find_all('td')
                if len(tds) < 2:
                    continue
                offer_td = tds[1]
                offer_text = offer_td.get_text(strip=True, separator=' ')
                price_span = offer_td.find('span', style=re.compile(r'#c03938'))
                price = None
                if price_span:
                    m = price_pattern.search(price_span.get_text())
                    if m:
                        price = m.group(1)
                if 'gültig' in offer_text and price:
                    stores.append({"name": store_name, "status": "im angebot", "price": price, "raw": offer_text})
                else:
                    stores.append({"name": store_name, "status": "nicht im angebot", "raw": offer_text})
        return stores
    else:
        return "Failed to retrieve HTML content."

@app.route('/')
def product_info():
    return jsonify(get_product_info())

# URL of the product page
URL = 'https://www.aktionspreis.de/angebote/havana-club-0-7l'

# Initialize cached HTML content
cached_html = fetch_and_cache_html(URL)

# Schedule to fetch HTML content every day at 6 am
schedule.every().day.at("06:00").do(update_cache)

# Run scheduled tasks in a separate thread
def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Start the schedule thread
    import threading
    threading.Thread(target=schedule_thread).start()
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0')

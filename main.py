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

def filter_by_gültig(text):
    return "gültig" in text

def get_product_info():
    price_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*€'

    if cached_html:
        soup = BeautifulSoup(cached_html, 'html5lib')
        tables = soup.find_all('table')
        if len(tables) == 1:
            table_html = tables[0]
            rows = table_html.find_all('tr', attrs={'onmouseover': True})
            stores = []
            for row in rows:
                l = row.find_all('td')[1].small
                pricetag = row.find_all('div')[2].get_text(strip=True, separator=' ')

                match = re.search(price_pattern, pricetag)
                if match:
                    price = match.group(1)
                storetag = row.select_one('div[style*="./system/images/unternehmen/logos/"]')
                storename = storetag['title'].replace (" Angebote", "")
                
                if "letzte" not in l.text and "noch" in pricetag:
                    stores.append({"name": storename, "status": "im angebot", "price": price, "raw": pricetag})
                else:
                    stores.append({"name": storename, "status": "nicht im angebot", "raw": pricetag})
            return stores
        else:
            return "More than one table found on the webpage."
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

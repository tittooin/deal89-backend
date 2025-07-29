from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class FlipkartScraper:
    def __init__(self):
        self.base_url = "https://www.flipkart.com"

    def get_deals(self) -> List[Dict[str, str]]:
        deals = []
        try:
            response = requests.get(f"{self.base_url}/search?q=deals")
            soup = BeautifulSoup(response.text, 'html.parser')

            # Example parsing logic (this may need to be adjusted based on actual HTML structure)
            for item in soup.find_all('div', class_='_1AtVbE'):
                title = item.find('a', class_='IRpwTa')
                price = item.find('div', class_='_30jeq3')
                if title and price:
                    deals.append({
                        "title": title.text,
                        "current_price": price.text,
                        "url": f"{self.base_url}{title['href']}",
                        "platform": "flipkart"
                    })
        except Exception as e:
            print(f"Error fetching deals from Flipkart: {str(e)}")
        
        return deals
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import logging

class JioMartScraper:
    def __init__(self):
        self.base_url = "https://www.jiomart.com"
        self.logger = logging.getLogger(__name__)

    def get_deals(self) -> List[Dict[str, str]]:
        deals = []
        try:
            response = requests.get(f"{self.base_url}/deals")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Example parsing logic (this will depend on the actual HTML structure of JioMart)
            for item in soup.select('.product-list .product'):
                title = item.select_one('.product-title').get_text(strip=True)
                current_price = item.select_one('.current-price').get_text(strip=True)
                original_price = item.select_one('.original-price').get_text(strip=True)
                discount_percentage = self.calculate_discount(original_price, current_price)
                url = self.base_url + item.select_one('a')['href']

                deals.append({
                    "title": title,
                    "current_price": current_price,
                    "original_price": original_price,
                    "discount_percentage": discount_percentage,
                    "url": url,
                    "platform": "jiomart"
                })

        except Exception as e:
            self.logger.error(f"Error fetching deals from JioMart: {str(e)}")
        
        return deals

    def calculate_discount(self, original_price: str, current_price: str) -> float:
        original_price_value = float(original_price.replace('₹', '').replace(',', '').strip())
        current_price_value = float(current_price.replace('₹', '').replace(',', '').strip())
        discount = ((original_price_value - current_price_value) / original_price_value) * 100
        return round(discount, 2) if original_price_value > 0 else 0.0
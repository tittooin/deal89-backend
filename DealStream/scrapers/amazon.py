from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import logging

class AmazonScraper:
    def __init__(self):
        self.base_url = "https://www.amazon.in/s?k="
        self.logger = logging.getLogger(__name__)

    def get_deals(self, query: str) -> List[Dict[str, str]]:
        """Scrape deals from Amazon based on the search query."""
        deals = []
        try:
            response = requests.get(self.base_url + query)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find product listings
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            for product in products:
                title = product.h2.text.strip()
                url = "https://www.amazon.in" + product.h2.a['href']
                price = product.find('span', 'a-price-whole')
                original_price = product.find('span', 'a-price a-text-price')
                discount_percentage = self.calculate_discount(price, original_price)

                deals.append({
                    "title": title,
                    "url": url,
                    "current_price": price.text.strip() if price else "N/A",
                    "original_price": original_price.text.strip() if original_price else "N/A",
                    "discount_percentage": discount_percentage
                })
        except Exception as e:
            self.logger.error(f"Error fetching deals from Amazon: {str(e)}")
        
        return deals

    def calculate_discount(self, current_price, original_price) -> float:
        """Calculate discount percentage."""
        if current_price and original_price:
            try:
                current_price_value = float(current_price.text.replace(',', '').replace('₹', '').strip())
                original_price_value = float(original_price.text.replace(',', '').replace('₹', '').strip())
                discount = ((original_price_value - current_price_value) / original_price_value) * 100
                return round(discount, 2)
            except (ValueError, AttributeError):
                return 0.0
        return 0.0
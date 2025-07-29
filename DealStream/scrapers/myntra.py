from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class MyntraScraper:
    def __init__(self):
        self.base_url = "https://www.myntra.com"

    def get_deals(self) -> List[Dict[str, str]]:
        deals = []
        try:
            response = requests.get(f"{self.base_url}/sale")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Example scraping logic (this may need to be adjusted based on actual HTML structure)
            products = soup.find_all("div", class_="productBase")
            for product in products:
                title = product.find("h4", class_="product-product").text.strip()
                current_price = product.find("span", class_="product-discountedPrice").text.strip()
                original_price = product.find("span", class_="product-strike").text.strip()
                discount_percentage = self.calculate_discount(original_price, current_price)

                deal = {
                    "title": title,
                    "current_price": current_price,
                    "original_price": original_price,
                    "discount_percentage": discount_percentage,
                    "url": f"{self.base_url}{product.find('a')['href']}",
                    "image_url": product.find("img")["src"]
                }
                deals.append(deal)

        except Exception as e:
            print(f"Error fetching deals from Myntra: {str(e)}")

        return deals

    def calculate_discount(self, original_price: str, current_price: str) -> float:
        original_price_value = float(original_price.replace("₹", "").replace(",", "").strip())
        current_price_value = float(current_price.replace("₹", "").replace(",", "").strip())
        discount = ((original_price_value - current_price_value) / original_price_value) * 100
        return round(discount, 2) if original_price_value > 0 else 0.0
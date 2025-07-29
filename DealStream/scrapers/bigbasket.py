from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class BigBasketScraper:
    def __init__(self):
        self.base_url = "https://www.bigbasket.com"

    def get_deals(self) -> List[Dict[str, str]]:
        deals = []
        try:
            response = requests.get(f"{self.base_url}/products")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Example scraping logic (this will need to be adjusted based on actual HTML structure)
            product_elements = soup.find_all("div", class_="product")
            for product in product_elements:
                title = product.find("h4", class_="product-title").text.strip()
                current_price = product.find("span", class_="discnt-price").text.strip()
                original_price = product.find("span", class_="actual-price").text.strip()
                discount_percentage = self.calculate_discount(original_price, current_price)

                deal = {
                    "id": product["data-id"],
                    "title": title,
                    "current_price": current_price,
                    "original_price": original_price,
                    "discount_percentage": discount_percentage,
                    "url": f"{self.base_url}{product.find('a')['href']}",
                    "image_url": product.find("img")["src"]
                }
                deals.append(deal)

        except Exception as e:
            print(f"Error fetching deals from BigBasket: {str(e)}")

        return deals

    def calculate_discount(self, original_price: str, current_price: str) -> float:
        original_price_value = float(original_price.replace("₹", "").replace(",", "").strip())
        current_price_value = float(current_price.replace("₹", "").replace(",", "").strip())
        discount = ((original_price_value - current_price_value) / original_price_value) * 100
        return round(discount, 2) if original_price_value > 0 else 0.0
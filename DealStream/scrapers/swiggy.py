from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class SwiggyInstatmartScraper:
    def __init__(self):
        self.base_url = "https://www.swiggy.com"

    def get_deals(self) -> List[Dict[str, str]]:
        deals = []
        try:
            response = requests.get(f"{self.base_url}/deals")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Example parsing logic (this will depend on the actual HTML structure)
                for deal in soup.find_all("div", class_="deal-card"):
                    title = deal.find("h2", class_="deal-title").text
                    current_price = deal.find("span", class_="current-price").text
                    original_price = deal.find("span", class_="original-price").text
                    discount_percentage = deal.find("span", class_="discount-percentage").text
                    
                    deals.append({
                        "title": title,
                        "current_price": current_price,
                        "original_price": original_price,
                        "discount_percentage": discount_percentage,
                        "url": self.base_url + deal.find("a")["href"],
                        "platform": "swiggy"
                    })
        except Exception as e:
            print(f"Error fetching deals from Swiggy: {str(e)}")
        
        return deals
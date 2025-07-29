import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import List, Dict, Any
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class BigBasketScraper:
    def __init__(self):
        self.base_url = "https://www.bigbasket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def get_deals(self) -> List[Dict[str, Any]]:
        """Scrape deals from BigBasket"""
        deals = []
        
        # URLs to scrape deals from
        deal_urls = [
            f"{self.base_url}/pc/fruits-vegetables/",
            f"{self.base_url}/pc/beverages/",
            f"{self.base_url}/pc/foodgrains-oil-masala/"
        ]
        
        for url in deal_urls:
            try:
                deals.extend(self._scrape_deals_page(url))
                time.sleep(random.uniform(1, 3))  # Random delay
            except Exception as e:
                logger.error(f"Error scraping BigBasket URL {url}: {str(e)}")
                continue
                
        return deals[:20]  # Return top 20 deals
    
    def _scrape_deals_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape deals from a specific BigBasket page"""
        deals = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product containers
            product_selectors = [
                '.product-tile',
                '.product-card',
                '.ProdListCard',
                '.product-item'
            ]
            
            products = []
            for selector in product_selectors:
                found_products = soup.select(selector)
                if found_products:
                    products = found_products
                    break
            
            for product in products[:10]:  # Limit to 10 per page
                try:
                    deal = self._extract_deal_info(product, url)
                    if deal and self._is_valid_deal(deal):
                        deals.append(deal)
                except Exception as e:
                    logger.debug(f"Error extracting deal info: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping BigBasket page {url}: {str(e)}")
            
        return deals
    
    def _extract_deal_info(self, product_element, base_url: str) -> Dict[str, Any]:
        """Extract deal information from product element"""
        try:
            # Extract title
            title_selectors = [
                '.product-name',
                '.ProdListCard-title',
                'a[title]',
                'h3',
                'h4'
            ]
            title = ""
            for selector in title_selectors:
                title_elem = product_element.select_one(selector)
                if title_elem:
                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Extract price
            price_selectors = [
                '.selling-price',
                '.current-price',
                '.product-price',
                '.ProdListCard-price'
            ]
            current_price = ""
            for selector in price_selectors:
                price_elem = product_element.select_one(selector)
                if price_elem:
                    current_price = price_elem.get_text(strip=True)
                    break
            
            # Extract original price
            original_price_selectors = [
                '.original-price',
                '.mrp-price',
                '.line-through',
                '.strike-through'
            ]
            original_price = ""
            for selector in original_price_selectors:
                orig_price_elem = product_element.select_one(selector)
                if orig_price_elem:
                    original_price = orig_price_elem.get_text(strip=True)
                    break
            
            # Extract product URL
            url_selectors = ['a[href]']
            product_url = ""
            for selector in url_selectors:
                url_elem = product_element.select_one(selector)
                if url_elem and url_elem.get('href'):
                    href = url_elem.get('href')
                    if href.startswith('/'):
                        product_url = urljoin(self.base_url, href)
                    else:
                        product_url = href
                    break
            
            # Calculate discount percentage
            discount_percentage = self._calculate_discount(current_price, original_price)
            
            # Generate unique ID
            deal_id = self._generate_deal_id(title, current_price)
            
            return {
                "id": deal_id,
                "title": title,
                "current_price": current_price,
                "original_price": original_price,
                "discount_percentage": discount_percentage,
                "url": product_url,
                "platform": "bigbasket",
                "image_url": self._extract_image_url(product_element),
                "scraped_at": time.time()
            }
            
        except Exception as e:
            logger.debug(f"Error in _extract_deal_info: {str(e)}")
            return None
    
    def _extract_image_url(self, product_element) -> str:
        """Extract product image URL"""
        img_selectors = ['img[src]', '.product-image img']
        for selector in img_selectors:
            img_elem = product_element.select_one(selector)
            if img_elem and img_elem.get('src'):
                return img_elem.get('src')
        return ""
    
    def _calculate_discount(self, current_price: str, original_price: str) -> float:
        """Calculate discount percentage"""
        try:
            # Extract numeric values from price strings
            current = float(re.sub(r'[^\d.]', '', current_price))
            original = float(re.sub(r'[^\d.]', '', original_price))
            
            if original > current > 0:
                return round(((original - current) / original) * 100, 2)
        except (ValueError, ZeroDivisionError):
            pass
        return 0.0
    
    def _generate_deal_id(self, title: str, price: str) -> str:
        """Generate unique deal ID"""
        return f"bigbasket_{hash(title + price) % 1000000}"
    
    def _is_valid_deal(self, deal: Dict[str, Any]) -> bool:
        """Validate if deal has required information"""
        return (deal.get("title") and 
                deal.get("current_price") and 
                deal.get("url") and
                len(deal.get("title", "")) > 5)

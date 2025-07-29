import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import List, Dict, Any
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class SwiggyInstatmartScraper:
    def __init__(self):
        self.base_url = "https://www.swiggy.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def get_deals(self) -> List[Dict[str, Any]]:
        """Scrape deals from Swiggy Instamart"""
        deals = []
        
        # URLs to scrape deals from (Swiggy Instamart sections)
        deal_urls = [
            f"{self.base_url}/instamart",
            f"{self.base_url}/instamart/search?custom_back=true&query=fruits",
            f"{self.base_url}/instamart/search?custom_back=true&query=vegetables"
        ]
        
        for url in deal_urls:
            try:
                deals.extend(self._scrape_deals_page(url))
                time.sleep(random.uniform(2, 4))  # Random delay
            except Exception as e:
                logger.error(f"Error scraping Swiggy URL {url}: {str(e)}")
                continue
                
        return deals[:20]  # Return top 20 deals
    
    def _scrape_deals_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape deals from a specific Swiggy page"""
        deals = []
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product containers (Swiggy uses React, so selectors might be limited)
            product_selectors = [
                '[data-testid="item-card"]',
                '.product-item',
                '.item-card',
                '.instamart-item'
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
            logger.error(f"Error scraping Swiggy page {url}: {str(e)}")
            
        return deals
    
    def _extract_deal_info(self, product_element, base_url: str) -> Dict[str, Any]:
        """Extract deal information from product element"""
        try:
            # Extract title
            title_selectors = [
                '[data-testid="item-name"]',
                '.item-name',
                '.product-title',
                'h3',
                'h4'
            ]
            title = ""
            for selector in title_selectors:
                title_elem = product_element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Extract price
            price_selectors = [
                '[data-testid="item-price"]',
                '.item-price',
                '.current-price',
                '.selling-price'
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
                '.strike-through',
                '.line-through'
            ]
            original_price = ""
            for selector in original_price_selectors:
                orig_price_elem = product_element.select_one(selector)
                if orig_price_elem:
                    original_price = orig_price_elem.get_text(strip=True)
                    break
            
            # For Swiggy, product URLs might not be directly available due to React routing
            # We'll construct a basic URL pattern
            product_url = f"{self.base_url}/instamart/item/{title.replace(' ', '-').lower()}"
            
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
                "platform": "swiggy",
                "image_url": self._extract_image_url(product_element),
                "scraped_at": time.time()
            }
            
        except Exception as e:
            logger.debug(f"Error in _extract_deal_info: {str(e)}")
            return None
    
    def _extract_image_url(self, product_element) -> str:
        """Extract product image URL"""
        img_selectors = ['img[src]', '[data-testid="item-image"]']
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
        return f"swiggy_{hash(title + price) % 1000000}"
    
    def _is_valid_deal(self, deal: Dict[str, Any]) -> bool:
        """Validate if deal has required information"""
        return (deal.get("title") and 
                deal.get("current_price") and 
                deal.get("url") and
                len(deal.get("title", "")) > 5)

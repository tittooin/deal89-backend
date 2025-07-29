from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import razorpay
import os
from dotenv import load_dotenv
import asyncio
import concurrent.futures
from typing import List, Dict, Any
import logging
import time
from datetime import datetime

# Import scraper modules
from scrapers.flipkart import FlipkartScraper
from scrapers.amazon import AmazonScraper
from scrapers.jiomart import JioMartScraper
from scrapers.myntra import MyntraScraper
from scrapers.swiggy import SwiggyInstatmartScraper
from scrapers.bigbasket import BigBasketScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Deal Aggregator API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID", ""),
        os.getenv("RAZORPAY_KEY_SECRET", "")
    )
)

# Initialize scrapers
scrapers = {
    "flipkart": FlipkartScraper(),
    "amazon": AmazonScraper(),
    "jiomart": JioMartScraper(),
    "myntra": MyntraScraper(),
    "swiggy": SwiggyInstatmartScraper(),
    "bigbasket": BigBasketScraper()
}

# Cache for deals (simple in-memory cache)
deals_cache = {}
cache_timestamp = {}

# Sample deals for immediate display
sample_deals = {
    "flipkart": [
        {
            "id": "flipkart_sample1",
            "title": "Samsung Galaxy M14 5G (Smoky Teal, 128 GB)",
            "current_price": "₹14,990",
            "original_price": "₹17,990",
            "discount_percentage": 16.7,
            "url": "https://www.flipkart.com/samsung-galaxy-m14-5g-smoky-teal-128-gb/p/sample",
            "platform": "flipkart",
            "image_url": "",
            "scraped_at": int(time.time())
        },
        {
            "id": "flipkart_sample2", 
            "title": "Apple iPhone 13 (Blue, 128 GB)",
            "current_price": "₹54,900",
            "original_price": "₹69,900",
            "discount_percentage": 21.5,
            "url": "https://www.flipkart.com/apple-iphone-13-blue-128-gb/p/sample",
            "platform": "flipkart",
            "image_url": "",
            "scraped_at": int(time.time())
        }
    ],
    "amazon": [
        {
            "id": "amazon_sample1",
            "title": "OnePlus Nord CE 3 Lite 5G (Pastel Lime, 8GB RAM, 128GB Storage)",
            "current_price": "₹19,999",
            "original_price": "₹21,999",
            "discount_percentage": 9.1,
            "url": "https://www.amazon.in/dp/sample1",
            "platform": "amazon",
            "image_url": "",
            "scraped_at": int(time.time())
        }
    ],
    "myntra": [
        {
            "id": "myntra_sample1",
            "title": "Roadster Men Navy Blue Solid Round Neck T-shirt",
            "current_price": "₹399",
            "original_price": "₹799",
            "discount_percentage": 50.1,
            "url": "https://www.myntra.com/tshirts/roadster/sample",
            "platform": "myntra",
            "image_url": "",
            "scraped_at": int(time.time())
        }
    ]
}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found")

@app.post("/create_order")
async def create_razorpay_order(request: Request):
    """Create a Razorpay order for ₹0.89 payment"""
    try:
        body = await request.json()
        deal_id = body.get("deal_id")
        platform = body.get("platform")
        
        if not deal_id or not platform:
            raise HTTPException(status_code=400, detail="Missing deal_id or platform")
        
        # Create Razorpay order
        order_data = {
            "amount": 89,  # ₹0.89 in paise
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "deal_id": deal_id,
                "platform": platform
            }
        }
        
        order = razorpay_client.order.create(order_data)
        
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key": os.getenv("RAZORPAY_KEY_ID", "")
        }
        
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@app.post("/verify_payment")
async def verify_payment(request: Request):
    """Verify payment and return affiliate link"""
    try:
        body = await request.json()
        payment_id = body.get("payment_id")
        order_id = body.get("order_id")
        signature = body.get("signature")
        deal_id = body.get("deal_id")
        platform = body.get("platform")
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        try:
            import razorpay.utils as razorpay_utils
            razorpay_utils.verify_payment_signature(params_dict, os.getenv("RAZORPAY_KEY_SECRET", ""))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Get the deal and generate affiliate link
        platform_deals = deals_cache.get(platform, [])
        deal = next((d for d in platform_deals if d.get("id") == deal_id), None)
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        affiliate_link = generate_affiliate_link(deal["url"], platform)
        
        return {
            "success": True,
            "affiliate_link": affiliate_link,
            "deal_title": deal["title"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment verification failed")

def generate_affiliate_link(original_url: str, platform: str) -> str:
    """Generate affiliate link based on platform"""
    affiliate_ids = {
        "flipkart": os.getenv("AFFILIATE_FLIPKART", ""),
        "amazon": os.getenv("AFFILIATE_AMAZON", ""),
        "jiomart": os.getenv("AFFILIATE_JIOMART", ""),
        "myntra": os.getenv("AFFILIATE_MYNTRA", ""),
        "bigbasket": os.getenv("AFFILIATE_BIGBASKET", ""),
        "swiggy": os.getenv("AFFILIATE_SWIGGY", "")
    }
    
    affiliate_id = affiliate_ids.get(platform, "")
    
    if platform == "flipkart":
        # Extract product path from URL
        if "/p/" in original_url:
            product_path = original_url.split("/p/")[1].split("?")[0]
            return f"https://dl.flipkart.com/dl/p/{product_path}?affid={affiliate_id}"
        return f"{original_url}?affid={affiliate_id}"
    
    elif platform == "amazon":
        # Extract ASIN from URL
        if "/dp/" in original_url:
            asin = original_url.split("/dp/")[1].split("/")[0].split("?")[0]
            return f"https://www.amazon.in/dp/{asin}?tag={affiliate_id}"
        return f"{original_url}?tag={affiliate_id}"
    
    elif platform == "jiomart":
        return f"{original_url}?affid={affiliate_id}"
    
    elif platform == "myntra":
        return f"https://myntra.go2cloud.org/aff_c?offer_id=6&aff_id={affiliate_id}&url={original_url}"
    
    elif platform == "bigbasket":
        return f"{original_url}?affiliate={affiliate_id}"
    
    elif platform == "swiggy":
        return f"https://cuelinks.com/redirect?url={original_url}&aff_id={affiliate_id}"
    
    return original_url

async def scrape_platform_async(platform: str, scraper) -> List[Dict[str, Any]]:
    """Asynchronously scrape deals from a platform"""
    try:
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            deals = await loop.run_in_executor(executor, scraper.get_deals)
            return deals
    except Exception as e:
        logger.error(f"Error scraping {platform}: {str(e)}")
        return []

@app.get("/deals/{platform}")
async def get_platform_deals(platform: str):
    """Get deals from a specific platform"""
    if platform not in scrapers:
        raise HTTPException(status_code=404, detail="Platform not supported")
    
    # Check cache freshness (5 minutes)
    current_time = datetime.now()
    if (platform in cache_timestamp and 
        (current_time - cache_timestamp[platform]).total_seconds() < 300 and
        platform in deals_cache):
        return {"platform": platform, "deals": deals_cache[platform]}
    
    try:
        scraper = scrapers[platform]
        deals = await scrape_platform_async(platform, scraper)
        
        # Update cache
        deals_cache[platform] = deals
        cache_timestamp[platform] = current_time
        
        return {"platform": platform, "deals": deals}
        
    except Exception as e:
        logger.error(f"Error fetching deals for {platform}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch {platform} deals")

@app.get("/deals")
async def get_all_deals():
    """Get deals from all platforms"""
    all_deals = []
    
    # First, add sample deals to ensure immediate display
    for platform, platform_deals in sample_deals.items():
        for deal in platform_deals:
            deal_copy = deal.copy()
            deal_copy["platform"] = platform
            all_deals.append(deal_copy)
    
    # Create tasks for concurrent scraping
    tasks = []
    platforms_to_scrape = []
    
    for platform, scraper in scrapers.items():
        # Check cache first
        current_time = datetime.now()
        if (platform in cache_timestamp and 
            (current_time - cache_timestamp[platform]).total_seconds() < 300 and
            platform in deals_cache):
            # Use cached data
            for deal in deals_cache[platform]:
                deal_copy = deal.copy()
                deal_copy["platform"] = platform
                all_deals.append(deal_copy)
        else:
            # Create scraping task
            tasks.append(scrape_platform_async(platform, scraper))
            platforms_to_scrape.append(platform)
    
    # Execute scraping tasks
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {platforms_to_scrape[i]}: {str(result)}")
                continue
            
            platform = platforms_to_scrape[i]
            deals = result if result else []
            
            # Update cache
            deals_cache[platform] = deals
            cache_timestamp[platform] = datetime.now()
            
            # Add platform info and append to all_deals
            for deal in deals:
                deal_copy = deal.copy()
                deal_copy["platform"] = platform
                all_deals.append(deal_copy)
    
    # Remove duplicates and sort by discount percentage
    seen_titles = set()
    unique_deals = []
    for deal in all_deals:
        title_key = f"{deal['platform']}_{deal['title'][:50]}"
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_deals.append(deal)
    
    unique_deals.sort(key=lambda x: float(x.get("discount_percentage", 0)), reverse=True)
    
    return {"deals": unique_deals, "total_count": len(unique_deals)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

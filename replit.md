# Deal Aggregator Website

## Overview

This is a real-time deal aggregator website built with Python FastAPI backend and vanilla HTML/CSS/JavaScript frontend. The application scrapes live deals from major Indian e-commerce platforms (Flipkart, Amazon, JioMart, Myntra, Swiggy Instamart, BigBasket) and provides affiliate links behind a payment gateway using Razorpay integration.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI for high-performance async web API
- **Scraping Engine**: Multi-platform web scraping using requests + BeautifulSoup
- **Payment Processing**: Razorpay integration for micro-payments (₹0.89)
- **Affiliate System**: Auto-generated affiliate links per platform
- **Background Tasks**: Async deal fetching to prevent blocking

### Frontend Architecture
- **Technology**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5 for responsive design
- **Payment UI**: Razorpay Checkout.js integration
- **Real-time Updates**: AJAX calls to backend API endpoints

### Data Flow
1. User visits frontend → loads cached deals
2. Background scrapers fetch fresh deals from 6 platforms
3. User clicks "Unlock Deal" → Razorpay payment flow
4. Payment success → affiliate link opens in new tab

## Key Components

### Web Scrapers (`/scrapers/`)
- **FlipkartScraper**: Scrapes offers-store, mobile, electronics, fashion sections
- **AmazonScraper**: Scrapes deals, goldbox, search results
- **JioMartScraper**: Scrapes groceries and electronics categories
- **MyntraScraper**: Scrapes men, women, kids fashion deals
- **SwiggyInstatmartScraper**: Scrapes grocery deals from Swiggy
- **BigBasketScraper**: Scrapes fruits, beverages, foodgrains sections

Each scraper implements:
- Session management with proper headers
- Random delays to avoid rate limiting
- Error handling and logging
- Structured deal data extraction

### Backend API Endpoints
- `GET /deals` - Aggregated deals from all platforms
- `GET /{platform}-deals` - Platform-specific deals
- `POST /create_order` - Razorpay order creation
- `POST /razorpay-webhook` - Payment verification (optional)

### Frontend Components
- Deal cards with platform branding
- Filter system by platform
- Unlock button with payment flow
- Loading states and error handling
- Responsive design for mobile/desktop

## Data Flow

### Deal Aggregation Flow
1. **Scraping**: Each platform scraper runs concurrently using `concurrent.futures`
2. **Data Processing**: Raw HTML → structured deal objects with title, price, URL
3. **Affiliate Generation**: Original URLs transformed to affiliate links
4. **API Response**: JSON array of deals with platform metadata

### Payment Flow
1. **Order Creation**: Frontend calls `/create_order` with amount (₹0.89)
2. **Razorpay Checkout**: Modal opens with payment options
3. **Payment Success**: Callback triggers affiliate link opening
4. **Webhook Verification**: Backend validates payment authenticity

### Affiliate Link Generation
- **Flipkart**: `https://dl.flipkart.com/dl<path>?affid=AFFILIATE_FLIPKART`
- **Amazon**: `https://www.amazon.in/dp/<ASIN>?tag=AFFILIATE_AMAZON`
- **JioMart**: `https://www.jiomart.com<path>?affid=AFFILIATE_JIOMART`
- **Myntra**: `https://myntra.go2cloud.org/aff_c?offer_id=6&aff_id=AFFILIATE_MYNTRA&url=<URL>`
- **BigBasket**: `https://www.bigbasket.com<path>?affiliate=AFFILIATE_BIGBASKET`
- **Swiggy**: `https://cuelinks.com/redirect?url=<ORIGINAL_URL>&aff_id=AFFILIATE_SWIGGY`

## External Dependencies

### Python Packages
- `fastapi` - Web framework
- `requests` - HTTP client for scraping
- `beautifulsoup4` - HTML parsing
- `razorpay` - Payment gateway SDK
- `python-dotenv` - Environment variable management
- `uvicorn` - ASGI server

### Frontend Dependencies
- Bootstrap 5 - CSS framework
- Font Awesome 6 - Icon library
- Razorpay Checkout.js - Payment interface

### Environment Variables
- `RAZORPAY_KEY_ID` - Public Razorpay key
- `RAZORPAY_KEY_SECRET` - Secret Razorpay key
- `AFFILIATE_FLIPKART` - Flipkart affiliate ID
- `AFFILIATE_AMAZON` - Amazon associate tag
- `AFFILIATE_JIOMART` - JioMart affiliate ID
- `AFFILIATE_MYNTRA` - Myntra affiliate ID
- `AFFILIATE_BIGBASKET` - BigBasket affiliate ID
- `AFFILIATE_SWIGGY` - Swiggy affiliate ID

## Deployment Strategy

### Development Setup
1. Install Python dependencies via pip
2. Configure `.env` file with Razorpay and affiliate credentials
3. Run FastAPI server: `uvicorn main:app --reload`
4. Serve static files from `/static` directory

### Production Considerations
- **Rate Limiting**: Implement delays between scraping requests
- **Caching**: Cache deals for 15-30 minutes to reduce scraping load
- **Error Handling**: Graceful fallbacks when scrapers fail
- **Monitoring**: Log scraping success/failure rates
- **Security**: Validate webhook signatures, sanitize scraped data

### Scaling Options
- **Background Jobs**: Move scraping to Celery/Redis queue
- **Database**: Store deals in PostgreSQL/MongoDB for persistence
- **CDN**: Serve static assets via CDN
- **Load Balancing**: Multiple FastAPI instances behind nginx

## Technical Notes

- Scrapers use realistic browser headers to avoid detection
- Random delays (1-4 seconds) between requests prevent IP blocking
- Each platform scraper is independent - failures don't affect others
- Affiliate links are generated client-side after payment success
- CORS enabled for frontend-backend communication
- Static file serving integrated into FastAPI app
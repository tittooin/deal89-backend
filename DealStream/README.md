# DealStream

DealStream is a FastAPI application that aggregates deals from various e-commerce platforms. It provides a simple API for fetching deals, processing payments through Razorpay, and generating affiliate links.

## Features

- Scrapes deals from multiple platforms including Amazon, Flipkart, JioMart, Myntra, BigBasket, and Swiggy.
- Handles payment processing using Razorpay.
- Provides endpoints for fetching deals and verifying payments.
- CORS enabled for frontend integration.
- Static files served for the frontend.

## Project Structure

```
DealStream
├── main.py                # Main entry point of the FastAPI application
├── scrapers               # Directory containing scraper implementations
│   ├── __init__.py       # Marks the scrapers directory as a package
│   ├── amazon.py         # AmazonScraper implementation
│   ├── bigbasket.py      # BigBasketScraper implementation
│   ├── flipkart.py       # FlipkartScraper implementation
│   ├── jiomart.py        # JioMartScraper implementation
│   ├── myntra.py         # MyntraScraper implementation
│   └── swiggy.py         # SwiggyInstatmartScraper implementation
├── static                 # Directory for static files
│   └── index.html        # Main HTML page served by the application
├── .env                   # Environment variables for the application
├── requirements.txt       # Python dependencies for the project
└── README.md              # Documentation for the project
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd DealStream
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables in the `.env` file. You can use the provided `.env.example` as a reference.

## Usage

To run the application, execute the following command:
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

You can then access the API at `http://localhost:8000`.

## API Endpoints

- `GET /deals/{platform}`: Fetch deals from a specific platform.
- `GET /deals`: Fetch deals from all platforms.
- `POST /create_order`: Create a Razorpay order.
- `POST /verify_payment`: Verify payment and get affiliate link.
- `GET /health`: Health check endpoint.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
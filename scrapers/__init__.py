"""
Deal aggregator scrapers package
"""

__version__ = "1.0.0"
__author__ = "Deal Aggregator"

from .flipkart import FlipkartScraper
from .amazon import AmazonScraper
from .jiomart import JioMartScraper
from .myntra import MyntraScraper
from .swiggy import SwiggyInstatmartScraper
from .bigbasket import BigBasketScraper

__all__ = [
    "FlipkartScraper",
    "AmazonScraper", 
    "JioMartScraper",
    "MyntraScraper",
    "SwiggyInstatmartScraper",
    "BigBasketScraper"
]

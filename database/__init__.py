"""
Database module - MongoDB integration.
"""
from .mongodb import MongoDBClient, get_mongodb_client
from .models import ScrapedDataModel, ScrapeLogModel

__all__ = [
    "MongoDBClient",
    "get_mongodb_client",
    "ScrapedDataModel",
    "ScrapeLogModel",
]

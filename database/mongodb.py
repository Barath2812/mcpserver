"""
MongoDB client for web scraper data storage.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import sys
sys.path.insert(0, 'd:\\mcp')

from config import (
    MONGODB_URI,
    MONGODB_DATABASE,
    MONGODB_SCRAPED_COLLECTION,
    MONGODB_LOGS_COLLECTION,
    MONGODB_PAPERS_COLLECTION,
)


class MongoDBClient:
    """
    MongoDB client for managing scraped data and logs.
    """
    
    def __init__(
        self,
        uri: str = MONGODB_URI,
        database: str = MONGODB_DATABASE,
    ):
        """
        Initialize MongoDB client.
        
        Args:
            uri: MongoDB connection URI
            database: Database name
        """
        self.uri = uri
        self.database_name = database
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
    
    def connect(self) -> None:
        """Connect to MongoDB."""
        if self._client is None:
            self._client = MongoClient(self.uri)
            self._db = self._client[self.database_name]
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    @property
    def db(self) -> Database:
        """Get the database instance."""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def scraped_data(self) -> Collection:
        """Get the scraped_data collection."""
        return self.db[MONGODB_SCRAPED_COLLECTION]
    
    @property
    def scrape_logs(self) -> Collection:
        """Get the scrape_logs collection."""
        return self.db[MONGODB_LOGS_COLLECTION]
    
    @property
    def research_papers(self) -> Collection:
        """Get the research_papers collection."""
        return self.db[MONGODB_PAPERS_COLLECTION]
    
    def insert_scraped_data(self, data: Dict[str, Any]) -> str:
        """
        Insert scraped data into MongoDB.
        
        Args:
            data: Scraped data document
        
        Returns:
            Inserted document ID as string
        """
        result = self.scraped_data.insert_one(data)
        return str(result.inserted_id)
    
    def insert_log(
        self,
        url: str,
        success: bool,
        error: Optional[str] = None
    ) -> str:
        """
        Insert a scrape log entry.
        
        Args:
            url: The scraped URL
            success: Whether the scrape was successful
            error: Error message if failed
        
        Returns:
            Inserted document ID as string
        """
        log_entry = {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "error": error,
        }
        result = self.scrape_logs.insert_one(log_entry)
        return str(result.inserted_id)
    
    def get_scraped_data_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get scraped data for a specific URL.
        
        Args:
            url: The URL to look up
        
        Returns:
            Document or None if not found
        """
        document = self.scraped_data.find_one({"url": url})
        if document:
            document["_id"] = str(document["_id"])
        return document
    
    def get_recent_scraped_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently scraped data.
        
        Args:
            limit: Maximum number of documents to return
        
        Returns:
            List of documents
        """
        cursor = self.scraped_data.find().sort("scraped_at", -1).limit(limit)
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
    
    def get_logs(
        self,
        url: Optional[str] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get scrape logs.
        
        Args:
            url: Filter by URL (optional)
            success_only: Only return successful scrapes
            limit: Maximum number of logs to return
        
        Returns:
            List of log documents
        """
        query = {}
        if url:
            query["url"] = url
        if success_only:
            query["success"] = True
        
        cursor = self.scrape_logs.find(query).sort("timestamp", -1).limit(limit)
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_scraped = self.scraped_data.count_documents({})
        static_count = self.scraped_data.count_documents({"scraper_type": "static"})
        dynamic_count = self.scraped_data.count_documents({"scraper_type": "dynamic"})
        
        total_logs = self.scrape_logs.count_documents({})
        success_count = self.scrape_logs.count_documents({"success": True})
        failure_count = self.scrape_logs.count_documents({"success": False})
        
        return {
            "total_scraped": total_scraped,
            "static_scrapes": static_count,
            "dynamic_scrapes": dynamic_count,
            "total_logs": total_logs,
            "successful_scrapes": success_count,
            "failed_scrapes": failure_count,
            "success_rate": round(success_count / total_logs * 100, 2) if total_logs > 0 else 0,
        }
    
    # ===============================
    # Research Paper Methods
    # ===============================
    
    def insert_paper(self, paper_data: Dict[str, Any]) -> str:
        """Insert a research paper into MongoDB."""
        result = self.research_papers.insert_one(paper_data)
        return str(result.inserted_id)
    
    def insert_papers(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Bulk insert research papers."""
        if not papers:
            return []
        result = self.research_papers.insert_many(papers)
        return [str(id) for id in result.inserted_ids]
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get a paper by its MongoDB _id."""
        from bson import ObjectId
        try:
            document = self.research_papers.find_one({"_id": ObjectId(paper_id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except Exception:
            return None
    
    def get_papers_by_topic(self, topic: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get papers by topic/query."""
        cursor = self.research_papers.find(
            {"topic": {"$regex": topic, "$options": "i"}}
        ).sort("stored_at", -1).limit(limit)
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
    
    def get_recent_papers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently stored papers."""
        cursor = self.research_papers.find(
            {}, {"extracted_text": 0}  # Exclude large text field
        ).sort("stored_at", -1).limit(limit)
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
    
    def search_papers_text(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search papers by title or abstract text."""
        cursor = self.research_papers.find(
            {"$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"abstract": {"$regex": query, "$options": "i"}},
            ]},
            {"extracted_text": 0}
        ).sort("stored_at", -1).limit(limit)
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
    
    def get_research_stats(self) -> Dict[str, Any]:
        """Get research statistics."""
        total_papers = self.research_papers.count_documents({})
        arxiv_count = self.research_papers.count_documents({"source": "arxiv"})
        ss_count = self.research_papers.count_documents({"source": "semantic_scholar"})
        
        # Get unique topics
        topics = self.research_papers.distinct("topic")
        
        return {
            "total_papers": total_papers,
            "arxiv_papers": arxiv_count,
            "semantic_scholar_papers": ss_count,
            "topics": topics,
            "unique_topics": len(topics),
        }
    
    def clear_all(self) -> Dict[str, int]:
        """
        Clear all data (for testing purposes).
        
        Returns:
            Count of deleted documents
        """
        scraped_deleted = self.scraped_data.delete_many({}).deleted_count
        logs_deleted = self.scrape_logs.delete_many({}).deleted_count
        papers_deleted = self.research_papers.delete_many({}).deleted_count
        return {
            "scraped_data_deleted": scraped_deleted,
            "logs_deleted": logs_deleted,
            "papers_deleted": papers_deleted,
        }


# Global client instance
_global_client: Optional[MongoDBClient] = None


def get_mongodb_client() -> MongoDBClient:
    """Get the global MongoDB client instance."""
    global _global_client
    if _global_client is None:
        _global_client = MongoDBClient()
    return _global_client

# AI-Driven Universal Web Data Extraction Platform

A production-grade, MCP-enabled universal web scraping platform with MongoDB storage and advanced anti-bot (antigravity) mechanisms.

## 🎯 Features

- **Dual Scraping Engines**: Static (Requests + BeautifulSoup) and Dynamic (Playwright)
- **Auto-Detection**: Automatically selects the appropriate scraper based on page content
- **Anti-Bot Protection**: User-Agent rotation, rate limiting, robots.txt compliance, stealth mode
- **MongoDB Storage**: Persists all scraped data with full metadata
- **MCP Integration**: Exposes scraping as tools for LLM invocation
- **Export Options**: JSON and CSV export capabilities

## 📁 Project Structure

```
d:\mcp\
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration settings
├── main.py                   # FastAPI MCP server entry point
├── scraper/
│   ├── static_scraper.py     # Requests + BeautifulSoup scraper
│   ├── dynamic_scraper.py    # Playwright scraper
│   └── strategy_selector.py  # Auto-detection logic
├── antigravity/
│   ├── user_agents.py        # User-Agent rotation
│   ├── throttle.py           # Request delays & rate limiting
│   ├── robots_validator.py   # robots.txt compliance
│   └── stealth.py            # Playwright stealth configuration
├── database/
│   ├── mongodb.py            # MongoDB connection & operations
│   └── models.py             # Pydantic data models
├── mcp/
│   └── tools.py              # MCP tool definitions
├── utils/
│   ├── normalizer.py         # Data normalization
│   └── exporter.py           # CSV/JSON export
├── tests/                    # Test suite
└── docs/
    └── README.md             # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd d:\mcp
pip install -r requirements.txt
playwright install chromium
```

### 2. Start MongoDB

Ensure MongoDB is running on `localhost:27017` (or update `MONGODB_URI` in `config.py`).

### 3. Run the Server

```bash
python main.py
```

The server will start at `http://localhost:8000`.

### 4. Test the API

Open `http://localhost:8000/docs` for interactive Swagger documentation.

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scrape` | POST/GET | Scrape a website |
| `/stats` | GET | Get scraping statistics |
| `/recent` | GET | Get recently scraped data |
| `/logs` | GET | Get scrape logs |
| `/export/json` | POST | Export data to JSON |
| `/export/csv` | POST | Export data to CSV |
| `/health` | GET | Health check |

### Example Scrape Request

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "auto_detect": true}'
```

## 🧠 MCP Tool Usage

The platform exposes a `scrape_website` tool via MCP:

```python
# Tool Schema
{
    "name": "scrape_website",
    "parameters": {
        "url": "string (required)",
        "dynamic": "boolean (default: false)",
        "auto_detect": "boolean (default: true)",
        "store_in_mongodb": "boolean (default: true)"
    }
}
```

## 🛡️ Anti-Bot (Antigravity) Features

1. **User-Agent Rotation**: 20+ realistic browser User-Agents
2. **Request Throttling**: 1-5 second random delays between requests
3. **Rate Limiting**: Max 10 requests per domain per minute
4. **robots.txt Compliance**: Respects crawling restrictions
5. **Playwright Stealth Mode**: Disables automation detection flags

## 📊 MongoDB Schema

### scraped_data Collection
```json
{
  "_id": "ObjectId",
  "url": "string",
  "scraped_at": "ISO timestamp",
  "scraper_type": "static | dynamic",
  "content": {
    "title": "string",
    "text": "string",
    "links": ["string"]
  },
  "metadata": {
    "status_code": "number",
    "response_time": "number",
    "user_agent": "string"
  }
}
```

### scrape_logs Collection
```json
{
  "url": "string",
  "timestamp": "ISO timestamp",
  "success": "boolean",
  "error": "string | null"
}
```

## 🧪 Running Tests

```bash
cd d:\mcp
pytest tests/ -v
```

## ⚖️ Ethical Considerations

- Always respects `robots.txt` directives
- Implements polite crawling with delays
- Only scrapes publicly accessible content
- Rate limiting prevents server overload
- Designed for responsible use

## 📋 Limitations

- Cannot bypass authentication or CAPTCHAs
- JavaScript-heavy SPAs may require dynamic scraping
- Some sites may detect and block scraping despite stealth measures
- Rate limiting may slow down bulk operations

## 🔮 Future Scope

- Proxy rotation support
- CAPTCHA solving integration
- Distributed scraping with task queues
- Advanced content extraction (structured data, tables)
- Scheduled/recurring scrapes
- WebSocket real-time updates

## 📄 License

This project is for educational purposes.

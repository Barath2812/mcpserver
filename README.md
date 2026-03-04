# 🌐 AI-Driven Universal Web Data Extraction Platform

A production-grade, MCP-enabled universal web scraping platform built with **FastAPI**, **MongoDB**, and **Playwright**. It features intelligent scraper auto-detection, advanced anti-bot mechanisms, and a sleek frontend dashboard.

---

## ✨ Features

- **Static Scraping** — Requests + BeautifulSoup for traditional HTML pages
- **Dynamic Scraping** — Playwright for JavaScript-rendered pages
- **Auto-Detection** — Automatically selects the appropriate scraper strategy
- **Anti-Bot Protection** — User-Agent rotation, rate limiting, robots.txt compliance
- **MongoDB Storage** — Persists all scraped data with rich metadata
- **MCP Integration** — Exposes scraping as tools for LLM invocation
- **Data Export** — Export scraped data to JSON or CSV
- **Frontend Dashboard** — Built-in web UI for managing scrapes

---

## 📁 Project Structure

```
mcp/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration settings
├── mcp_server.py           # MCP server setup
├── mcp_config.json         # MCP configuration
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata & build config
├── antigravity/            # Anti-bot & stealth modules
│   ├── stealth.py          # Stealth browsing utilities
│   ├── throttle.py         # Request throttling / rate limiting
│   ├── robots_validator.py # robots.txt compliance checker
│   └── user_agents.py      # User-Agent rotation
├── database/               # Database layer
│   ├── models.py           # Pydantic data models
│   └── mongodb.py          # MongoDB client & operations
├── scraper/                # Core scraping engines
│   ├── static_scraper.py   # BeautifulSoup-based scraper
│   ├── dynamic_scraper.py  # Playwright-based scraper
│   └── strategy_selector.py# Auto-detection logic
├── scraper_mcp/            # MCP tool wrappers
├── frontend/               # Web dashboard (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── utils/                  # Utility modules
│   ├── exporter.py         # JSON/CSV export
│   └── normalizer.py       # Data normalization
├── tests/                  # Test suite
└── docs/                   # Documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** ≥ 3.10
- **MongoDB** running locally (default: `mongodb://localhost:27017`)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd mcp
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv mcpvenv
   # Windows
   mcpvenv\Scripts\activate
   # macOS / Linux
   source mcpvenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Set environment variables** (optional)
   ```bash
   # Override defaults via .env or shell
   export MONGODB_URI="mongodb://localhost:27017"
   ```

### Running the Server

```bash
python main.py
```

The server starts at **http://localhost:8000**. Open it in a browser to access the dashboard.

---

## 📡 API Endpoints

| Method | Endpoint        | Description                        |
|--------|-----------------|------------------------------------|
| GET    | `/`             | Frontend dashboard                 |
| GET    | `/api`          | API information                    |
| POST   | `/scrape`       | Scrape a website (JSON body)       |
| GET    | `/scrape`       | Scrape a website (query params)    |
| GET    | `/stats`        | Scraping statistics                |
| GET    | `/recent`       | Recently scraped data              |
| GET    | `/logs`         | Scrape logs                        |
| POST   | `/export/json`  | Export data to JSON                |
| POST   | `/export/csv`   | Export data to CSV                 |
| GET    | `/health`       | Health check                       |
| GET    | `/docs`         | Swagger API documentation          |

---

## ⚙️ Configuration

All configuration is managed in `config.py`:

| Setting                  | Default                         | Description                    |
|--------------------------|---------------------------------|--------------------------------|
| `MONGODB_URI`            | `mongodb://localhost:27017`     | MongoDB connection string      |
| `SERVER_HOST`            | `0.0.0.0`                      | Server bind host               |
| `SERVER_PORT`            | `8000`                          | Server bind port               |
| `PLAYWRIGHT_HEADLESS`    | `True`                          | Run browser in headless mode   |
| `PLAYWRIGHT_TIMEOUT`     | `30000` ms                      | Page load timeout              |
| `MAX_REQUESTS_PER_DOMAIN_PER_MINUTE` | `10`               | Rate limit per domain          |

---

## 🧪 Running Tests

```bash
pytest
```

---

## 🛡️ Ethical Scraping

This platform is designed with ethical scraping in mind:

- ✅ Respects `robots.txt` directives
- ✅ Implements polite crawling with configurable delays
- ✅ Rate-limits requests per domain
- ✅ Rotates User-Agents to reduce server load patterns

---

## 🛠️ Tech Stack

- **FastAPI** — High-performance async web framework
- **Playwright** — Browser automation for dynamic content
- **BeautifulSoup** — HTML parsing for static content
- **MongoDB + PyMongo** — Document storage
- **MCP (Model Context Protocol)** — LLM tool integration
- **Pydantic** — Data validation & serialization

---

## 📄 License

This project is for educational and personal use.

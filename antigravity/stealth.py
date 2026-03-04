"""
Playwright stealth configuration for anti-bot detection.
"""
import random
from typing import Any
import sys
sys.path.insert(0, 'd:\\mcp')
from config import USER_AGENTS, VIEWPORT_SIZES, PLAYWRIGHT_HEADLESS


def get_stealth_browser_config() -> dict[str, Any]:
    """
    Get stealth configuration for Playwright browser.
    
    Returns:
        Dictionary of browser launch options
    """
    return {
        "headless": PLAYWRIGHT_HEADLESS,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--window-size=1920,1080",
        ],
    }


def get_stealth_context_config() -> dict[str, Any]:
    """
    Get stealth configuration for Playwright browser context.
    
    Returns:
        Dictionary of context options
    """
    viewport = random.choice(VIEWPORT_SIZES)
    user_agent = random.choice(USER_AGENTS)
    
    return {
        "viewport": viewport,
        "user_agent": user_agent,
        "locale": random.choice(["en-US", "en-GB", "en-CA"]),
        "timezone_id": random.choice([
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
        ]),
        "permissions": [],
        "geolocation": None,
        "color_scheme": random.choice(["light", "dark"]),
        "java_script_enabled": True,
        "bypass_csp": False,
        "ignore_https_errors": False,
        # Disable various detection mechanisms
        "extra_http_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        },
    }


async def apply_stealth_scripts(page: Any) -> None:
    """
    Apply stealth scripts to a Playwright page to avoid detection.
    
    Args:
        page: Playwright page object
    """
    # Override navigator.webdriver
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # Override navigator.plugins
    await page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                }
            ]
        });
    """)
    
    # Override navigator.languages
    await page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    # Override chrome runtime
    await page.add_init_script("""
        window.chrome = {
            runtime: {},
        };
    """)
    
    # Override permissions
    await page.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)


def get_random_mouse_movements() -> list[tuple[int, int]]:
    """
    Generate random mouse movement coordinates for human-like behavior.
    
    Returns:
        List of (x, y) coordinate tuples
    """
    movements = []
    current_x, current_y = random.randint(100, 500), random.randint(100, 500)
    
    for _ in range(random.randint(3, 7)):
        # Add some randomness to movement
        current_x += random.randint(-100, 100)
        current_y += random.randint(-100, 100)
        
        # Keep within reasonable bounds
        current_x = max(0, min(1920, current_x))
        current_y = max(0, min(1080, current_y))
        
        movements.append((current_x, current_y))
    
    return movements

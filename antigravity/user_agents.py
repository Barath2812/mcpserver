"""
User-Agent rotation for anti-bot detection evasion.
"""
import random
from typing import Optional
import sys
sys.path.insert(0, 'd:\\mcp')
from config import USER_AGENTS


def get_random_user_agent(exclude: Optional[str] = None) -> str:
    """
    Get a random User-Agent string from the configured list.
    
    Args:
        exclude: Optional User-Agent to exclude from selection
                 (useful to ensure different UA from previous request)
    
    Returns:
        A randomly selected User-Agent string
    """
    available_agents = USER_AGENTS.copy()
    
    if exclude and exclude in available_agents:
        available_agents.remove(exclude)
    
    return random.choice(available_agents)


def get_user_agent_for_platform(platform: str = "desktop") -> str:
    """
    Get a User-Agent appropriate for a specific platform.
    
    Args:
        platform: One of 'desktop', 'mobile', 'tablet'
    
    Returns:
        A User-Agent string matching the requested platform
    """
    platform_patterns = {
        "desktop": ["Windows NT", "Macintosh", "X11"],
        "mobile": ["iPhone", "Android", "Mobile"],
        "tablet": ["iPad", "Tablet"],
    }
    
    patterns = platform_patterns.get(platform, platform_patterns["desktop"])
    
    matching_agents = [
        ua for ua in USER_AGENTS
        if any(pattern in ua for pattern in patterns)
    ]
    
    return random.choice(matching_agents) if matching_agents else get_random_user_agent()

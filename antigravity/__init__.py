"""
Antigravity module - Anti-bot detection mechanisms.
"""
from .user_agents import get_random_user_agent
from .throttle import random_delay, RateLimiter
from .robots_validator import RobotsValidator, is_allowed
from .stealth import get_stealth_browser_config

__all__ = [
    "get_random_user_agent",
    "random_delay",
    "RateLimiter",
    "RobotsValidator",
    "is_allowed",
    "get_stealth_browser_config",
]

"""
Redis-based rate limiting for production environments.
Uses sliding window algorithm for accurate rate limiting.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from aioredis import Redis, from_url
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Production-grade rate limiter using Redis."""
    
    def __init__(self, redis_url: str, requests_per_minute: int = 30):
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.redis: Optional[Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis = await from_url(self.redis_url, encoding="utf8", decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Redis rate limiter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a request."""
        if not self.redis:
            logger.warning("Redis not initialized, allowing request")
            return True
        
        try:
            now = datetime.now()
            window_start = (now - timedelta(seconds=self.window_size)).timestamp()
            key = f"rate_limit:{user_id}"
            
            # Remove old entries outside the window
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            count = await self.redis.zcard(key)
            
            if count < self.requests_per_minute:
                # Add new request
                await self.redis.zadd(key, {str(now.timestamp()): now.timestamp()})
                # Set expiry
                await self.redis.expire(key, self.window_size * 2)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Fail open - allow request on error
    
    async def get_remaining(self, user_id: int) -> int:
        """Get remaining requests for user."""
        if not self.redis:
            return self.requests_per_minute
        
        try:
            key = f"rate_limit:{user_id}"
            count = await self.redis.zcard(key)
            return max(0, self.requests_per_minute - count)
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return self.requests_per_minute
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()


class RateLimitMiddleware(BaseMiddleware):
    """Middleware for rate limiting with Redis."""
    
    def __init__(self, limiter: RedisRateLimiter):
        self.limiter = limiter
        super().__init__()
    
    async def __call__(self, handler, event: TelegramObject, data):
        user_id = self._get_user_id(event)
        
        if not user_id:
            return await handler(event, data)
        
        # Check rate limit
        allowed = await self.limiter.is_allowed(user_id)
        
        if not allowed:
            if isinstance(event, Message):
                await event.answer(
                    "⏰ *Rate limit exceeded*\nPlease wait a moment before sending more requests.",
                    parse_mode="Markdown"
                )
                logger.warning(f"Rate limit exceeded for user {user_id}")
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⏰ Too many requests. Please wait.",
                    show_alert=False
                )
            return
        
        return await handler(event, data)
    
    def _get_user_id(self, event: TelegramObject) -> Optional[int]:
        """Extract user ID from event."""
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None
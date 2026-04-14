"""
Security headers middleware for aiohttp.
Implements industry best practices for security.
"""
import logging
from aiohttp import web
from typing import Callable

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""
    
    # Standard security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    @web.middleware
    async def middleware(self, request: web.Request, handler: Callable) -> web.Response:
        """Add security headers to response."""
        try:
            response = await handler(request)
            
            # Add security headers
            for header, value in self.SECURITY_HEADERS.items():
                response.headers[header] = value
            
            # Additional headers
            response.headers['X-Request-ID'] = request.headers.get('X-Request-ID', 'no-id')
            
            return response
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security headers middleware error: {e}")
            return web.Response(
                text="<h1>500 Internal Server Error</h1>",
                content_type='text/html',
                status=500
            )


class CORSMiddleware:
    """CORS middleware for aiohttp."""
    
    def __init__(self, allowed_origins: list = None, allow_credentials: bool = True):
        self.allowed_origins = allowed_origins or ['https://example.com']
        self.allow_credentials = allow_credentials
    
    @web.middleware
    async def middleware(self, request: web.Request, handler: Callable) -> web.Response:
        """Handle CORS preflight and add CORS headers."""
        # Handle preflight requests
        if request.method == 'OPTIONS':
            return self._handle_preflight(request)
        
        try:
            response = await handler(request)
            self._add_cors_headers(response, request)
            return response
        except web.HTTPException as e:
            response = e
            self._add_cors_headers(response, request)
            raise
        except Exception as e:
            logger.error(f"CORS middleware error: {e}")
            return web.Response(
                text='<h1>500 Internal Server Error</h1>',
                content_type='text/html',
                status=500
            )
    
    def _handle_preflight(self, request: web.Request) -> web.Response:
        """Handle CORS preflight requests."""
        response = web.Response()
        self._add_cors_headers(response, request)
        return response
    
    def _add_cors_headers(self, response: web.Response, request: web.Request):
        """Add CORS headers to response."""
        origin = request.headers.get('Origin', '')
        
        if origin in self.allowed_origins or '*' in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            if self.allow_credentials:
                response.headers['Access-Control-Allow-Credentials'] = 'true'
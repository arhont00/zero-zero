"""
Production-ready web application with security headers, CORS, and proper error handling.
"""
import os
import logging
import aiohttp
from aiohttp import web
from pathlib import Path
from datetime import datetime
import sqlite3
from html import escape
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

# Import security modules
from security_headers import SecurityHeadersMiddleware, CORSMiddleware
from input_validator import InputValidator
from audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Пути
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates'
STATIC_DIR = Path(__file__).resolve().parent / 'static'
KB_DIR = BASE_DIR / 'content' / 'knowledge_base'

# Initialize audit logger
audit_logger = AuditLogger(BASE_DIR / 'logs' / 'web_audit.log')

def get_db_path():
    from config import Config
    return Config.DB_PATH


def db_query(sql, params=()):
    """Выполнить запрос к БД с обработкой ошибок."""
    try:
        conn = sqlite3.connect(str(get_db_path()), timeout=10)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(sql, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except sqlite3.DatabaseError as e:
        logger.error(f"DB error: {e}")
        audit_logger.log_security_incident('DATABASE_ERROR', None, {'error': str(e)})
        return []
    except Exception as e:
        logger.error(f"Unexpected error in db_query: {e}")
        audit_logger.log_security_incident('UNEXPECTED_ERROR', None, {'error': str(e)})
        return []


def escape_html(text: str) -> str:
    """Безопасное экранирование HTML."""
    if not isinstance(text, str):
        text = str(text) if text else ''
    return escape(text)


def load_all_stones():
    """Загрузить все камни из файлов с обработкой ошибок."""
    stones = {}
    try:
        if not KB_DIR.exists():
            logger.warning(f"Knowledge base directory not found: {KB_DIR}")
            return stones
        
        for f in sorted(KB_DIR.glob('*.txt'))[:100]:  # Лимит для безопасности
            try:
                stone_id = f.stem
                data = {}
                current_key = None
                current_lines = []
                
                for line in f.read_text(encoding='utf-8', errors='ignore').split('\n'):
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        if current_key:
                            data[current_key] = '\n'.join(current_lines).strip()
                        current_key = line[1:-1]
                        current_lines = []
                    elif current_key:
                        current_lines.append(line)
                
                if current_key:
                    data[current_key] = '\n'.join(current_lines).strip()
                if data:
                    stones[stone_id] = data
            except Exception as e:
                logger.error(f"Error loading stone {f.name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error loading stones: {e}")
    
    return stones


def render_template(name, **ctx):
    """Безопасный рендер шаблона с методом jinja2."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )
        tmpl = env.get_template(name)
        return tmpl.render(**ctx)
    except Exception as e:
        logger.error(f"Template render error: {e}")
        # Fallback: базовой рендер с экранированием
        tmpl_path = TEMPLATES_DIR / name
        with open(tmpl_path, encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for key, val in ctx.items():
            safe_val = escape_html(val) if val is not None else ''
            content = content.replace('{{ ' + key + ' }}', safe_val)
            content = content.replace('{{' + key + '}}', safe_val)
        
        return content


async def handle_static(request):
    """Отдача статических файлов с проверкой безопасности."""
    try:
        filename = request.match_info['filename']
        # Проверка path traversal
        if '..' in filename or filename.startswith('/'):
            audit_logger.log_security_incident('PATH_TRAVERSAL_ATTEMPT', None, {'filename': filename})
            raise web.HTTPForbidden()
        
        filepath = (STATIC_DIR / filename).resolve()
        static_root = STATIC_DIR.resolve()
        
        if not filepath.exists() or filepath.is_dir():
            raise web.HTTPNotFound()
        
        # Проверяем, что файл внутри STATIC_DIR
        if not str(filepath).startswith(str(static_root)):
            audit_logger.log_security_incident('PATH_TRAVERSAL_ATTEMPT', None, {'filepath': str(filepath)})
            raise web.HTTPForbidden()
        
        return web.FileResponse(filepath, headers={
            'Cache-Control': 'public, max-age=86400'
        })
    except web.HTTPException:
        raise
    except Exception as e:
        logger.error(f"Static file error: {e}")
        raise web.HTTPInternalServerError()


async def handle_index(request):
    """Главная страница."""
    try:
        # Load data safely
        stones = load_all_stones()
        total_stones = len(stones)
        
        # Get products (simplified)
        products = db_query("""
            SELECT si.*, sc.name as collection_name, sc.emoji
            FROM showcase_items si
            JOIN showcase_collections sc ON si.collection_id = sc.id
            ORDER BY si.created_at DESC
            LIMIT 6
        """)
        
        html = render_template('index.html',
            total_stones=total_stones,
            products=products
        )
        
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except Exception as e:
        logger.error(f"Index page error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'index', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_catalog(request):
    """Каталог товаров."""
    try:
        collection_id = request.rel_url.query.get('collection', '')
        search = request.rel_url.query.get('q', '').lower().strip()[:100]
        
        # Validate inputs
        if collection_id and not InputValidator.validate_slug(collection_id):
            audit_logger.log_security_incident('INVALID_INPUT', None, {'input': collection_id})
            raise web.HTTPBadRequest(text="Invalid collection ID")
        
        if search and not InputValidator.validate_string(search, max_length=100):
            audit_logger.log_security_incident('INVALID_INPUT', None, {'input': search})
            raise web.HTTPBadRequest(text="Invalid search query")
        
        # Build query safely
        query = """
            SELECT si.*, sc.name as collection_name, sc.emoji
            FROM showcase_items si
            JOIN showcase_collections sc ON si.collection_id = sc.id
        """
        params = []
        
        if collection_id:
            query += " WHERE si.collection_id = ?"
            params.append(collection_id)
        elif search:
            query += " WHERE LOWER(si.name) LIKE ? OR LOWER(si.description) LIKE ?"
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY si.created_at DESC"
        
        collections = db_query("SELECT * FROM showcase_collections ORDER BY sort_order")
        products = db_query(query, params)
        active_col = collection_id
        
        html = render_template('catalog.html',
            collections=collections,
            products=products,
            active_col=active_col
        )
        
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except Exception as e:
        logger.error(f"Catalog page error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'catalog', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_stones(request):
    """База знаний о камнях."""
    try:
        stones = load_all_stones()
        search = request.rel_url.query.get('q', '').lower().strip()[:100]
        
        # Validate search input
        if search and not InputValidator.validate_string(search, max_length=100):
            audit_logger.log_security_incident('INVALID_INPUT', None, {'input': search})
            raise web.HTTPBadRequest(text="Invalid search query")
        
        if search:
            filtered = {
                sid: d for sid, d in stones.items()
                if search in d.get('TITLE', '').lower()
                or search in d.get('PROPERTIES', '').lower()
                or search in d.get('SHORT_DESC', '').lower()
            }
        else:
            filtered = stones
        
        html = render_template('stones.html',
            stones=filtered,
            search=search,
            total=len(filtered)
        )
        
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except Exception as e:
        logger.error(f"Stones page error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'stones', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_stone_detail(request):
    """Карточка камня."""
    try:
        stone_id = request.match_info.get('stone_id', '')
        
        # Validate stone_id
        if not stone_id or len(stone_id) > 50 or not InputValidator.validate_slug(stone_id):
            audit_logger.log_security_incident('INVALID_INPUT', None, {'stone_id': stone_id})
            raise web.HTTPBadRequest(text="Invalid stone ID")
        
        stones = load_all_stones()
        stone = stones.get(stone_id)
        
        if not stone:
            raise web.HTTPNotFound()
        
        html = render_template('stone_detail.html', stone=stone, stone_id=stone_id)
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except web.HTTPNotFound:
        raise
    except Exception as e:
        logger.error(f"Stone detail error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'stone_detail', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_quiz(request):
    """Страница квиза."""
    try:
        html = render_template('quiz.html')
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except Exception as e:
        logger.error(f"Quiz page error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'quiz', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_order(request):
    """Страница заказа."""
    try:
        stone_id = request.rel_url.query.get('stone', '')
        
        # Validate stone_id if provided
        if stone_id and not InputValidator.validate_slug(stone_id):
            audit_logger.log_security_incident('INVALID_INPUT', None, {'stone_id': stone_id})
            raise web.HTTPBadRequest(text="Invalid stone ID")
        
        html = render_template('order.html', stone_id=stone_id)
        return web.Response(text=html, content_type='text/html', charset='utf-8')
    except Exception as e:
        logger.error(f"Order page error: {e}")
        audit_logger.log_security_incident('PAGE_ERROR', None, {'page': 'order', 'error': str(e)})
        return web.Response(text="<h1>500 Internal Server Error</h1>",
                          content_type='text/html', status=500)


async def handle_404(request):
    """Обработчик 404 ошибок."""
    return web.Response(
        text="<h1>404 Not Found</h1><p>Страница не найдена</p>",
        content_type='text/html',
        status=404
    )


async def handle_500(request):
    """Обработчик 500 ошибок."""
    return web.Response(
        text="<h1>500 Internal Server Error</h1><p>Произошла ошибка на сервере</p>",
        content_type='text/html',
        status=500
    )


def create_app():
    """Создание приложения с безопасностью."""
    app = web.Application(
        client_max_size=1024*1024,  # 1MB limit
        middlewares=[
            SecurityHeadersMiddleware().middleware,
            CORSMiddleware(allowed_origins=['https://example.com']).middleware,
        ]
    )
    
    # Routes
    app.router.add_get('/', handle_index)
    app.router.add_get('/catalog', handle_catalog)
    app.router.add_get('/stones', handle_stones)
    app.router.add_get('/stones/{stone_id}', handle_stone_detail)
    app.router.add_get('/quiz', handle_quiz)
    app.router.add_get('/order', handle_order)
    app.router.add_get('/static/{filename}', handle_static)
    
    # Error handlers
    app.router.add_get('/{path:.*}', handle_404)
    
    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)
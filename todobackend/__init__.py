import asyncio
from logging import getLogger, basicConfig, INFO
from os import getenv
from aiohttp import web
import aiohttp_cors
from aiohttp_swagger import setup_swagger
if getenv('MODEL','redis') == 'dict':
    from .views import (
        IndexView,
        TodoView,
        TagIndexView,
        TagView,
        TodoTagsIndexView,
        TodoTagsView,
        TagsTodoIndexView
    )
    print('**DICT MODEL in use...**')
else:
    from .redis_views import (
        IndexView,
        TodoView,
        TagIndexView,
        TagView,
        TodoTagsIndexView,
        TodoTagsView,
        TagsTodoIndexView
    )
    print('** REDIS MODEL in use...**')


IP = getenv('IP', '0.0.0.0')
PORT = getenv('PORT', '8000')

basicConfig(level=INFO)
logger = getLogger(__name__)


def start_redis_pool(app):
    app['redis_listener']=asyncio.create_task(Task.get_connection_pool())

async def shutdown_redis_pool(app):
    await Task.close_connection()
    app['redis_listener'].cancel()
    await app['redis_listener']


async def init(loop):
    app = web.Application()
    app.on_startup.append(start_redis_pool(app))
    app.on_cleanup.append(shutdown_redis_pool(app))

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
    })

    # Routes
    cors.add(
        app.router.add_route('*', '/todos/', IndexView),
        webview=True)
    cors.add(
        app.router.add_route('*', '/todos/{uuid}', TodoView, name='todo'),
        webview=True)
    cors.add(
        app.router.add_route('*', '/tags/', TagIndexView),
        webview=True)
    cors.add(
        app.router.add_route('*', '/tags/{uuid}', TagView, name='tag'),
        webview=True)
    cors.add(
        app.router.add_route('*', '/todos/{uuid}/tags/', TodoTagsIndexView, name='todo_tag'),
        webview=True)
    cors.add(
        app.router.add_route('*', '/todos/{uuid_todos}/tags/{uuid_tags}', TodoTagsView),
        webview=True)
    cors.add(
        app.router.add_route('GET', '/tags/{uuid}/todos/', TagsTodoIndexView),
        webview=True)

    # Config
    setup_swagger(app, swagger_url="/api/v1/doc", swagger_from_file="swagger.yaml")
    logger.info("Starting server at %s:%s", IP, PORT)
    srv = await loop.create_server(app.make_handler(), IP, PORT)


    return srv

from .redis_models import Task

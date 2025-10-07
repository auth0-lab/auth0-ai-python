import asyncio
from asgiref.wsgi import WsgiToAsgi
from hypercorn.config import Config
from hypercorn.asyncio import serve
from src.app.app import app


def main():
    config = Config()
    config.bind = ["0.0.0.0:3000"]
    config.worker_class = "asyncio"
    config.use_reloader = True

    asyncio.run(serve(WsgiToAsgi(app), config))

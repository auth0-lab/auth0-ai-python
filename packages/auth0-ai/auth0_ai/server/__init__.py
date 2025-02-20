"""
Auth0 AI Server Module
Internal module for handling OAuth callback server and routes.
"""
from .auth_server import AuthServer
from .routes import setup_routes

__all__ = ["AuthServer","setup_routes"] 

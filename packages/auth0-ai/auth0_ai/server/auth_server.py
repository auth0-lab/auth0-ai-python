from __future__ import annotations
import threading
import urllib.parse
from typing import Any

import uvicorn
import os
from fastapi import FastAPI

from .routes import setup_routes

class AuthServer:
    """
    FastAPI server handling Auth0 callbacks and authentication routes.
    """
    
    def __init__(self, auth_client: Any):
        """
        Initialize the authentication server.
        
        Args:
            auth_client: The parent AIAuth instance
        """
        self.auth_client = auth_client
        self.app = FastAPI()
        
        # Parse redirect URI for server config
        parsed_uri = urllib.parse.urlparse(auth_client.redirect_uri)
        self.host = parsed_uri.hostname
        self.port = parsed_uri.port
        self.protocol = urllib.parse.urlparse(auth_client.redirect_uri).scheme
        
        # Setup routes with dependencies
        setup_routes(self.app, auth_client)
        self.start()

    def _is_valid_file(self,file_path) -> bool:
        """Check if the file exists and is accessible."""
        valid = False
        try: 
            valid = os.path.isfile(file_path) and os.access(file_path, os.R_OK)
            return valid
        except Exception as e:
            return valid

    
    def start(self):
        """Runs FastAPI as the middleware inside a separate thread."""
        if (self.protocol == "https"):

            ssl_keyfile = os.getenv("AUTH0_SSL_KEYFILE")
            ssl_certfile = os.getenv("AUTH0_SSL_CERTFILE")

            if not self._is_valid_file(ssl_keyfile) or not self._is_valid_file(ssl_certfile):
                raise ValueError(
                    "AUTH0_SSL_KEYFILE and AUTH0_SSL_CERTFILE environment variables must be set with valid file paths for HTTPS.")

            server_thread = threading.Thread(
                target=uvicorn.run,
                args=(self.app,),
                kwargs={
                    "host": self.host, 
                    "port": self.port, 
                    "ssl_keyfile": ssl_keyfile,  # Path to private key
                    "ssl_certfile": ssl_certfile,  # Path to certificate
                    "log_level": "error"},
                daemon=True  # Daemon mode so it exits when the main thread exits
            )
        else:
            server_thread = threading.Thread(
                target=uvicorn.run,
                args=(self.app,),
                kwargs={
                    "host": self.host, 
                    "port": self.port, 
                    "log_level": "info"},
                daemon=True  # Daemon mode so it exits when the main thread exits
            )
        try:
            server_thread.start()
        except Exception as e:
            print(f"Error starting middleware server: {str(e)}")
            raise e    
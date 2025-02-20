from __future__ import annotations
from typing import Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
import jwt


def setup_routes(app: FastAPI, auth_client: Any) -> None:
    """Set up all routes for the authentication server."""

    @app.get("/auth/callback")
    async def manage_callback(request: Request, response: Response):
        """Parses and validates callback URL query parameters."""
        query_params = request.query_params
        required_keys = {"code", "state"}

        if query_params.get("error"):
            error_description = query_params.get("error_description", "Unknown error occurred.")
            if query_params.get("state"):
                del auth_client.state_store[query_params.get("state")]
            raise HTTPException(status_code=400, detail=error_description)

        if not required_keys.issubset(query_params.keys()):
            raise HTTPException(status_code=400, detail="Missing required query parameters.")

        received_state = query_params["state"]

        # Validate state to prevent CSRF attacks
        if received_state not in auth_client.state_store:
            raise HTTPException(status_code=400, detail="Invalid or missing state parameter.")

        # Extract code value from query string
        received_code = query_params["code"]

        auth0_tokens = auth_client.token_manager.exchange_code_for_tokens(received_code)

        if auth0_tokens:
            cookie_data = await auth_client.session_manager.set_encrypted_session(auth0_tokens, state=received_state)

            response.set_cookie(
                key="session",
                value=cookie_data,
                httponly=True,  # Prevent JavaScript access
                # secure=True,  # Send only over HTTPS
                samesite="Lax",  # Protect against CSRF
                # set expiry based on access token expiry
                max_age=auth0_tokens["expires_in"],
            )

            user_id = auth_client.state_store[received_state].get("user_id", "failed")
            auth_client.state_store[received_state] = {"user_id": user_id, "is_completed": True}

            return {"message": "successful. you can now close this window"}

    @app.get("/auth/login")
    async def manage_login(request: Request, response: Response):
        """Handle login initiation."""
        # if scope is None:  # Original comment preserved
        scope = "openid profile email"
        connection = "Username-Password-Authentication"

        state = auth_client._generate_state()

        auth_url = auth_client.url_builder.get_authorize_url(
            state=state,
            connection=connection,
            scope=scope
        )

        return RedirectResponse(url=auth_url, status_code=302)

    @app.get("/auth/get_user")
    async def get_user(request: Request):
        """Reads the session cookie and extracts user info."""
        auth_cookie = request.cookies.get("session")

        if not auth_cookie:
            raise HTTPException(status_code=401, detail="Missing session cookie.")

        try:
            # Decode the JWT stored in the session cookie
            decoded_data = jwt.decode(auth_cookie, auth_client.secret_key, algorithms=["HS256"])

            # Extract the user ID (sub) from the decoded JWT
            user_id = decoded_data["user_id"]

            if not user_id:
                raise HTTPException(status_code=400, detail="Invalid session cookie: Missing 'sub' claim.")

            return JSONResponse(content=decoded_data)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session cookie has expired.")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid session cookie.")










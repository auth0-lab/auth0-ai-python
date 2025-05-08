from flask import request, jsonify, g
from auth0_api_python import ApiClient, ApiClientOptions
from functools import wraps

def get_token_auth_header():
    """Extracts the Access Token from the Authorization header."""
    auth = request.headers.get("Authorization", None)
    if not auth:
        return None
    parts = auth.split()

    if parts[0].lower() != "bearer" or len(parts) != 2:
        return None
    return parts[1]

def requires_auth(auth0_domain: str, audience: str):
    api_client = ApiClient(ApiClientOptions(
        domain=auth0_domain,
        audience=audience,
    ))
    
    def decorator(f):
        """Decorator to protect endpoints and inject decoded Access Token payload."""
        @wraps(f)
        async def decorated(*args, **kwargs):
            token = get_token_auth_header()
            if token is None:
                return jsonify({"error": "Authorization header missing or invalid"}), 401
            try:
                payload = await api_client.verify_access_token(access_token=token)
                g.access_token_payload = payload
            except Exception as e:
                return jsonify({"error": str(e)}), 401

            return f(*args, **kwargs)
        return decorated
    return decorator

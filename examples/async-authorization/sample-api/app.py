import json
import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from typing import List, Optional
from flask_cors import cross_origin
from jose import jwt
from six.moves.urllib.request import urlopen

load_dotenv()

app = Flask(__name__)

PORT = int(os.getenv("PORT", 8081))
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUDIENCE")

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected"}, 401)
    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": "Authorization header must start with Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header", "description": "Authorization header must be  Bearer token"}, 401)

    token = parts[1]
    return token

def requires_auth(scopes: Optional[List[str]] = None):

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_auth_header()
            jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
            jwks = json.loads(jsonurl.read())
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if not rsa_key:
                raise AuthError({"code": "invalid_header", "description": "unable to find appropriate key"}, 400)
            
            try:
                jwt_payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=API_AUDIENCE,
                    issuer="https://"+AUTH0_DOMAIN+"/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims", "description": "incorrect claims, please check the audience and issuer"}, 401)
            except Exception as e:
                raise AuthError({"code": "server_error", "description": "unable to verify access token"}, 400)
            
            is_authorized = not scopes or all(scope in jwt_payload.get("scope", "").strip().split() for scope in scopes)
            if not is_authorized:
                raise AuthError({"code": "insufficient_scope", "description": f"insufficient scope, expected: {' '.join(scopes)}"}, 403)

            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth(scopes=["stock:trade"])
def stock_purchase():
    print("Received request to purchase stock")
    return jsonify({"message": "Stock purchase request received"}), 200

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

if __name__ == '__main__':
    app.run(port=PORT)

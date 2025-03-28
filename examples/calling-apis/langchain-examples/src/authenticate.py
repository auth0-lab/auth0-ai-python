import os
import base64
import hashlib
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from auth0.authentication import GetToken
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_NATIVE_CLIENT_ID")
REDIRECT_URI = 'http://localhost:8000/callback'

def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode('utf-8')).digest()
    ).rstrip(b'=').decode('utf-8')
    return verifier, challenge

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/callback':
            params = parse_qs(parsed.query)
            CallbackHandler.auth_code = params.get('code', [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done! You can close this window now.")
        else:
            self.send_error(404)

def start_server():
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server.serve_forever()

def authenticate():
    verifier, challenge = generate_pkce_pair()

    auth_url = f"https://{AUTH0_DOMAIN}/authorize?" + urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid offline_access',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
    })

    threading.Thread(target=start_server, daemon=True).start()
    print("Opening browser for login...")
    webbrowser.open(auth_url)

    print("Waiting for authentication...")
    while CallbackHandler.auth_code is None:
        time.sleep(1)

    print("Got authorization code, exchanging for tokens...")

    token_client = GetToken(AUTH0_DOMAIN, CLIENT_ID)
    token_response = token_client.authorization_code_pkce(
        code=CallbackHandler.auth_code,
        code_verifier=verifier,
        redirect_uri=REDIRECT_URI
    )

    return token_response

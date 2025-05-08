from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from auth0.management import Auth0
from auth0.authentication.get_token import GetToken
from common.jwt_auth import requires_auth as requires_auth_decorator

load_dotenv()

app = Flask(__name__)

requires_auth = requires_auth_decorator(os.getenv("HR_AUTH0_DOMAIN"), os.getenv("HR_API_AUTH0_AUDIENCE"))

# TODO: replace HR_AGENT_AUTH0_CLIENT_ID/HR_AGENT_AUTH0_CLIENT_SECRET with a proper client
get_token = GetToken(domain=os.getenv("HR_AUTH0_DOMAIN"), client_id=os.getenv("HR_AGENT_AUTH0_CLIENT_ID"), client_secret=os.getenv("HR_AGENT_AUTH0_CLIENT_SECRET"))

@app.route('/employees/<employee_id>', methods=['GET'])
@requires_auth
def get_employee(employee_id):
    employee = Auth0(
        domain=os.getenv("HR_AUTH0_DOMAIN"),
        token=get_token.client_credentials(f"https://{os.getenv('HR_AUTH0_DOMAIN')}/api/v2/")["access_token"]
    ).users.get(id=employee_id, fields=["name", "email", "user_id"])

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify(employee), 200

def main():
    host = os.getenv("HR_API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("HR_API_PORT", 8081)))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host=host, port=port, debug=debug, use_reloader=debug)

if __name__ == '__main__':
    main()

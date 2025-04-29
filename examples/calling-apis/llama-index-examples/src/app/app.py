import os
import uuid
from datetime import datetime
from urllib.parse import quote_plus, urlencode

from auth0_ai_llamaindex.auth0_ai import Auth0AI, set_ai_context
from auth0_ai_llamaindex.federated_connections import FederatedConnectionInterrupt
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from llama_index.agent.openai import OpenAIAgent

from ..tools.check_country_holiday import check_country_holiday_tool
from ..tools.check_user_calendar import check_user_calendar_tool

load_dotenv()

agents = {}
system_prompt = f"""You are an assistant designed to answer random user's questions.
**Additional Guidelines**:
- Today’s date for reference: {datetime.now().isoformat()}
"""

auth0_ai = Auth0AI()
with_calender_free_busy_access = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/calendar.freebusy"],
    refresh_token=lambda *_args, **_kwargs: session["user"].get(
        "refresh_token"),
)

tools = [check_country_holiday_tool,
         with_calender_free_busy_access(check_user_calendar_tool)]


def get_agent():
    user_id = session["user"]["userinfo"]["sub"]
    if user_id not in agents:
        agents[user_id] = OpenAIAgent.from_tools(
            tools=tools, model="gpt-4o", system_prompt=system_prompt, verbose=True)
    return agents[user_id]


app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "YOUR_SECRET_KEY")

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile offline_access",
    },
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    
    thread_id = str(uuid.uuid4())
    set_ai_context(thread_id)

    return render_template("index.html", user=session.get('user'))


@app.route("/chat", methods=["POST"])
async def chat():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401

    try:
        message = request.json.get("message")
        response = await get_agent().achat(message)
        return jsonify({"response": str(response)})
    except FederatedConnectionInterrupt as e:
        return jsonify({"error": str(e.to_json())}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("login_callback", _external=True)
    )


@app.route("/login/callback", methods=["GET", "POST"])
def login_callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

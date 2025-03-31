import os
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from langgraph_sdk import get_client
from langchain_core.messages import HumanMessage

load_dotenv()

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

    return render_template("index.html", user=session.get('user'))

@app.route("/chat", methods=["POST"])
async def chat():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401
    
    if "messages" not in session:
        session["messages"] = []
    
    message = request.json.get("message")
    session["messages"].append(message)

    async def run_and_return():
        client = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
        
        if "thread_id" not in session:
            session["thread_id"] = (await client.threads.create())["thread_id"]

        return await client.runs.wait(
            session["thread_id"],
            "agent",
            input={"messages": list(map(HumanMessage, session["messages"]))},
            config={"configurable": {
                "_credentials": {"refresh_token": session["user"]["refresh_token"]}
            }}
        )

    try:
        wait_result = await run_and_return()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if wait_result and "messages" in wait_result:
        last_message = wait_result["messages"][-1]["content"]
        return jsonify({"response": last_message})

    return jsonify({"error": "server_error"}), 500

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

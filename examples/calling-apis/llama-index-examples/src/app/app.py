import os
import uuid

from auth0_ai_llamaindex.auth0_ai import set_ai_context
from auth0_ai_llamaindex.federated_connections import FederatedConnectionInterrupt

# from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from ..agents.agent import get_agent
from ..agents.memory import get_memory
from ..auth0.routes import login_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY")

app.register_blueprint(login_bp)


@app.route("/")
async def home():
    if "user" not in session:
        return redirect(url_for("auth0.login", _external=True))

    session["thread_id"] = str(uuid.uuid4())
    return redirect(url_for("chat", thread_id=session["thread_id"], _external=True))


@app.route("/chat/resume")
async def resume_chat():
    if "user" not in session:
        return "please login", 401

    if "thread_id" not in session:
        return redirect(url_for("home"))

    if "interrupt" in session:
        set_ai_context(session["thread_id"])
        interrupt = session["interrupt"]
        agent = await get_agent(session["user"]["sub"], session["thread_id"])
        await agent.achat(interrupt["last_message"])
        session["interrupt"] = None

    return redirect(url_for("chat", thread_id=session["thread_id"], _external=True))


@app.route("/chat/<thread_id>")
async def chat(thread_id: str):
    if "user" not in session:
        return "please login", 401

    if ("thread_id" not in session) or (session["thread_id"] != thread_id):
        return "Invalid or mismatched chat session. Please start a new chat.", 400

    user_id = session["user"]["sub"]

    memory = await get_memory(user_id, thread_id)

    messages = [
        {
            "role": m.role,
            "content": m.content
        } for m in memory.get_all()
    ]

    return render_template("index.html", user=session["user"], messages=messages, interrupt=None)


@app.route("/api/chat", methods=["POST"])
async def api_chat():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401

    user_id = session["user"]["sub"]
    thread_id = session["thread_id"]
    set_ai_context(thread_id)

    try:
        message = request.json.get("message")
        agent = await get_agent(user_id, thread_id)
        response = await agent.achat(message)
        return jsonify({"response": str(response)})
    except FederatedConnectionInterrupt as e:
        session["interrupt"] = {
            "value": e.to_json(),
            "last_message": message
        }
        return jsonify({"response": e.to_json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

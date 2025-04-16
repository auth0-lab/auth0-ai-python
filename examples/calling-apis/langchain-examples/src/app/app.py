import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from auth0_fastapi.config import Auth0Config
from auth0_fastapi.auth.auth_client import AuthClient
from auth0_fastapi.server.routes import router, register_auth_routes

from langgraph_sdk import get_client
from langchain_core.messages import HumanMessage
from auth0_ai_langchain.utils.interrupt import get_auth0_interrupts


load_dotenv()

app = FastAPI(
    title="Auth0 AI + LangChain - Chatbot Example: Calling API's on user's behalf")

# 1) Add Session Middleware, needed if you're storing data in (or rely on) session cookies
app.add_middleware(SessionMiddleware, secret_key=os.getenv(
    "APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY"))

# 2) Create an Auth0Config with your Auth0 credentials & app settings
config = Auth0Config(
    domain=os.getenv("AUTH0_DOMAIN"),
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    authorization_params={"scope": "openid profile email offline_access"},
    app_base_url=os.getenv("APP_BASE_URL", "http://localhost:3000"),
    secret=os.getenv("APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY"),
)

# 3) Instantiate the AuthClient
auth_client = AuthClient(config)

# Attach to the FastAPI app state so internal routes can access it
app.state.config = config
app.state.auth_client = auth_client

# 4) Conditionally register routes
register_auth_routes(router, config)

# 5) Include the SDK’s default routes
app.include_router(router)

# Set up templates directory
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/")
async def home(request: Request, response: Response):
    # Check if user is authenticated
    user = await auth_client.client.get_user(store_options={"request": request, "response": response})

    if not user:
        return RedirectResponse(url="/auth/login")

    # Render the chat page with the user information
    request.session.pop("thread_id", None)
    request.session.pop("messages", None)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.post("/chat")
async def chat(request: Request, response: Response):
    # Check if user is authenticated
    user = await auth_client.client.get_user(store_options={"request": request, "response": response})

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Retrieve the chat session
    session = request.session

    # Initialize session messages if not present
    if "messages" not in session:
        session["messages"] = []

    # Get the user's message from the request body
    body = await request.json()
    message = body.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    session["messages"].append(message)

    # Initialize LangGraph client
    client = get_client(url=os.getenv(
        "LANGGRAPH_API_URL", "http://localhost:54367"))

    async def run_and_return():
        # Create a thread if it doesn't exist in the session
        if "thread_id" not in session:
            session["thread_id"] = (await client.threads.create())["thread_id"]

        # Wait for the LangGraph agent to process the input
        return await client.runs.wait(
            session["thread_id"],
            "agent",
            input={"messages": list(map(HumanMessage, session["messages"]))},
            config={"configurable": {
                "_credentials": {"refresh_token": user.get("refresh_token")}
            }}
        )

    try:
        wait_result = await run_and_return()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

    # Retrieve thread and handle Auth0 interrupts
    thread = await client.threads.get(session["thread_id"])
    auth0_interrupts = get_auth0_interrupts(thread)

    if auth0_interrupts:
        return JSONResponse(content={"response": auth0_interrupts})

    # Return the last message from the LangGraph agent
    if wait_result and "messages" in wait_result:
        last_message = wait_result["messages"][-1]["content"]
        return JSONResponse(content={"response": last_message})

    return JSONResponse(content={"error": "Unexpected error"}, status_code=500)

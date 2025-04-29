import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware

from auth0_fastapi.server.routes import router, register_auth_routes
from auth0_fastapi.auth.auth_client import StartInteractiveLoginOptions

from langgraph_sdk import get_client
from langgraph_sdk.schema import Command
from langchain_core.messages import HumanMessage
from auth0_ai_langchain.utils.interrupt import get_auth0_interrupts
from src.auth0.auth import config, auth_client


load_dotenv()

app = FastAPI(
    title="Auth0 AI + LangChain - Chatbot Example: Calling API's on user's behalf")

app.add_middleware(SessionMiddleware, secret_key=os.getenv(
    "APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY"))

# Attach to the FastAPI app state so internal routes can access it
app.state.config = config
app.state.auth_client = auth_client

# Conditionally register routes
register_auth_routes(router, config)

# Include the SDK’s default routes
app.include_router(router)

# Set up templates directory with custom Jinja2 environment
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Initialize LangGraph client
langgraph_client = get_client(url=os.getenv(
    "LANGGRAPH_API_URL", "http://localhost:54367"))


@app.get("/")
async def home(request: Request, response: Response):
    # Check if user is authenticated
    try:
        await auth_client.require_session(request, response)
    except Exception:
        return RedirectResponse(url="/auth/login")

    # Reset the chat session and redirect
    chat_session = request.session
    chat_session["thread_id"] = (await langgraph_client.threads.create())["thread_id"]

    # improve with string interpolation
    return RedirectResponse(url="/chat/" + chat_session["thread_id"])


@app.get("/chat/resume")
async def chat_resume(request: Request, response: Response, auth_session=Depends(auth_client.require_session)):
    # Reset the chat session and redirect
    chat_session = request.session

    # Check if there is any thread_id in the session
    # otherwise redirect to home
    if not chat_session.get("thread_id"):
        return RedirectResponse(url="/")

    thread = await langgraph_client.threads.get(chat_session["thread_id"])
    auth0_interrupts = get_auth0_interrupts(thread)

    if auth0_interrupts:
        # Here I must resume tool calls
        await langgraph_client.runs.wait(
            chat_session["thread_id"],
            "agent",
            command=Command(resume=''),
            config={"configurable": {
                "_credentials": {"refresh_token": auth_session.get("refresh_token")}
            }}
        )

    return RedirectResponse(url="/chat/" + chat_session["thread_id"])


@app.get('/chat/{thread_id}')
async def chat_thread(request: Request, thread_id: str, response: Response, auth_session=Depends(auth_client.require_session)):
    chat_session = request.session

    # Check if the thread_id is valid and matches the session
    if ("thread_id" not in chat_session) or (chat_session["thread_id"] != thread_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid or mismatched chat session. Please start a new chat."
        )

    user = auth_session.get("user")

    thread = await langgraph_client.threads.get(chat_session["thread_id"])

    auth0_interrupts = get_auth0_interrupts(thread)
    thread_messages = (thread["values"] if thread["values"]
                       else {}).get("messages", [])

    # Limit the content that is sent to the client
    messages = [
        {
            "type": message["type"],
            "content": message["content"],
            "id": message["id"]
        }
        for message in thread_messages
    ]
    interrupt = auth0_interrupts[0] if auth0_interrupts else None

    # Render the chat page with the user information
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages, "user": user, "interrupt": interrupt})


@app.post("/api/chat")
async def chat_api(request: Request, auth_session=Depends(auth_client.require_session)):
    # Retrieve the chat session
    chat_session = request.session

    # Initialize session messages if not present
    if "thread_id" not in chat_session:
        return JSONResponse(content={"error": "Conversation has expired or doesn't exist. Please start a new chat."}, status_code=400)

    # Get the user's message from the request body
    body = await request.json()
    message = body.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        wait_result = await langgraph_client.runs.wait(
            chat_session["thread_id"],
            "agent",
            input={"messages": [HumanMessage(content=message)]},
            config={"configurable": {
                "_credentials": {"refresh_token": auth_session.get("refresh_token")}
            }}
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

    # Retrieve thread and handle Auth0 interrupts
    thread = await langgraph_client.threads.get(chat_session["thread_id"])
    auth0_interrupts = get_auth0_interrupts(thread)

    if auth0_interrupts:
        return JSONResponse(content={"response": auth0_interrupts[0]})

    # Return the last message from the LangGraph agent
    if wait_result and "messages" in wait_result:
        # reply with the last message
        last_message = wait_result["messages"][-1]
        return JSONResponse(content={"response": last_message["content"]})

    return JSONResponse(content={"error": "Unexpected error"}, status_code=500)


# TODO: Remove this endpoint once `auth0_fastapi` SDK supports
# forwarding the necessary auth_params from `/auth/login` endpoint.
@app.get('/auth/signin')
async def login(request: Request, response: Response):
    protected_keys = [
        "client_id", "redirect_uri", "response_type", "code_challenge", "code_challenge_method", "state", "nonce"
    ]
    return_to: Optional[str] = request.query_params.get("returnTo")
    app_state = {"returnTo": return_to} if return_to else None
    authorization_params = (
        {
            key: value
            for key, value in request.query_params.items()
            if key not in protected_keys
        }
        if not config.pushed_authorization_requests else {}
    )

    auth_url = await auth_client.client.start_interactive_login(
        options=StartInteractiveLoginOptions(
            app_state=app_state,
            authorization_params=authorization_params
        ),
        store_options={"request": request, "response": response}
    )

    return RedirectResponse(url=auth_url, headers=response.headers)

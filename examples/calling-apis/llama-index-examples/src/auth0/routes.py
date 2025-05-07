from flask import Blueprint, request, session, make_response, url_for
from auth0_server_python.auth_types import StartInteractiveLoginOptions, LogoutOptions
from .auth import auth0

login_bp = Blueprint("auth0", __name__)


@login_bp.route("/auth/login")
async def login():
    response = make_response()
    store_options = {"request": request, "response": response}
    options = StartInteractiveLoginOptions(
        app_state={"returnTo": request.args.get("returnTo")},
        authorization_params={k: v for k, v in request.args.items() if k not in [
            "returnTo"]}
    )

    response.headers["Location"] = await auth0.start_interactive_login(options, store_options)
    response.status_code = 302
    return response


@login_bp.route("/auth/callback")
async def login_callback():
    response = make_response()
    store_options = {"request": request, "response": response}
    default_return_to = url_for("home", _external=True)

    result = await auth0.complete_interactive_login(str(request.url), store_options)
    session["user"] = result.get("state_data", {}).get("user")

    response.headers["Location"] = result["app_state"].get(
        "returnTo") or default_return_to
    response.status_code = 302
    return response


@login_bp.route("/auth/logout")
async def logout():
    response = make_response()
    store_options = {"request": request, "response": response}
    options = LogoutOptions(return_to=url_for("home", _external=True))

    response.headers["Location"] = await auth0.logout(options, store_options)
    response.status_code = 302

    session.clear()

    return response

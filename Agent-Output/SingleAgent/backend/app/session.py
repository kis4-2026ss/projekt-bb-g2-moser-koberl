from uuid import uuid4

from fastapi import Request, Response

SESSION_COOKIE = "sneakerhaus_session"


def get_session_token(request: Request, response: Response) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        token = uuid4().hex
        response.set_cookie(
            SESSION_COOKIE,
            token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )
    return token

from typing import Optional
from fastapi import FastAPI

app = FastAPI(
    title="Emilia Hiring Challenge 👩‍💻",
    description="Help Emilia 👩 to fix our tests and get a job interview 💼🎙️!",
)


"""
Task 1 - Warmup
"""


@app.get("/task1/greet/{name}", tags=["Task 1"], summary="👋🇩🇪🇬🇧🇪🇸")
async def task1_greet(name: str, language = None) -> str:
    """Greet somebody in German, English or Spanish!"""
    if language=='en': 
        return f"Hello {name}, I am Emilia."
    elif language=='es':
        return f"Hola {name}, soy Emilia."
    elif language=='ita':
        return f"Hallo {name}, leider spreche ich nicht 'ita'!"

    # Defaults language=='es'
    return f"Hallo {name}, ich bin Emilia."


"""
Task 2 - snake_case to cameCase
"""

from typing import Any


def camelize(key: str):
    """Takes string in snake_case format returns camelCase formatted version."""
    split_key = key.split('_')

    key_part_first = split_key[0]
    key_part_rest = (word.capitalize() for word in split_key[1:])

    return key_part_first+ ''.join(key_part_rest)


@app.post("/task2/camelize", tags=["Task 2"], summary="🐍➡️🐪")
async def task2_camelize(data: dict[str, Any]) -> dict[str, Any]:
    """Takes a JSON object and transfroms all keys from snake_case to camelCase."""
    return {camelize(key): value for key, value in data.items()}


"""
Task 3 - Handle User Actions
"""

from pydantic import BaseModel

friends = {
    "Matthias": ["Sahar", "Franziska", "Hans"],
    "Stefan": ["Felix", "Ben", "Philip"],
}


class ActionRequest(BaseModel):
    username: str
    action: str


class ActionResponse(BaseModel):
    message: str


def handle_call_action(action_request: ActionRequest):
    action = action_request.action.lower()

    for friend in friends[action_request.username]:
        if friend.lower() in action:
            message = f"🤙 Calling {friend} ..."
            break
    else:
        message = f"{action_request.username}, I can't find this person in your contacts."

    return ActionResponse(message=message)


def handle_reminder_action(action_request: ActionRequest):
    message = "🔔 Alright, I will remind you!"
    return ActionResponse(message=message)


def handle_timer_action(action_request: ActionRequest):
    message = "⏰ Alright, the timer is set!"
    return ActionResponse(message=message)


def handle_unknown_action(action_request: ActionRequest):
    message = "👀 Sorry , but I can't help with that!"
    return ActionResponse(message=message)


@app.post("/task3/action", tags=["Task 3"], summary="🤌")
def task3_action(request: ActionRequest):
    """Accepts an action request, recognizes its intent and forwards it to the corresponding action handler."""
    action_handlers = {
        'call': handle_call_action,
        'remind': handle_reminder_action,
        'timer': handle_timer_action,
    }

    # Handle Unknown users' requests
    if request.username not in friends:
        message = f"Hi {request.username}, I don't know you yet. But I would love to meet you!"
        return ActionResponse(message=message)

    # Handle Known requests
    for action in action_handlers:
        if action in request.action.lower():
            handler = action_handlers[action]
            response = handler(request)
            break
    # Handle Unkown requests
    else:
        response = handle_unknown_action(request)

    return response


"""
Task 4 - Security
"""

from datetime import datetime, timedelta
from functools import partial
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# create secret key with: openssl rand -hex 32
SECRET_KEY = "069d49a9c669ddc08f496352166b7b5d270ff64d3009fc297689aa8b0fb66d98"
ALOGRITHM = "HS256"

encode_jwt = partial(jwt.encode, key=SECRET_KEY, algorithm=ALOGRITHM)
decode_jwt = partial(jwt.decode, key=SECRET_KEY, algorithms=[ALOGRITHM])

_crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
verify_password = _crypt_context.verify
hash_password = _crypt_context.hash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/task4/token")

fake_users_db = {
    "stefan": {
        "username": "stefan",
        "email": "stefan.buchkremer@meetap.de",
        "hashed_password": hash_password("decent-espresso-by-john-buckmann"),
        "secret": "I love pressure-profiled espresso ☕!",
    },
    "felix": {
        "username": "felix",
        "email": "felix.andreas@meetap.de",
        "hashed_password": hash_password("elm>javascript"),
        "secret": "Rust 🦀 is the best programming language ever!",
    },
}


class User(BaseModel):
    username: str
    email: str
    hashed_password: str
    secret: str


class Token(BaseModel):
    access_token: str
    token_type: str


@app.post("/task4/token", response_model=Token, summary="🔒", tags=["Task 4"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Allows registered users to obtain a bearer token."""
    # Not really a 'Security Person' but this is fun
    user = get_user(form_data.username)
    if not (user and verify_password(form_data.password, user.hashed_password)):
        raise HTTPException(401, detail='Incorrect username or password')

    payload = {
        "sub": form_data.username,
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return {
        "access_token": encode_jwt(payload),
        "token_type": "bearer",
    }


def get_user(username: str) -> Optional[User]:
    if username not in fake_users_db:
        return
    return User(**fake_users_db[username])


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try : 
        payload = decode_jwt(token)
    except JWTError:
        raise credentials_exception
    
    return get_user(payload['sub'])


@app.get("/task4/users/{username}/secret", summary="🤫", tags=["Task 4"])
async def read_user_secret(
    username: str, current_user: User = Depends(get_current_user)
):
    """Read a user's secret."""
    if current_user.username != username:
        raise HTTPException(403, detail="Don't spy on other user!")

    return current_user.secret


"""
Task and Help Routes
"""

from functools import partial
from pathlib import Path

from tomlkit.api import parse

messages = parse((Path(__file__).parent / "messages.toml").read_text("utf-8"))


@app.get("/", summary="👋", tags=["Emilia"])
async def hello():
    return messages["hello"]


identity = lambda x: x
for i in 1, 2, 3, 4:
    task = messages[f"task{i}"]
    info = partial(identity, task["info"])
    help_ = partial(identity, task["help"])
    tags = [f"Task {i}"]
    app.get(f"/task{i}", summary="📝", description=info(), tags=tags)(info)
    app.get(f"/task{i}/help", summary="🙋", description=help_(), tags=tags)(help_)

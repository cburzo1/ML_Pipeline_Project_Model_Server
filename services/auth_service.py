import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from jwt import PyJWKClient

load_dotenv()

COGNITO_REGION = os.getenv("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_CLI_CLIENT_ID = os.getenv("COGNITO_CLI_CLIENT_ID")

if not COGNITO_REGION:
    raise RuntimeError("COGNITO_REGION environment variable is missing")

if not COGNITO_USER_POOL_ID:
    raise RuntimeError("COGNITO_USER_POOL_ID environment variable is missing")

if not COGNITO_CLIENT_ID:
    raise RuntimeError("COGNITO_CLIENT_ID environment variable is missing")

if not COGNITO_CLI_CLIENT_ID:
    raise RuntimeError("COGNITO_CLI_CLIENT_ID environment variable is missing")

COGNITO_ALLOWED_CLIENT_IDS = {COGNITO_CLIENT_ID}

if COGNITO_CLI_CLIENT_ID:
    COGNITO_ALLOWED_CLIENT_IDS.add(COGNITO_CLI_CLIENT_ID)

COGNITO_ISSUER = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}"
)

JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

jwks_client = PyJWKClient(JWKS_URL)


def verify_token(token: str):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            options={
                "verify_aud": False
            }
        )

        if payload.get("token_use") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        if payload.get("client_id") not in COGNITO_ALLOWED_CLIENT_IDS:
            raise HTTPException(
                status_code=401,
                detail="Invalid token client"
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token missing user ID"
            )

        return user_id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


def get_current_user_id_auth(
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header"
        )

    token = authorization[7:]

    return verify_token(token)
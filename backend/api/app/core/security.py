import json

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import jwt

from app.core.config import settings

from jwt.algorithms import RSAAlgorithm


JWKS_URL = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
_jwks_cache: dict | None = None


async def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache

async def get_signing_key(kid: str):
    jwks = await get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    global _jwks_cache
    _jwks_cache = None
    jwks = await get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
        
    return None

security = HTTPBearer()

async def verify_token(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header["kid"]

    jwk_dict = await get_signing_key(kid)
    if jwk_dict is None:
        raise HTTPException(status_code=401, detail="Invalid token: unknown signing key")
    
    public_key = RSAAlgorithm.from_jwk(json.dumps(jwk_dict))

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.cognito_user_pool_client_id,
            issuer=f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}",
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token")
    
    if payload.get("token_use") != "id":
        raise HTTPException(status_code=401, detail="Invalid token: expected ID token")
    
    tenant_id = payload.get("custom:tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Token missing tenant_id claim")
    
    return {
        "sub": payload["sub"],
        "tenant_id": tenant_id,
    }

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials

    return await verify_token(token)

    
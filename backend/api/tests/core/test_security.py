import json

from fastapi import HTTPException
import jwt
import pytest

import time

from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.core import security
from app.core.config import settings


@pytest.fixture(scope="module")
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def signing_jwk(rsa_keypair):
    _, public_key = rsa_keypair
    jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk["kid"] = "test-kid"
    return jwk

@pytest.fixture
def patch_signing_key(monkeypatch, signing_jwk):
    async def fake_get_signing_key(kid):
        return signing_jwk

    monkeypatch.setattr(security, "get_signing_key", fake_get_signing_key)

def make_token(private_key, **overrides):
    claims = {
        "sub": "test-user-id",
        "custom:tenant_id": "test-tenant-id",
        "token_use" : "id",
        "aud" : settings.cognito_user_pool_client_id,
        "iss" : f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}",
        "exp" : int(time.time()) + 3600,
        "iat" : int(time.time())
    }
    claims.update(overrides)
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-kid"})

    return token

async def test_verify_token_success(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key)
    result = await security.verify_token(token)
    assert result == {"sub": "test-user-id", "tenant_id": "test-tenant-id"}

async def test_verify_token_expired(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key, exp=int(time.time()) - 60)
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401

async def test_verify_token_wrong_audience(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key, aud="wrong-client-id")
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401

async def test_verify_token_wrong_issuer(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key, iss="https://cognito-idp.us-east-1.amazonaws.com/wrong-pool-id")
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401

async def test_verify_token_wrong_token_use(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key, token_use="access")
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401

async def test_verify_token_missing_tenant_id(patch_signing_key, rsa_keypair):
    private_key, _ = rsa_keypair
    token = make_token(private_key)

    token = make_token(private_key, **{"custom:tenant_id": None})
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401

async def test_verify_token_unknown_kid(monkeypatch, rsa_keypair):
    private_key, _ = rsa_keypair

    async def fake_get_signing_key(kid):
        return None

    monkeypatch.setattr(security, "get_signing_key", fake_get_signing_key)
    token = make_token(private_key)
    with pytest.raises(HTTPException) as exc_info:
        await security.verify_token(token)
    assert exc_info.value.status_code == 401
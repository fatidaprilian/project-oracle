from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials


SECRET_KEY = os.getenv("ORACLE_SECRET_KEY",
                       "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = int(os.getenv("ORACLE_TOKEN_EXPIRY_HOURS", "24"))
DEFAULT_PBKDF2_ITERATIONS = int(os.getenv("ORACLE_AUTH_HASH_ITERATIONS", "390000"))

Role = Literal["viewer", "operator", "admin"]


def normalize_role(value: str) -> Role:
    lowered = value.strip().lower()
    if lowered in ("viewer", "operator", "admin"):
        return lowered  # type: ignore[return-value]
    return "viewer"


def get_auth_dsn() -> str:
    return (
        os.getenv("ORACLE_AUTH_POSTGRES_DSN", "").strip()
        or os.getenv("ORACLE_POSTGRES_DSN", "").strip()
    )


def _get_psycopg_module():
    try:
        import psycopg  # type: ignore

        return psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg package is required for database auth") from exc


def hash_password(password: str, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    if iterations < 100_000:
        raise ValueError("PBKDF2 iterations must be at least 100000")

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def verify_password_hash(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_b64, digest_b64 = password_hash.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_raw)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except Exception:
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed, expected)


def ensure_auth_schema(dsn: str | None = None) -> None:
    target_dsn = (dsn or get_auth_dsn()).strip()
    if not target_dsn:
        raise RuntimeError(
            "Auth database DSN is not configured. Set ORACLE_AUTH_POSTGRES_DSN or ORACLE_POSTGRES_DSN."
        )

    psycopg = _get_psycopg_module()
    with psycopg.connect(target_dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('viewer', 'operator', 'admin')),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        connection.commit()


def create_or_update_user(
    username: str,
    password: str,
    role: str,
    dsn: str | None = None,
) -> None:
    normalized_username = username.strip()
    normalized_role = normalize_role(role)
    if not normalized_username:
        raise ValueError("Username must not be empty")

    target_dsn = (dsn or get_auth_dsn()).strip()
    if not target_dsn:
        raise RuntimeError(
            "Auth database DSN is not configured. Set ORACLE_AUTH_POSTGRES_DSN or ORACLE_POSTGRES_DSN."
        )

    ensure_auth_schema(target_dsn)
    hashed = hash_password(password)
    psycopg = _get_psycopg_module()

    with psycopg.connect(target_dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auth_users (username, password_hash, role, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (username) DO UPDATE
                SET
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    is_active = TRUE,
                    updated_at = NOW()
                """,
                (normalized_username, hashed, normalized_role),
            )
        connection.commit()


def authenticate_db_user(
    username: str,
    password: str,
    dsn: str | None = None,
) -> dict[str, str] | None:
    normalized_username = username.strip()
    if not normalized_username or not password:
        return None

    target_dsn = (dsn or get_auth_dsn()).strip()
    if not target_dsn:
        raise RuntimeError(
            "Auth database DSN is not configured. Set ORACLE_AUTH_POSTGRES_DSN or ORACLE_POSTGRES_DSN."
        )

    ensure_auth_schema(target_dsn)
    psycopg = _get_psycopg_module()

    with psycopg.connect(target_dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, password_hash, role, is_active
                FROM auth_users
                WHERE username = %s
                """,
                (normalized_username,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    db_username, db_password_hash, db_role, is_active = row
    if not bool(is_active):
        return None
    if not verify_password_hash(password, str(db_password_hash)):
        return None

    return {
        "username": str(db_username),
        "role": normalize_role(str(db_role)),
    }


def create_api_token(identifier: str = "default", role: str = "viewer") -> str:
    payload = {
        "sub": identifier,
        "role": normalize_role(role),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_api_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials) -> dict:
    token = credentials.credentials
    return verify_api_token(token)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_signature(
    payload: str,
    signature: str,
    secret: str,
) -> bool:
    expected_sig = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected_sig)

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from slowapi import Limiter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (create_access_token, create_refresh_token,
                               decode_token, hash_password, verify_password)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (LoginRequest, RefreshRequest, RegisterRequest,
                              SupabaseExchangeRequest, TokenResponse)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


def rate_limit_key(request: Request) -> str:
    """Generate rate limit key from request, preferring client IP with port."""
    if hasattr(request.state, "rate_limit_key") and request.state.rate_limit_key:
        return request.state.rate_limit_key
    # Check for X-Forwarded-For header when behind reverse proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP from the chain (original client)
        return forwarded_for.split(",")[0].strip()
    # Use client IP:port for better granularity
    if request.client:
        return f"{request.client.host}:{request.client.port}"
    return "unknown"


limiter = Limiter(key_func=rate_limit_key)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.register_rate_limit)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password), role="user")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    access = create_access_token(str(user.id), user.role)
    refresh, jti, expires_at = create_refresh_token(str(user.id), user.role)
    db.add(RefreshToken(user_id=user.id, token_jti=jti, expires_at=expires_at))
    await db.commit()
    await log_audit_event(
        db,
        action="user_registered",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.login_rate_limit)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token(str(user.id), user.role)
    refresh, jti, expires_at = create_refresh_token(str(user.id), user.role)
    db.add(RefreshToken(user_id=user.id, token_jti=jti, expires_at=expires_at))
    await db.commit()
    await log_audit_event(
        db,
        action="user_login",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        metadata_json={"email": user.email},
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.refresh_rate_limit)
async def refresh_token(payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token)
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if claims.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = claims.get("sub")
    token_jti = claims.get("jti")
    if not user_id or not token_jti:
        raise HTTPException(status_code=401, detail="Malformed refresh token")

    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token_jti == token_jti, RefreshToken.user_id == int(user_id))
    )
    stored = result.scalar_one_or_none()
    if not stored or stored.is_revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    stored.is_revoked = True
    access = create_access_token(str(user.id), user.role)
    refresh, new_jti, expires_at = create_refresh_token(str(user.id), user.role)
    db.add(RefreshToken(user_id=user.id, token_jti=new_jti, expires_at=expires_at))
    await db.commit()

    await log_audit_event(
        db,
        action="token_refreshed",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


def _supabase_auth_config() -> tuple[str, str]:
    url = settings.supabase_url or settings.vite_supabase_url
    key = settings.supabase_publishable_key or settings.vite_supabase_publishable_key
    if not url or not key:
        raise HTTPException(status_code=503, detail="Supabase auth bridge is not configured")
    return url.rstrip("/"), key


async def _fetch_supabase_user(access_token: str) -> dict:
    import httpx

    supabase_url, publishable_key = _supabase_auth_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": publishable_key,
                "Authorization": f"Bearer {access_token}",
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase session")
    data = response.json()
    if not data.get("id") or not data.get("email"):
        raise HTTPException(status_code=401, detail="Supabase session is missing user identity")
    return data


@router.post("/supabase/exchange", response_model=TokenResponse)
@limiter.limit(settings.login_rate_limit)
async def exchange_supabase_session(
    payload: SupabaseExchangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a verified Supabase session for the backend's JWT pair."""

    supabase_user = await _fetch_supabase_user(payload.access_token)
    email = supabase_user["email"]
    metadata = supabase_user.get("user_metadata") or {}
    role = "admin" if metadata.get("role") == "admin" else "user"

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        if user.role != role and role == "admin":
            user.role = role
    else:
        user = User(
            email=email,
            password_hash=hash_password(f"supabase:{supabase_user['id']}"),
            role=role,
        )
        db.add(user)
        await db.flush()

    access = create_access_token(str(user.id), user.role)
    refresh, jti, expires_at = create_refresh_token(str(user.id), user.role)
    db.add(RefreshToken(user_id=user.id, token_jti=jti, expires_at=expires_at))
    await db.commit()
    await log_audit_event(
        db,
        action="supabase_session_exchanged",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        metadata_json={"email": user.email},
    )
    return TokenResponse(access_token=access, refresh_token=refresh)

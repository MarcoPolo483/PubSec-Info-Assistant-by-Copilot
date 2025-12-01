"""JWT/OAuth authentication module for enterprise-grade security."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # subject (user ID)
    tenant_id: str
    roles: list[str] = []
    exp: int  # expiration timestamp
    iat: int  # issued at
    token_type: str = "access"


class TokenResponse(BaseModel):
    """OAuth2 token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    subject: str,
    tenant_id: str,
    roles: list[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": subject,
        "tenant_id": tenant_id,
        "roles": roles or [],
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "token_type": "access"
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str, tenant_id: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "token_type": "refresh"
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        
        # Validate token type
        if payload.get("token_type") != token_type:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(**payload)
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Dict[str, Any]:
    """
    Extract and validate user from JWT token or fallback to API key.
    
    Supports dual authentication:
    1. Bearer token (JWT) - preferred for production
    2. X-API-Key header - legacy support during migration
    """
    # JWT authentication (preferred)
    if credentials:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        
        return {
            "user_id": payload.sub,
            "tenant_id": payload.tenant_id,
            "roles": payload.roles,
            "auth_method": "jwt"
        }
    
    # Fallback to API key authentication
    if x_api_key:
        # Simple API key validation (enhance with database lookup in production)
        if not x_api_key.strip():
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # For API key auth, extract tenant from header
        return {
            "user_id": "api_key_user",
            "tenant_id": None,  # Will be extracted from X-Tenant-ID header
            "roles": ["api_user"],
            "auth_method": "api_key"
        }
    
    # No authentication provided (allow for public endpoints if configured)
    if settings.allow_anonymous:
        return {
            "user_id": "anonymous",
            "tenant_id": settings.default_tenant_id,
            "roles": ["anonymous"],
            "auth_method": "anonymous"
        }
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_roles: list[str]):
    """Dependency to enforce role-based access control."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # Admin role bypasses all checks
        if "admin" in user_roles:
            return current_user
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


# Authentication endpoints to be added to main.py
class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
    tenant_id: Optional[str] = None


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and issue tokens.
    
    In production, validate against user database.
    For demo purposes, accepts any username/password.
    """
    # TODO: Replace with actual user validation from database
    # For now, accept any credentials for testing
    if not request.username or not request.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Mock user validation (replace with database lookup)
    user_id = request.username
    tenant_id = request.tenant_id or settings.default_tenant_id
    roles = ["user", "reader"]  # Default roles
    
    # Generate tokens
    access_token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        roles=roles
    )
    
    refresh_token = create_refresh_token(
        subject=user_id,
        tenant_id=tenant_id
    )
    
    logger.info(f"User {user_id} authenticated successfully for tenant {tenant_id}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


async def refresh_access_token(request: RefreshRequest) -> TokenResponse:
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    # Issue new tokens
    access_token = create_access_token(
        subject=payload.sub,
        tenant_id=payload.tenant_id,
        roles=[]  # Roles should be fetched from database
    )
    
    # Optionally rotate refresh token
    refresh_token = create_refresh_token(
        subject=payload.sub,
        tenant_id=payload.tenant_id
    )
    
    logger.info(f"Access token refreshed for user {payload.sub}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

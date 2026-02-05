from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import models
from database import get_db
import logging

logger = logging.getLogger(__name__)

# Secret key - in production, use environment variable
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    # Ensure 'sub' (subject) is a string per JWT spec to avoid decode errors
    if "sub" in to_encode and to_encode["sub"] is not None:
        try:
            to_encode["sub"] = str(to_encode["sub"])
        except Exception:
            # fallback: remove invalid subject to avoid token creation failure
            to_encode.pop("sub", None)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return token data"""
    token = credentials.credentials
    logger.info(f"Verifying token: {token[:50]}...")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token decoded successfully. Payload: {payload}")
        sub_claim = payload.get("sub")
        if sub_claim is None:
            logger.error("Token missing 'sub' (user_id) claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert subject to integer user_id when possible
        try:
            user_id = int(sub_claim)
        except Exception:
            logger.error(f"Invalid 'sub' claim type: {type(sub_claim)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Token verified for user_id: {user_id}")
        return {"user_id": user_id, "role": payload.get("role")}
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    """Get current authenticated user"""
    token_data = verify_token(credentials)
    user_id = token_data.get("user_id")
    logger.info(f"Looking up user with ID: {user_id}")

    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            logger.error(f"User with ID {user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        logger.info(f"User found: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error looking up user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User lookup failed",
        )


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Check if user has admin role"""
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib  # ADD THIS
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Token, UserCreate
from database import db
from config import settings

# REMOVE: pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Simple SHA256 hash (for demo only)
    test_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return test_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Simple SHA256 hash (for demo only)
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def authenticate_user(email: str, password: str):
    """Authenticate a user"""
    user = await db.get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user['hashed_password']):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def register_new_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user object
    user_dict = user_data.dict()
    user_dict['hashed_password'] = get_password_hash(user_data.password)
    del user_dict['password']
    
    # Save user to database
    user_id = await db.create_user(user_dict)
    
    # Create token
    access_token = create_access_token(data={"sub": user_id})
    
    return Token(access_token=access_token, token_type="bearer")
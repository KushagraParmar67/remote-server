from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# Request Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    age: Optional[int] = None
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    profile_photo: Optional[str] = None  # Base64 encoded image

class ServerCreate(BaseModel):
    name: str
    host: str
    username: str
    port: int = 22
    use_password: bool = False
    password: Optional[str] = None
    ssh_key: Optional[str] = None  # PEM content or path

class CommandRequest(BaseModel):
    command: str
    server_id: str

# Response Models
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    age: Optional[int]
    phone: Optional[str]
    profile_photo: Optional[str] = None
    role: UserRole
    created_at: datetime

class ServerResponse(BaseModel):
    id: str
    name: str
    host: str
    username: str
    port: int
    created_at: datetime
    updated_at: datetime

class CommandResponse(BaseModel):
    output: str
    error: str
    exit_code: int
    execution_time: float

class LogResponse(BaseModel):
    id: str
    user_id: str
    server_id: str
    command: str
    output: str
    exit_code: int
    timestamp: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from typing import List


from models import *
from auth import *
from database import db
from ssh_manager import ssh_manager
from email_service import email_service
from security import validator

# Lifespan manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Remote Server Manager API")
    yield
    # Shutdown
    print("Shutting down Remote Server Manager API")

async def create_initial_admin():
    """Create an initial admin user for testing"""
    admin_email = "admin@example.com"
    existing = await db.get_user_by_email(admin_email)
    if not existing:
        from auth import get_password_hash
        admin_user = {
            "email": admin_email,
            "hashed_password": get_password_hash("admin123"),
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin"
        }
        await db.create_user(admin_user)
        print("Created initial admin user: admin@example.com / admin123")

# Create FastAPI app
app = FastAPI(
    title="Remote Server Manager API",
    description="API for managing remote Linux servers via SSH",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate):
    """Register a new user"""
    return await register_new_user(user)

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: dict):
    """Login user and get access token"""
    email = form_data.get("email")
    password = form_data.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user['id']})
    return {"access_token": access_token, "token_type": "bearer"}

# ========== PROFILE ENDPOINTS ==========

@app.get("/api/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@app.put("/api/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    update_data = user_update.dict(exclude_unset=True)
    success = await db.update_user(current_user['id'], update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get updated user
    updated_user = await db.get_user_by_id(current_user['id'])
    return updated_user

@app.delete("/api/profile")
async def delete_profile(current_user: dict = Depends(get_current_user)):
    """Delete user profile"""
    success = await db.delete_user(current_user['id'])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}

# ========== SERVER MANAGEMENT ENDPOINTS ==========

@app.post("/api/servers", response_model=dict)
async def create_server(
    server: ServerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new server"""
    # Test connection before saving
    if server.use_password and not server.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password required for password authentication"
        )
    
    # Test SSH connection
    test_success = ssh_manager.test_connection(
        host=server.host,
        username=server.username,
        port=server.port,
        password=server.password if server.use_password else None,
        ssh_key=server.ssh_key if not server.use_password else None
    )
    
    if not test_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to server. Check credentials."
        )
    
    # Save server
    server_data = server.dict()
    server_id = await db.create_server(current_user['id'], server_data)
    
    # Send email notification (in background)
    asyncio.create_task(
        email_service.send_server_notification(
            current_user['email'],
            server.name,
            "added"
        )
    )
    
    return {
        "message": "Server added successfully",
        "server_id": server_id,
        "test_connection": "successful"
    }

@app.get("/api/servers", response_model=List[ServerResponse])
async def get_servers(current_user: dict = Depends(get_current_user)):
    """Get all servers for current user"""
    servers = await db.get_user_servers(current_user['id'])
    return servers

@app.get("/api/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific server"""
    server = await db.get_server(server_id, current_user['id'])
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    return server

@app.put("/api/servers/{server_id}")
async def update_server(
    server_id: str,
    server_update: ServerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update server information"""
    server = await db.get_server(server_id, current_user['id'])
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Test new connection
    test_success = ssh_manager.test_connection(
        host=server_update.host,
        username=server_update.username,
        port=server_update.port,
        password=server_update.password if server_update.use_password else None,
        ssh_key=server_update.ssh_key if not server_update.use_password else None
    )
    
    if not test_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect with new credentials"
        )
    
    # Update server
    update_data = server_update.dict()
    success = await db.update_server(server_id, current_user['id'], update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update server"
        )
    
    return {"message": "Server updated successfully"}

@app.delete("/api/servers/{server_id}")
async def delete_server(
    server_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a server"""
    server = await db.get_server(server_id, current_user['id'])
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    success = await db.delete_server(server_id, current_user['id'])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete server"
        )
    
    # Send email notification
    asyncio.create_task(
        email_service.send_server_notification(
            current_user['email'],
            server['name'],
            "deleted"
        )
    )
    
    return {"message": "Server deleted successfully"}

# ========== COMMAND EXECUTION ENDPOINTS ==========

@app.post("/api/servers/{server_id}/execute")
async def execute_command(
    server_id: str,
    command_request: CommandRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Execute a command on a remote server"""
    # Get server details
    server = await db.get_server(server_id, current_user['id'])
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Sanitize command
    command = validator.sanitize_command(command_request.command)
    
    # Execute command
    try:
        output, error, exit_code, exec_time = await ssh_manager.execute_command(
            host=server['host'],
            username=server['username'],
            port=server['port'],
            password=server.get('password') if server.get('use_password') else None,
            ssh_key=server.get('ssh_key') if not server.get('use_password') else None,
            command=command
        )
        
        # Create log entry
        log_data = {
            "user_id": current_user['id'],
            "server_id": server_id,
            "server_name": server['name'],
            "command": command,
            "output": output,
            "error": error,
            "exit_code": exit_code,
            "execution_time": exec_time
        }
        
        await db.create_log(log_data)
        
        # Send email notification for failed commands
        if exit_code != 0:
            asyncio.create_task(
                email_service.send_command_notification(
                    current_user['email'],
                    server['name'],
                    command,
                    success=False,
                    output=f"Error: {error}\nExit Code: {exit_code}"
                )
            )
        
        return {
            "output": output,
            "error": error,
            "exit_code": exit_code,
            "execution_time": exec_time,
            "server": server['name'],
            "command": command
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {str(e)}"
        )

@app.get("/api/logs")
async def get_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get command execution logs for current user"""
    logs = await db.get_user_logs(current_user['id'], limit)
    return logs

# ========== HEALTH CHECK ==========

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Remote Server Manager API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Remote Server Manager API"
    }

# ========== RUN APPLICATION ==========

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
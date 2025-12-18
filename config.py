import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # SSH Settings
    SSH_TIMEOUT = 30
    ALLOWED_COMMANDS = [
        "ls", "pwd", "whoami", "date", "uptime", "free", "df", "ps",
        "cat", "grep", "tail", "head", "wc", "find", "du", "uname"
    ]
    BLOCKED_COMMANDS = [
        "rm -rf", "rm -fr", "rm -r", "dd", "mkfs", "shutdown",
        "reboot", "halt", "poweroff", "init", "kill", "chmod 777"
    ]
    
    # Email Settings
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    
    # File paths
    DATA_DIR = "data"
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    SERVERS_FILE = os.path.join(DATA_DIR, "servers.json")
    LOGS_FILE = os.path.join(DATA_DIR, "logs.json")
    
    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

settings = Settings()
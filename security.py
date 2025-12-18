import re
from config import settings

class CommandValidator:
    @staticmethod
    def is_command_allowed(command: str) -> bool:
        """Check if command is allowed"""
        command_lower = command.lower().strip()
        
        # Check for blocked commands
        for blocked in settings.BLOCKED_COMMANDS:
            if blocked in command_lower:
                return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r"rm\s+.*-.*[rf]",  # rm with -r or -f flags
            r":\(\)\{.*;\s*:",  # Fork bomb
            r"chmod\s+[0-7]{3,4}\s+.*",  # chmod with 3-4 digit mode
            r">\s*/dev/sd[a-z]",  # Writing to disk devices
            r"dd\s+.*if=.*of=",  # dd command
            r"mkfs\s+",  # Format commands
            r">\s*/proc/",  # Writing to /proc
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False
        
        # Allow only basic commands for demo
        # In production, implement a whitelist system
        allowed_prefixes = [
            "ls", "pwd", "whoami", "date", "uptime", 
            "free", "df", "ps", "cat ", "grep ", "tail ",
            "head ", "wc ", "find ", "du ", "uname", "echo ",
            "cd ", "mkdir ", "touch ", "cp ", "mv "
        ]
        
        for prefix in allowed_prefixes:
            if command_lower.startswith(prefix):
                return True
        
        return False
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize command input"""
        # Remove multiple spaces
        command = re.sub(r'\s+', ' ', command.strip())
        # Remove dangerous characters
        command = re.sub(r'[;&|`$<>]', '', command)
        return command

# Create validator instance
validator = CommandValidator()
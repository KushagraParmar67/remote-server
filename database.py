import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import settings
import aiofiles
import asyncio

class JSONDatabase:
    def __init__(self):
        self.users_file = settings.USERS_FILE
        self.servers_file = settings.SERVERS_FILE
        self.logs_file = settings.LOGS_FILE
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        for file_path in [self.users_file, self.servers_file, self.logs_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _read_file(self, file_path: str) -> List[Dict]:
        """Read JSON file asynchronously"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    async def _write_file(self, file_path: str, data: List[Dict]):
        """Write to JSON file asynchronously"""
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    # User Operations
    async def create_user(self, user_data: Dict) -> str:
        """Create a new user"""
        user_data['id'] = str(uuid.uuid4())
        user_data['created_at'] = datetime.now().isoformat()
        user_data['role'] = 'user'
        
        users = await self._read_file(self.users_file)
        users.append(user_data)
        await self._write_file(self.users_file, users)
        
        return user_data['id']
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users = await self._read_file(self.users_file)
        for user in users:
            if user['email'] == email:
                return user
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = await self._read_file(self.users_file)
        for user in users:
            if user['id'] == user_id:
                return user
        return None
    
    async def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user information"""
        users = await self._read_file(self.users_file)
        for i, user in enumerate(users):
            if user['id'] == user_id:
                users[i].update(update_data)
                users[i]['updated_at'] = datetime.now().isoformat()
                await self._write_file(self.users_file, users)
                return True
        return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        users = await self._read_file(self.users_file)
        new_users = [u for u in users if u['id'] != user_id]
        
        if len(new_users) != len(users):
            await self._write_file(self.users_file, new_users)
            return True
        return False
    
    # Server Operations
    async def create_server(self, user_id: str, server_data: Dict) -> str:
        """Create a new server for user"""
        server_data['id'] = str(uuid.uuid4())
        server_data['user_id'] = user_id
        server_data['created_at'] = datetime.now().isoformat()
        server_data['updated_at'] = datetime.now().isoformat()
        
        # Encrypt sensitive data (simple base64 for demo, use proper encryption in production)
        if server_data.get('password'):
            import base64
            server_data['password'] = base64.b64encode(server_data['password'].encode()).decode()
        
        servers = await self._read_file(self.servers_file)
        servers.append(server_data)
        await self._write_file(self.servers_file, servers)
        
        return server_data['id']
    
    async def get_user_servers(self, user_id: str) -> List[Dict]:
        """Get all servers for a user"""
        servers = await self._read_file(self.servers_file)
        user_servers = [s for s in servers if s['user_id'] == user_id]
        
        # Decrypt passwords
        for server in user_servers:
            if server.get('password'):
                import base64
                server['password'] = base64.b64decode(server['password'].encode()).decode()
        
        return user_servers
    
    async def get_server(self, server_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific server"""
        servers = await self._read_file(self.servers_file)
        for server in servers:
            if server['id'] == server_id and server['user_id'] == user_id:
                if server.get('password'):
                    import base64
                    server['password'] = base64.b64decode(server['password'].encode()).decode()
                return server
        return None
    
    async def update_server(self, server_id: str, user_id: str, update_data: Dict) -> bool:
        """Update server information"""
        servers = await self._read_file(self.servers_file)
        for i, server in enumerate(servers):
            if server['id'] == server_id and server['user_id'] == user_id:
                # Encrypt password if updating
                if update_data.get('password'):
                    import base64
                    update_data['password'] = base64.b64encode(update_data['password'].encode()).decode()
                
                servers[i].update(update_data)
                servers[i]['updated_at'] = datetime.now().isoformat()
                await self._write_file(self.servers_file, servers)
                return True
        return False
    
    async def delete_server(self, server_id: str, user_id: str) -> bool:
        """Delete a server"""
        servers = await self._read_file(self.servers_file)
        new_servers = [s for s in servers if not (s['id'] == server_id and s['user_id'] == user_id)]
        
        if len(new_servers) != len(servers):
            await self._write_file(self.servers_file, new_servers)
            return True
        return False
    
    # Log Operations
    async def create_log(self, log_data: Dict) -> str:
        """Create a command execution log"""
        log_data['id'] = str(uuid.uuid4())
        log_data['timestamp'] = datetime.now().isoformat()
        
        logs = await self._read_file(self.logs_file)
        logs.append(log_data)
        await self._write_file(self.logs_file, logs)
        
        return log_data['id']
    
    async def get_user_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get logs for a user"""
        logs = await self._read_file(self.logs_file)
        user_logs = [log for log in logs if log['user_id'] == user_id]
        return sorted(user_logs, key=lambda x: x['timestamp'], reverse=True)[:limit]

# Create a global database instance
db = JSONDatabase()
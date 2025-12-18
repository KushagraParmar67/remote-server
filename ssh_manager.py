import paramiko
import asyncio
import time
from io import StringIO
from typing import Tuple
from config import settings
from security import validator

class SSHManager:
    @staticmethod
    async def execute_command(
        host: str,
        username: str,
        port: int = 22,
        password: str = None,
        ssh_key: str = None,
        command: str = ""
    ) -> Tuple[str, str, int, float]:
        """
        Execute a command on remote server via SSH
        
        Returns: (output, error, exit_code, execution_time)
        """
        start_time = time.time()
        client = None
        
        try:
            # Validate command
            if not validator.is_command_allowed(command):
                raise ValueError(f"Command not allowed: {command}")
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to server
            if ssh_key:
                # Use SSH key
                key_file = StringIO(ssh_key)
                private_key = paramiko.RSAKey.from_private_key(key_file)
                client.connect(
                    hostname=host,
                    username=username,
                    pkey=private_key,
                    port=port,
                    timeout=settings.SSH_TIMEOUT
                )
            elif password:
                # Use password
                client.connect(
                    hostname=host,
                    username=username,
                    password=password,
                    port=port,
                    timeout=settings.SSH_TIMEOUT
                )
            else:
                raise ValueError("Either password or SSH key must be provided")
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=30)
            
            # Get output
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            # Get exit code
            exit_code = stdout.channel.recv_exit_status()
            
            execution_time = time.time() - start_time
            
            return output, error, exit_code, execution_time
            
        except paramiko.AuthenticationException:
            raise Exception("Authentication failed. Check credentials.")
        except paramiko.SSHException as e:
            raise Exception(f"SSH connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error executing command: {str(e)}")
        finally:
            if client:
                client.close()

    @staticmethod
    def test_connection(
        host: str,
        username: str,
        port: int = 22,
        password: str = None,
        ssh_key: str = None
    ) -> bool:
        """Test SSH connection to server"""
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if ssh_key:
                key_file = StringIO(ssh_key)
                private_key = paramiko.RSAKey.from_private_key(key_file)
                client.connect(
                    hostname=host,
                    username=username,
                    pkey=private_key,
                    port=port,
                    timeout=10
                )
            elif password:
                client.connect(
                    hostname=host,
                    username=username,
                    password=password,
                    port=port,
                    timeout=10
                )
            else:
                return False
            
            # Execute a simple test command
            stdin, stdout, stderr = client.exec_command("echo 'Connection successful'")
            output = stdout.read().decode().strip()
            return "Connection successful" in output
            
        except Exception:
            return False
        finally:
            if client:
                client.close()

# Create SSH manager instance
ssh_manager = SSHManager()
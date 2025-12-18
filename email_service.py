import asyncio
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

class EmailService:
    def __init__(self):
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USER
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM or settings.EMAIL_USER
    
    async def send_email(self, to_email: str, subject: str, body: str, html_body: str = None):
        """Send an email"""
        if not all([self.host, self.port, self.username, self.password]):
            print("Email configuration missing. Skipping email send.")
            return False
        
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.from_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add plain text version
            message.attach(MIMEText(body, 'plain'))
            
            # Add HTML version if provided
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Send email
            async with SMTP(hostname=self.host, port=self.port, start_tls=True) as smtp:
                await smtp.login(self.username, self.password)
                await smtp.send_message(message)
            
            print(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    async def send_command_notification(self, user_email: str, server_name: str, command: str, 
                                      success: bool, output: str = ""):
        """Send notification about command execution"""
        status = "SUCCESS" if success else "FAILED"
        subject = f"SSH Command {status} on {server_name}"
        
        body = f"""
        Command Execution Report
        
        Server: {server_name}
        Command: {command}
        Status: {status}
        
        Output:
        {output[:500]}  # Limit output length
        
        ---
        Remote Server Manager
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Command Execution Report</h2>
            <p><strong>Server:</strong> {server_name}</p>
            <p><strong>Command:</strong> <code>{command}</code></p>
            <p><strong>Status:</strong> <span style="color: {'green' if success else 'red'}">{status}</span></p>
            <h3>Output:</h3>
            <pre>{output[:500]}</pre>
            <hr>
            <p>Remote Server Manager</p>
        </body>
        </html>
        """
        
        await self.send_email(user_email, subject, body, html_body)
    
    async def send_server_notification(self, user_email: str, server_name: str, action: str):
        """Send notification about server changes"""
        subject = f"Server {action}: {server_name}"
        
        body = f"""
        Server Management Notification
        
        Server: {server_name}
        Action: {action}
        
        The server has been {action.lower()} successfully.
        
        ---
        Remote Server Manager
        """
        
        await self.send_email(user_email, subject, body)

# Create email service instance
email_service = EmailService()
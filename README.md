# Remote Server Manager API

A backend REST API for managing remote Linux servers via SSH with user authentication, command execution, and email notifications.

## Features
- User authentication (JWT-based)
- Profile management
- Remote server CRUD operations
- SSH command execution with security restrictions
- Email notifications
- JSON-based database (no external DB required)

## Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd remote-server-manager

Create virtual environment

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install -r requirements.txt
Configure environment variables

bash
cp .env.example .env
# Edit .env with your values
Run the application

bash
python app.py
The API will be available at http://localhost:8000

API Documentation
Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Default Admin User
Email: admin@example.com

Password: admin123

Testing with EC2 Instance
Add your EC2 server:

bash
POST /api/servers
{
  "name": "My EC2 Server",
  "host": "your-ec2-public-ip",
  "username": "ubuntu",
  "port": 22,
  "use_password": false,
  "ssh_key": "-----BEGIN RSA PRIVATE KEY-----\n..."
}
Execute a command:

bash
POST /api/servers/{server_id}/execute
{
  "command": "ls -la"
}
Security Notes
SSH keys and passwords are encrypted in storage

Command validation prevents dangerous operations

JWT tokens expire in 30 minutes

Always use HTTPS in production

Deployment to Render
Push code to GitHub

Create new Web Service on Render

Set environment variables

Deploy!

Project Structure
text
├── app.py              # Main application
├── auth.py             # Authentication
├── database.py         # JSON database
├── ssh_manager.py      # SSH operations
├── email_service.py    # Email notifications
├── security.py         # Security validation
├── models.py           # Data models
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── data/              # JSON data storage
└── README.md
License
MIT

text

## **How to Run Locally:**

1. **Create the project structure:**
```bash
mkdir remote-server-manager
cd remote-server-manager
Create all the files (copy each file content above into respective files)

Install dependencies:

bash
pip install -r requirements.txt
Set up environment:

bash
cp .env.example .env
# Edit .env with your email settings (optional for testing)
Run the application:

bash
python app.py
Access the API:

Open browser to: http://localhost:8000/docs

Use the interactive Swagger UI to test endpoints

Testing Flow:
Register a new user or use default admin:

Email: admin@example.com

Password: admin123

Login to get JWT token

Add your EC2 server (use "Authorize" button in Swagger to set token)

Execute commands on your EC2 instance
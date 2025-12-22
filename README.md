# SQL Chat - Talk to Your Database

A simple, stateless web application that lets you query databases using natural language or direct SQL. No signup, no login - just add your API key and database credentials to get started.

## Features

- 🔓 **Completely Stateless** - No signup or login required
- 🔑 **Bring Your Own Keys** - Use your own Gemini or OpenAI API key
- 💾 **LocalStorage Persistence** - Credentials saved in your browser
- 💬 **Chat History Saved** - All conversations persist across sessions
- 🤖 **AI Mode** - Ask questions in natural language
- ⚡ **Direct SQL Mode** - Execute your own SELECT queries
- 🔒 **Read-Only** - Only SELECT queries allowed for safety
- 🗄️ **Multi-Database** - Supports PostgreSQL and MySQL

## Quick Start

1. **Install dependencies (local Python)**

```bash
pip install -r requirements.txt
```

2. **Run the application locally**

```bash
uvicorn app:app --reload
```

- Open http://localhost:8000 in your browser  
- Health check: http://localhost:8000/health

3. **Run with Docker**

```bash
# Build the Docker image
docker build -t sql-chat .

# Run the Docker container
docker run -d -p 8000:8000 --name sql-chat-web sql-chat
```

- Access the app at http://localhost:8000

4. **Optional: Using Docker Compose**

```bash
docker-compose up --build
```

- This will build and start the container automatically  
- Access the app at http://localhost:8000

5. **Notes**

- Use `host.docker.internal` as DB host if connecting to a database on your local machine from Docker  
- API keys and DB credentials are provided **dynamically via the UI**, no hardcoding needed  
- The app works with any database accessible from your network, as long as credentials are correct


3. Open http://localhost:8000 in your browser

4. Click "Get Started" on the landing page

5. Click "Settings" and configure:
   - Your AI provider (Gemini or OpenAI)
   - Your API key
   - Your database credentials

6. Start chatting with your database!

## Usage Modes

### AI Query Mode
Ask questions in natural language:
- "Show me all users from California"
- "What are the top 10 products by revenue?"
- "List orders from last week"

### Direct SQL Mode
Write and execute your own SQL:
```sql
SELECT * FROM users WHERE status = 'active' LIMIT 10;
```

## Security

- ✅ Only SELECT queries allowed
- ✅ SQL injection protection
- ✅ Credentials stored locally in browser
- ✅ No server-side credential storage
- ✅ Read-only database access
- ✅ Chat history persists in localStorage

## Data Persistence

All data is stored in your browser's localStorage:
- **Credentials**: API key and database connection details
- **Chat History**: All your queries and results
- **Settings**: AI provider and database type preferences

Your data persists across browser sessions. To clear:
- Click "Clear Chat" button to remove chat history only
- Clear browser data to reset everything

## Configuration

All configuration is done through the Settings modal:

- **AI Provider**: Choose between Google Gemini or OpenAI
- **API Key**: Your personal API key (stored in browser)
- **Database Type**: PostgreSQL or MySQL
- **Database Credentials**: Host, port, database name, username, password

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Uvicorn
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Google Gemini / OpenAI GPT-4
- **Database**: PostgreSQL / MySQL

## Author

Dhanraj D. Hasure - [Check My Portfolio](https://dhanraj-hasure.github.io)

## License

MIT License
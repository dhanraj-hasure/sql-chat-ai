from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import openai
from google import genai
import sqlparse
import re
from typing import List, Dict, Any
import datetime
from urllib.parse import quote_plus

app = FastAPI(title="SQL Chat By Dhanraj D. Hasure")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config class for storing database and AI provider details
class Config(BaseModel):
    aiProvider: str
    apiKey: str
    dbType: str
    dbHost: str
    dbPort: str
    dbName: str
    dbUser: str
    dbPassword: str

# QueryRequest class for storing query and schema
class QueryRequest(Config):
    query: str
    schema: str = ""


def get_db_url(config: Config) -> str:
    user = quote_plus(config.dbUser)
    password = quote_plus(config.dbPassword)

    if config.dbType == "postgresql":
        return f"postgresql+psycopg2://{user}:{password}@{config.dbHost}:{config.dbPort}/{config.dbName}"

    if config.dbType == "mysql":
        return f"mysql+pymysql://{user}:{password}@{config.dbHost}:{config.dbPort}/{config.dbName}?charset=utf8mb4"

    raise ValueError(f"Unsupported database type: {config.dbType}")

# Getting schema query for the database type
def get_schema_query(config: Config) -> str:
    # postgresql schema query
    if config.dbType == "postgresql":
        return """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """
    else:  # mysql schema query
        return f"""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '{config.dbName}' 
            ORDER BY table_name;
        """

# Ensuring only SELECT queries are executed
def is_safe_select(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    for stmt in parsed:
        if stmt.get_type() != "SELECT":
            return False
    return True

# Fetching schema from the database
@app.post("/api/schema")
async def fetch_schema(config: Config):
    try:
        db_url = get_db_url(config)
        engine = create_engine(db_url, pool_pre_ping=True)
        schema_query = get_schema_query(config)
        
        with engine.connect() as connection:
            result = connection.execute(text(schema_query))
            schema_info = {}
            for row in result:
                table, column, data_type = row
                if table not in schema_info:
                    schema_info[table] = []
                schema_info[table].append(f"{column} ({data_type})")
            
            formatted_schema = "\n".join(
                f"Table: {table}\nColumns: {', '.join(columns)}\n"
                for table, columns in schema_info.items()
            )
            
            return {"schema": formatted_schema.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema fetch failed: {str(e)}")

# Executing direct SQL query (SELECT only)
@app.post("/api/execute")
async def execute_query(request: QueryRequest):
    try:
        query = request.query.strip()
        
        # Remove markdown code blocks if present
        query = re.sub(r"^```sql\s*|\s*```$", "", query, flags=re.MULTILINE)
        
        # Validate it's a SELECT query
        if not is_safe_select(query):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        
        db_url = get_db_url(request)
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            result = connection.execute(text(query))
            columns = result.keys()
            results = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return {"query": query, "results": results}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generating SQL from natural language using AI
@app.post("/api/generate")
async def generate_query(request: QueryRequest):
    try:
        # Generate SQL query using AI
        sql_query = await generate_sql_with_ai(request)
        
        # Execute the generated query
        request.query = sql_query
        result = await execute_query(request)
        
        # Generate summary of the results
        summary = await generate_summary(request, result["results"])
        
        return {
            "sql_query": sql_query,
            "results": result["results"],
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generating SQL query using AI
async def generate_sql_with_ai(request: QueryRequest) -> str:
    prompt = f"""
    Convert the following user query into a read-only {request.dbType.upper()} SELECT query.
    
    Database Schema:
    {request.schema}
    
    Rules:
    - ONLY generate SELECT statements
    - Use proper {request.dbType.upper()} syntax
    - Return only the SQL query, no explanations
    
    User Query: {request.query}
    """
    
    try:
        if request.aiProvider == "openai": # OpenAI API
            openai.api_key = request.apiKey
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            sql = response.choices[0].message.content.strip()
        else:  # Gemini API
            client = genai.Client(api_key=request.apiKey)
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            sql = response.text.strip()
        
        # Clean up the response
        sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.MULTILINE)
        
        # Validate
        if not is_safe_select(sql):
            raise ValueError("Generated query is not a SELECT statement, only SELECT queries are allowed")
        
        return sql
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# Generating summary of the results
async def generate_summary(request: QueryRequest, results: List[Dict]) -> str:
    if not results:
        return "No results found."
    
    prompt = f"""
    Summarize the following query results in 1-2 clear sentences.
    
    User Question: {request.query}
    Results Count: {len(results)}
    Sample Data: {str(results[:3])}
    
    Provide a concise, helpful answer.
    """
    
    try:
        if request.aiProvider == "openai":
            openai.api_key = request.apiKey
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        else:  # gemini
            client = genai.Client(api_key=request.apiKey)
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            return response.text.strip()
    except:
        return f"Found {len(results)} results."

# Serving the landing page
@app.get("/")
async def serve_landing():
    return FileResponse("index.html")

# Serving the dashboard page
@app.get("/dashboard.html")
async def serve_dashboard():
    return FileResponse("dashboard.html")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "app_name": "SQL Chat",
        "app_description": "SQL Chat is a web application that allows users to generate SQL queries using natural language and execute them on their database.",
        "app_version": "1.0.0",
        "status": "SQL Chat is running",
        "timestamp": datetime.datetime.now().isoformat(),
        "developer": {
            "name": "Dhanraj D. Hasure",
            "role": "Full Stack Developer",
            "experience": "1.5+ years",
            "skills": {
                "backend": ["Java", "Spring Boot", "REST APIs", "Python", "FastAPI"],
                "frontend": ["HTML", "CSS", "JavaScript", "Angular"],
                "databases": ["PostgreSQL", "MySQL", "Redis", "MongoDB"],
                "tools": ["Git", "GitHub", "Docker", "Postman"],
                "other": ["AWS", "Render", "Netlify", "OpenAI", "Gemini"]
            },
            "github": "https://github.com/dhanraj-hasure",
            "portfolio": "https://dhanraj-hasure.github.io"
        }
    }


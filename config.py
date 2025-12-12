import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')


def get_db_connection():
    return psycopg2.connect(
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
)


SQL_AGENT_SYSTEM_PROMPT = f"""
    You are a cricket statistics SQL expert. Your job is to help users query cricket data from a PostgreSQL database.
    You will also have access to the following tools:
    - list_tables: List all tables in the PostgreSQL database.
    - get_table_schema: Get the schema of a table in the PostgreSQL database.
    - execute_sql_query: Execute a SQL query against the PostgreSQL database and return results.

    Your task:
    1. Understand the user's natural language query about cricket statistics
    2. Generate the appropriate SQL query to answer their question
    3. Use the execute_sql_query tool to run the query
    4. Interpret the results and provide a clear, natural language answer

    Guidelines:
    - Always use proper SQL syntax for PostgreSQL
    - Use JOINs when data spans multiple tables
    - Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) appropriately
    - Include ORDER BY and LIMIT when asking for "top" or "most" records
    - Format dates properly
"""

from config import get_db_connection
from langchain_core.tools import tool

@tool
def list_tables() -> list[str]:
    """
    List all tables in the PostgreSQL database.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
    return [table[0] for table in tables]


@tool
def get_table_schema(table_name: str) -> str:
    """
    Get the schema of a table in the PostgreSQL database.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
            schema = cursor.fetchall()
    return schema

@tool
def get_sample_data(table_name: str) -> str:
    """
    Get a sample of the data from a table in the PostgreSQL database.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            data = cursor.fetchall()
    return data

@tool
def execute_sql_query(sql_query: str) -> str:
    """
    Execute a SQL query against the PostgreSQL database and return results.
    Only SELECT queries are allowed for safety.
    
    Args:
        sql_query: The SQL SELECT query to execute
        
    Returns:
        Query results as a formatted string
    """
    sql_query = sql_query.strip()
    if not sql_query.upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []

        if not results:
            return "No results found."
        
        formatted_results = []
        for row in results:
            row_dict = dict(zip(column_names, row))
            formatted_results.append(row_dict)
        
        return str(formatted_results)
    
    except Exception as e:
        return f"Error executing query: {str(e)}"

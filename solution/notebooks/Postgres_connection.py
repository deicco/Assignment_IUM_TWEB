from sqlalchemy import create_engine
from sqlalchemy import text
from dotenv import load_dotenv
import psycopg2 as ps
import pandas as pd
import os
from sqlalchemy.dialects.postgresql import psycopg2
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_engine():
    # Crea la connessione al database PostgreSQL
        db_username = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")  # Cambia se necessario
        db_port = os.getenv("DB_PORT") # Cambia se necessario
        db_name = os.getenv("DB_NAME")

        engine = create_engine(
            f"postgresql://postgres:riccardo@localhost:5432/IUM_TWEB?client_encoding=utf8")
        return engine

# Test DB connection

engine = get_db_engine()
try:
    with engine.connect() as conn:
        print("Connection successful")
except Exception as e:
    print(e)
    print("Connection unsuccessful")

# Function to execute INSERT, UPDATE, DELETE queries
def execute_query(sql):
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
            print("Connection successful")
    except Exception as e:
        print(f"Error: {e}")

# Function to execute SELECT queries and return DataFrame

def get_dataframe(query):
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            return df
    except Exception as e:
        print(f"Error: {e}")
        return None
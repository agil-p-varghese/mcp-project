
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Establish a connection to the PostgreSQL database."""

    return psycopg.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD")
    )

# read only connection

def get_readonly_connection():
    """Connect to PostgreSQL using the read-only account."""

    return psycopg.connect(
        host=os.getenv("READONLY_PGHOST"),
        port=os.getenv("READONLY_PGPORT"),
        dbname=os.getenv("READONLY_PGDATABASE"),
        user=os.getenv("READONLY_PGUSER"),
        password=os.getenv("READONLY_PGPASSWORD")
    )

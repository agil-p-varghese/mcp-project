
from fastmcp import FastMCP
from db.connection import get_connection

mcp = FastMCP("BakeHouse Database Analyst")


@mcp.tool()
def inspect_schema() -> dict:
    """
    Inspect the PostgreSQL database schema.

    Returns database name, tables, column names,
    data types, nullable information and primary keys.
    """

    schema_info = {}

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Get database name
            cur.execute("SELECT current_database();")
            database_name = cur.fetchone()[0]

            # Get tables and their columns
            cur.execute("""
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    CASE
                        WHEN pk.column_name IS NOT NULL
                        THEN TRUE
                        ELSE FALSE
                    END AS is_primary_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT
                        ku.table_name,
                        ku.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage ku
                        ON tc.constraint_name = ku.constraint_name
                        AND tc.table_schema = ku.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = 'public'
                ) pk
                    ON c.table_name = pk.table_name
                    AND c.column_name = pk.column_name
                WHERE c.table_schema = 'public'
                ORDER BY c.table_name, c.ordinal_position;
            """)

            rows = cur.fetchall()

            for row in rows:
                table_name = row[0]

                if table_name not in schema_info:
                    schema_info[table_name] = []

                schema_info[table_name].append({
                    "column": row[1],
                    "data_type": row[2],
                    "nullable": row[3] == "YES",
                    "primary_key": row[4]
                })

    return {
        "database": database_name,
        "tables": schema_info
    }

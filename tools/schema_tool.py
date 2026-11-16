import re
from decimal import Decimal
from datetime import date, datetime

from fastmcp import FastMCP
from db.connection import get_connection, get_readonly_connection

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


@mcp.tool()
def execute_readonly_sql(sql: str) -> dict:
    """
    Execute a read-only SQL query against the BakeHouse database.

    Only SELECT and WITH queries are accepted.
    Returns column names, query results and truncation status.
    Maximum returned rows: 1000.
    """

    query = sql.strip().rstrip(";").strip()

    if not query:
        return {"error": "SQL query cannot be empty."}

    if ";" in query:
        return {"error": "Multiple SQL statements are not allowed."}

    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        return {"error": "Only SELECT and WITH queries are allowed."}

    try:
        with get_readonly_connection() as conn:
            with conn.cursor() as cur:

                # Enforce read-only mode for this transaction
                cur.execute("SET TRANSACTION READ ONLY")

                cur.execute(query)

                columns = [desc.name for desc in cur.description]

                rows = cur.fetchmany(1001)

                truncated = len(rows) > 1000
                rows = rows[:1000]

                result_rows = []

                for row in rows:
                    result = {}

                    for column, value in zip(columns, row):
                        if isinstance(value, Decimal):
                            value = str(value)
                        elif isinstance(value, (date, datetime)):
                            value = value.isoformat()

                        result[column] = value

                    result_rows.append(result)

        return {
            "columns": columns,
            "rows": result_rows,
            "returned_rows": len(result_rows),
            "truncated": truncated
        }

    except Exception as e:
        return {"error": str(e)}

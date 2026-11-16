
import psycopg

try:
    conn = psycopg.connect(
        dbname="bakehouse_db",
        user="postgres",
        password="680307",
        host="localhost",
        port="5432"
    )

    print("PostgreSQL connection successful!")

    conn.close()

except Exception as e:
    print("Connection failed:", e)

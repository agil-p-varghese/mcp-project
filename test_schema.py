
from db.connection import get_readonly_connection

with get_readonly_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_user;")
        print("Connected as:", cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM bakery_sales;")
        print("Total records:", cur.fetchone()[0])

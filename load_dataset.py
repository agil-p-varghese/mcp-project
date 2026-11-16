
import csv
import getpass
import psycopg

password = getpass.getpass("PostgreSQL password: ")

csv_path = "datasets/SuperKart.csv"

columns = [
    "Product_Id",
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Type",
    "Product_MRP",
    "Store_Id",
    "Store_Establishment_Year",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Store_Sales_Total"
]

create_table_sql = """
CREATE TABLE IF NOT EXISTS bakery_sales (
    product_id TEXT,
    product_weight NUMERIC(10,2),
    product_sugar_content TEXT,
    product_type TEXT,
    product_mrp NUMERIC(10,2),
    store_id TEXT,
    store_establishment_year INTEGER,
    store_size TEXT,
    store_location_city_type TEXT,
    store_type TEXT,
    product_store_sales_total NUMERIC(12,2)
);
"""

copy_sql = """
COPY bakery_sales (
    product_id,
    product_weight,
    product_sugar_content,
    product_type,
    product_mrp,
    store_id,
    store_establishment_year,
    store_size,
    store_location_city_type,
    store_type,
    product_store_sales_total
) FROM STDIN
"""

try:
    with psycopg.connect(
        dbname="bakehouse_db",
        user="postgres",
        password=password,
        host="localhost",
        port=5432
    ) as conn:

        with conn.cursor() as cur:
            cur.execute(create_table_sql)

            # Clear existing records before reloading
            cur.execute("TRUNCATE TABLE bakery_sales")

            with open(csv_path, "r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                with cur.copy(copy_sql) as copy:
                    for row in reader:
                        copy.write_row(
                            tuple(row[col] for col in columns)
                        )

            cur.execute("SELECT COUNT(*) FROM bakery_sales")
            count = cur.fetchone()[0]

            print(f"Successfully loaded {count} records!")

except Exception as e:
    print("Error:", e)

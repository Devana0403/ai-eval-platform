import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5544")),
        dbname=os.getenv("DB_NAME", "eval_platform"),
        user=os.getenv("DB_USER", "eval_admin"),
        password=os.environ["DB_PASSWORD"],
    )
    print("Connected successfully!")
    conn.close()
except Exception as e:
    print("Connection failed:")
    print(e)

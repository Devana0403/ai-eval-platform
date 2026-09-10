import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5544,
        dbname="eval_platform",
        user="eval_admin",
        password="eval_password_123"
    )
    print("Connected successfully!")
    conn.close()
except Exception as e:
    print("Connection failed:")
    print(e)
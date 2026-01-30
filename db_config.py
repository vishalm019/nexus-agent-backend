import psycopg2

# Database configuration settings
DB_CONFIG = {
    'dbname': 'chatbot', 
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432',
}
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
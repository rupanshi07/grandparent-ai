import psycopg2

DATABASE_URL = "postgresql://neondb_owner:npg_aTnhV9tbN4kg@ep-lingering-poetry-at96prx0-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("ALTER TABLE elders ADD COLUMN IF NOT EXISTS user_id INTEGER DEFAULT 0;")
print("user_id column added or already existed")

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR,
        full_name VARCHAR DEFAULT '',
        google_id VARCHAR UNIQUE,
        created_at TIMESTAMP DEFAULT NOW()
    );
""")
print("users table created or already existed")

conn.commit()
cur.close()
conn.close()
print("Done")
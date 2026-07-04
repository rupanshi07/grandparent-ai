import psycopg2

DATABASE_URL = "paste-your-neon-connection-string-here"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Find the duplicate
cur.execute("SELECT id, name, user_id FROM elders WHERE phone_number = '+918699303323';")
rows = cur.fetchall()
print("Found elders with this number:")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, User ID: {row[2]}")

# Delete all of them so you can re-add cleanly
cur.execute("DELETE FROM elders WHERE phone_number = '+918699303323';")
conn.commit()
print("Deleted successfully!")

cur.close()
conn.close()
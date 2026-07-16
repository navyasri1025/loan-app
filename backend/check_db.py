import sqlite3
conn = sqlite3.connect('app/loan_agent.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print('Tables:', tables)
if 'documents' in tables:
    cur.execute("PRAGMA table_info(documents)")
    print('Documents columns:', cur.fetchall())
conn.close()

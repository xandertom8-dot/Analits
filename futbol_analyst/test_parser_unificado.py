import sqlite3
conn = sqlite3.connect('database/football.db')
c = conn.cursor()
c.execute("PRAGMA table_info(partidos)")
for col in c.fetchall():
    print(col)
conn.close()
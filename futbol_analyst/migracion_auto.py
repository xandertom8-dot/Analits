import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'football.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

try:
    c.execute('ALTER TABLE pronosticos ADD COLUMN automatico INTEGER DEFAULT 0')
    print("✅ Columna 'automatico' añadida")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("ℹ️  Columna 'automatico' ya existe.")
    else:
        raise

conn.commit()
conn.close()
print("\n✅ Migración completada")
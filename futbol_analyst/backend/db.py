# ============================================================
# backend/db.py
# Configuración de la base de datos y creación de tablas.
# ============================================================

import sqlite3
import os

# Ruta raíz del proyecto (un nivel arriba de backend/)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_PATH = os.path.dirname(BACKEND_DIR)

# Ruta de la base de datos
DB_PATH = os.path.join(PROYECTO_PATH, "database", "football.db")


def get_connection():
    """Devuelve una conexión a la BD con row_factory configurado."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Inicializa la base de datos SQLite (solo si no existe)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        pais TEXT,
        liga TEXT,
        temporada TEXT,
        local TEXT,
        visitante TEXT,
        estadisticas_local_raw TEXT,
        estadisticas_visitante_raw TEXT,
        jugadores_local INTEGER,
        jugadores_visitante INTEGER,
        fecha_creacion TEXT,
        tiene_advertencias INTEGER DEFAULT 0,
        advertencias TEXT DEFAULT NULL,
        og_local INTEGER DEFAULT 0,
        og_visitante INTEGER DEFAULT 0,
        timeline_json TEXT DEFAULT NULL,
        resumen_timeline_json TEXT DEFAULT NULL       
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS estadisticas_local (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partido_id INTEGER,
            jugador TEXT,
            G INTEGER, A INTEGER, TR INTEGER, TA INTEGER,
            Crn INTEGER, S INTEGER, SOnT INTEGER, BS INTEGER,
            P INTEGER, C INTEGER, E INTEGER, O INTEGER,
            FC INTEGER, FR INTEGER, SAV INTEGER,
            campos_faltantes TEXT DEFAULT NULL,
            FOREIGN KEY (partido_id) REFERENCES partidos(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS estadisticas_visitante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partido_id INTEGER,
            jugador TEXT,
            G INTEGER, A INTEGER, TR INTEGER, TA INTEGER,
            Crn INTEGER, S INTEGER, SOnT INTEGER, BS INTEGER,
            P INTEGER, C INTEGER, E INTEGER, O INTEGER,
            FC INTEGER, FR INTEGER, SAV INTEGER,
            campos_faltantes TEXT DEFAULT NULL,
            FOREIGN KEY (partido_id) REFERENCES partidos(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partido_id INTEGER,
            mercado TEXT,
            probabilidad REAL,
            cuota_justa REAL,
            cuota_usada REAL,
            ev REAL,
            fecha_analisis TEXT,
            FOREIGN KEY (partido_id) REFERENCES partidos(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

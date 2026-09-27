# ============================================================
# database/aprendizaje.py
# Capa de retroalimentación / auto-calibración del motor.
#
# Persiste en football.db (tabla aprendizaje_modelo) lo que el
# sistema va aprendiendo de sus propios aciertos y fallos, para
# que no se pierda al reiniciar la app.
#
# Tres niveles:
#   1. Sesgo por equipo            -> corrige lambda (goles esperados)
#   2. Calibración de probabilidad -> corrige EV / Kelly por mercado
#   3. Hiperparámetros globales    -> ver nota al final (requiere
#      fecha_corte en obtener_partidos_historicos antes de activarse)
# ============================================================

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "football.db")

# ============================================================
# CONFIG
# ============================================================
MIN_MUESTRAS_SESGO = 8          # mínimo de partidos cerrados para confiar en el sesgo de un equipo
MIN_MUESTRAS_CALIBRACION = 5    # mínimo de muestras por bin para calibrar un mercado
CAP_SESGO_GOLES = 0.5           # tope absoluto de corrección de lambda (goles)
CAP_SESGO_RELATIVO = 0.20       # tope relativo: no corregir más del 20% de lambda
DAMPING_SESGO = 0.7             # no aplicar el 100% del sesgo medido (evita sobreajuste)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tabla_aprendizaje():
    """Crea la tabla de aprendizaje si no existe. Llamar una vez al arrancar la app."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS aprendizaje_modelo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            clave TEXT NOT NULL,
            valor TEXT NOT NULL,
            n_muestras INTEGER DEFAULT 0,
            fecha_actualizacion TEXT,
            UNIQUE(tipo, clave)
        )
    ''')
    conn.commit()
    conn.close()


def _guardar(tipo, clave, valor_dict, n_muestras):
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO aprendizaje_modelo (tipo, clave, valor, n_muestras, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tipo, clave) DO UPDATE SET
                valor = excluded.valor,
                n_muestras = excluded.n_muestras,
                fecha_actualizacion = excluded.fecha_actualizacion
        ''', (tipo, clave, json.dumps(valor_dict, ensure_ascii=False), n_muestras, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def _leer(tipo, clave):
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute('SELECT valor, n_muestras, fecha_actualizacion FROM aprendizaje_modelo WHERE tipo = ? AND clave = ?', (tipo, clave))
        row = c.fetchone()
        if not row:
            return None
        return {
            'valor': json.loads(row['valor']),
            'n_muestras': row['n_muestras'],
            'fecha_actualizacion': row['fecha_actualizacion'],
        }
    finally:
        conn.close()


def _leer_todos(tipo):
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute('SELECT clave, valor, n_muestras, fecha_actualizacion FROM aprendizaje_modelo WHERE tipo = ?', (tipo,))
        resultado = {}
        for row in c.fetchall():
            resultado[row['clave']] = {
                'valor': json.loads(row['valor']),
                'n_muestras': row['n_muestras'],
                'fecha_actualizacion': row['fecha_actualizacion'],
            }
        return resultado
    finally:
        conn.close()


# ============================================================
# NIVEL 1 — SESGO POR EQUIPO
# ============================================================
def recalcular_sesgos_equipos(fecha_corte=None):
    """
    Recorre todos los pronósticos cerrados con lambda predicho y resultado real,
    y calcula el sesgo medio (predicho - real) por equipo y condición (local/visitante).
    Guarda el resultado en aprendizaje_modelo bajo tipo='sesgo_equipo'.
    
    Args:
        fecha_corte: si se especifica ('YYYY-MM-DD'), solo usa pronósticos cerrados
                     con fecha_cierre < fecha_corte. Evita data leakage en backtesting.
                     Si es None, usa todos los pronósticos cerrados.
    """
    conn = _conn()
    c = conn.cursor()
    try:
        # ========== Filtro dinámico de fecha ==========
        filtro_fecha = ''
        params = []
        if fecha_corte:
            filtro_fecha = ' AND fecha_cierre < ?'
            params = [fecha_corte]
        
        c.execute(f'''
            SELECT partido_local, partido_visitante, lambda_local_pred, lambda_visitante_pred,
                   resultado_local, resultado_visitante
            FROM pronosticos
            WHERE cerrado = 1
              AND lambda_local_pred IS NOT NULL
              AND lambda_visitante_pred IS NOT NULL
              AND resultado_local IS NOT NULL
              AND resultado_visitante IS NOT NULL
              {filtro_fecha}
        ''', params)
        rows = c.fetchall()
    finally:
        conn.close()

    acumulado = {}  # {(equipo, 'local'|'visitante'): [errores]}

    for r in rows:
        acumulado.setdefault((r['partido_local'], 'local'), []).append(
            r['lambda_local_pred'] - r['resultado_local']
        )
        acumulado.setdefault((r['partido_visitante'], 'visitante'), []).append(
            r['lambda_visitante_pred'] - r['resultado_visitante']
        )

    actualizados = 0
    for (equipo, condicion), errores in acumulado.items():
        n = len(errores)
        if n < MIN_MUESTRAS_SESGO:
            continue
        sesgo_medio = sum(errores) / n
        sesgo_capado = max(-CAP_SESGO_GOLES, min(CAP_SESGO_GOLES, sesgo_medio))
        clave = f'{equipo}|{condicion}'
        _guardar('sesgo_equipo', clave, {'sesgo': round(sesgo_capado, 4), 'sesgo_bruto': round(sesgo_medio, 4)}, n)
        actualizados += 1

    return {'equipos_actualizados': actualizados, 'total_pronosticos_usados': len(rows)}


def obtener_correccion_lambda(equipo, como_local, fecha_corte=None):
    """
    Devuelve el ajuste (en goles) a restar de lambda para este equipo/condición,
    ya amortiguado y listo para aplicar. 0.0 si no hay datos suficientes.
    
    Args:
        equipo: nombre del equipo
        como_local: True/False
        fecha_corte: si se especifica, la corrección se calcula al vuelo
                     con solo los pronósticos cerrados antes de esa fecha.
                     Si es None, usa la corrección ya guardada en la tabla.
    """
    condicion = 'local' if como_local else 'visitante'
    
    # ========== Si hay fecha_corte, recalcular al vuelo ==========
    if fecha_corte:
        sesgos = _recalcular_sesgos_al_vuelo(fecha_corte)
        clave = f'{equipo}|{condicion}'
        if clave not in sesgos:
            return 0.0
        sesgo_data = sesgos[clave]
        if sesgo_data['n_muestras'] < MIN_MUESTRAS_SESGO:
            return 0.0
        sesgo = sesgo_data['sesgo']
        confianza = min(sesgo_data['n_muestras'] / 30.0, 1.0)
        return sesgo * DAMPING_SESGO * confianza
    
    # ========== Sin fecha_corte: usar la tabla persistida ==========
    dato = _leer('sesgo_equipo', f'{equipo}|{condicion}')
    if not dato or dato['n_muestras'] < MIN_MUESTRAS_SESGO:
        return 0.0
    sesgo = dato['valor']['sesgo']
    confianza = min(dato['n_muestras'] / 30.0, 1.0)
    return sesgo * DAMPING_SESGO * confianza


def aplicar_correccion_lambda(lam, equipo, como_local, fecha_corte=None):
    """
    Aplica la corrección de sesgo aprendida a un lambda ya calculado.
    Nunca corrige más del CAP_SESGO_RELATIVO (20%) del valor original.
    
    Si fecha_corte se especifica, calcula el sesgo solo con pronósticos anteriores.
    """
    correccion = obtener_correccion_lambda(equipo, como_local, fecha_corte=fecha_corte)
    if correccion == 0.0:
        return lam
    tope = lam * CAP_SESGO_RELATIVO
    correccion = max(-tope, min(tope, correccion))
    lam_corregido = lam - correccion
    return max(0.2, min(5.0, lam_corregido))


# ============================================================
# CÁLCULO DE SESGOS AL VUELO (para backtesting sin leakage)
# ============================================================
def _recalcular_sesgos_al_vuelo(fecha_corte):
    """
    Calcula los sesgos de todos los equipos usando SOLO los pronósticos
    cerrados antes de `fecha_corte`. NO persiste en la tabla.
    
    Returns:
        {
            'equipo|condicion': {
                'sesgo': float,
                'sesgo_bruto': float,
                'n_muestras': int,
            },
            ...
        }
    """
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT partido_local, partido_visitante, lambda_local_pred, lambda_visitante_pred,
                   resultado_local, resultado_visitante
            FROM pronosticos
            WHERE cerrado = 1
              AND lambda_local_pred IS NOT NULL
              AND lambda_visitante_pred IS NOT NULL
              AND resultado_local IS NOT NULL
              AND resultado_visitante IS NOT NULL
              AND fecha_cierre < ?
        ''', (fecha_corte,))
        rows = c.fetchall()
    finally:
        conn.close()
    
    acumulado = {}
    for r in rows:
        acumulado.setdefault((r['partido_local'], 'local'), []).append(
            r['lambda_local_pred'] - r['resultado_local']
        )
        acumulado.setdefault((r['partido_visitante'], 'visitante'), []).append(
            r['lambda_visitante_pred'] - r['resultado_visitante']
        )
    
    resultado = {}
    for (equipo, condicion), errores in acumulado.items():
        n = len(errores)
        sesgo_medio = sum(errores) / n
        sesgo_capado = max(-CAP_SESGO_GOLES, min(CAP_SESGO_GOLES, sesgo_medio))
        clave = f'{equipo}|{condicion}'
        resultado[clave] = {
            'sesgo': round(sesgo_capado, 4),
            'sesgo_bruto': round(sesgo_medio, 4),
            'n_muestras': n,
        }
    
    return resultado


# ============================================================
# NIVEL 2 — CALIBRACIÓN DE PROBABILIDADES POR MERCADO
# ============================================================
_MERCADOS_CALIBRABLES = {
    '1X2_local':     (['mercados', '1X2', 'local'],     lambda mj: 1 if mj['goles_local'] > mj['goles_visitante'] else 0),
    '1X2_empate':    (['mercados', '1X2', 'empate'],    lambda mj: 1 if mj['goles_local'] == mj['goles_visitante'] else 0),
    '1X2_visitante': (['mercados', '1X2', 'visitante'], lambda mj: 1 if mj['goles_local'] < mj['goles_visitante'] else 0),
    'BTTS':          (['mercados', 'BTTS'],             lambda mj: mj.get('btts')),
    'over_1.5':      (['mercados', 'over', '1.5'],      lambda mj: mj.get('over15')),
    'over_2.5':      (['mercados', 'over', '2.5'],      lambda mj: mj.get('over25')),
    'over_3.5':      (['mercados', 'over', '3.5'],      lambda mj: mj.get('over35')),
}


def _get_path(d, path):
    val = d
    for key in path:
        if isinstance(val, dict):
            val = val.get(key)
        else:
            return None
        if val is None:
            return None
    return val


def recalcular_calibracion_mercados(n_bins=10, fecha_corte=None):
    """
    Para cada mercado calibrable, agrupa las probabilidades predichas históricas
    en bins de 10% y calcula la frecuencia real observada en cada bin.
    Guarda una curva de calibración (lista de puntos) por mercado.
    
    Args:
        n_bins: número de bins
        fecha_corte: si se especifica, usa solo pronósticos cerrados antes de esa fecha.
    """
    conn = _conn()
    c = conn.cursor()
    try:
        # ========== Filtro dinámico ==========
        filtro_fecha = ''
        params = []
        if fecha_corte:
            filtro_fecha = ' AND fecha_cierre < ?'
            params = [fecha_corte]
        
        c.execute(f'''
            SELECT pronostico_json, resultado_mercados_json
            FROM pronosticos
            WHERE cerrado = 1
              AND pronostico_json IS NOT NULL AND pronostico_json != ''
              AND resultado_mercados_json IS NOT NULL AND resultado_mercados_json != ''
              {filtro_fecha}
        ''', params)
        rows = c.fetchall()
    finally:
        conn.close()

    actualizados = 0

    for mercado, (path, get_real) in _MERCADOS_CALIBRABLES.items():
        bins = [[] for _ in range(n_bins)]

        for row in rows:
            try:
                pj = json.loads(row['pronostico_json'])
                mj = json.loads(row['resultado_mercados_json'])
            except Exception:
                continue

            prob = _get_path(pj, path)
            try:
                real = get_real(mj)
            except Exception:
                real = None

            if prob is None or real is None:
                continue

            idx = min(int(prob * n_bins), n_bins - 1)
            bins[idx].append(real)

        puntos = []
        n_total = 0
        for i, bin_data in enumerate(bins):
            if len(bin_data) < MIN_MUESTRAS_CALIBRACION:
                continue
            centro_predicho = (i + 0.5) / n_bins
            frecuencia_real = sum(bin_data) / len(bin_data)
            puntos.append({'predicho': round(centro_predicho, 3), 'real': round(frecuencia_real, 3), 'n': len(bin_data)})
            n_total += len(bin_data)

        if len(puntos) >= 2:
            _guardar('calibracion_mercado', mercado, {'puntos': puntos}, n_total)
            actualizados += 1

    return {'mercados_calibrados': actualizados, 'total_pronosticos_usados': len(rows)}


def aplicar_calibracion(prob, mercado, fecha_corte=None):
    """
    Ajusta una probabilidad del modelo usando la curva de calibración aprendida
    para ese mercado (interpolación lineal). Si no hay datos suficientes,
    devuelve prob sin tocar.
    
    Si fecha_corte se especifica, se usa la calibración ya persistida
    (asumimos que la tabla refleja el estado sin leakage).
    """
    if prob is None:
        return prob

    dato = _leer('calibracion_mercado', mercado)
    if not dato:
        return prob

    puntos = sorted(dato['valor']['puntos'], key=lambda p: p['predicho'])
    if len(puntos) < 2:
        return prob

    if prob <= puntos[0]['predicho']:
        return puntos[0]['real']
    if prob >= puntos[-1]['predicho']:
        return puntos[-1]['real']

    for i in range(len(puntos) - 1):
        p0, p1 = puntos[i], puntos[i + 1]
        if p0['predicho'] <= prob <= p1['predicho']:
            if p1['predicho'] == p0['predicho']:
                return p0['real']
            t = (prob - p0['predicho']) / (p1['predicho'] - p0['predicho'])
            return p0['real'] + t * (p1['real'] - p0['real'])

    return prob


# ============================================================
# NIVEL 3 — HIPERPARÁMETROS GLOBALES (placeholder deliberado)
# ============================================================
# NO se implementa el grid search todavía. Razón honesta:
# obtener_partidos_historicos() siempre trae los N partidos MÁS
# RECIENTES de la BD completa, sin corte de fecha. Si se re-simula
# un pronóstico histórico con eso, el modelo "ve" partidos posteriores
# a la fecha que se está pronosticando -> fuga de información (data
# leakage) y el resultado del tuning no sería de fiar.
#
# Antes de activar esto hace falta añadir un parámetro fecha_corte a
# obtener_partidos_historicos() (filtro "AND p.fecha < fecha_corte").
# Es un cambio quirúrgico pero toca el corazón del motor, así que
# conviene hacerlo aparte y probarlo bien antes de usarlo para tuning.
#
# Estas dos funciones ya dejan el mecanismo de persistencia listo para
# cuando ese replay exista:

def obtener_hiperparametros_activos():
    dato = _leer('hiperparametro', 'global')
    if not dato:
        return {}
    return dato['valor']


def guardar_hiperparametros(valores, n_muestras):
    _guardar('hiperparametro', 'global', valores, n_muestras)


# ============================================================
# RECALCULAR TODO (llamar tras cerrar cada pronóstico)
# ============================================================
def recalcular_aprendizaje_completo(fecha_corte=None):
    """
    Recalcula TODO el aprendizaje. Si fecha_corte se especifica,
    usa solo pronósticos cerrados antes de esa fecha.
    """
    init_tabla_aprendizaje()
    r1 = recalcular_sesgos_equipos(fecha_corte=fecha_corte)
    r2 = recalcular_calibracion_mercados(fecha_corte=fecha_corte)
    return {'sesgos': r1, 'calibracion': r2}


# ============================================================
# VISTA DE ESTADO (para la UI / debug)
# ============================================================
def estado_aprendizaje():
    return {
        'sesgos_equipos': _leer_todos('sesgo_equipo'),
        'calibracion_mercados': _leer_todos('calibracion_mercado'),
        'hiperparametros': _leer_todos('hiperparametro'),
    }

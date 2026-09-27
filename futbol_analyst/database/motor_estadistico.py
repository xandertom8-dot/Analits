"""
============================================================
MOTOR ESTADÍSTICO MEJORADO - VERSIÓN 2.0
============================================================
Incluye:
- Ventana temporal configurable (últimos 5, 10, temporada)
- Ponderación exponencial (0.85^índice)
- Filtro de antigüedad máxima (18 meses)
- Filtro de competición con pesos contextuales
- Detección de jugadores activos/inactivos
- Detección de tendencias (sube/baja/estable)
- Modelo Poisson para goles
- Nivel de confianza
============================================================
"""

# ============================================================
# MODIFICADORES ACTIVOS DEL MOTOR (FASE A)
# ============================================================
# Cada modificador puede activarse/desactivarse sin tocar código.
# Esto permite backtesting A/B para medir si cada uno aporta valor.
#
# Categorías:
#   - Modifican λ: cambian el resultado de la predicción.
#   - Contexto: solo informan, NO modifican λ.
# ============================================================

MODIFICADORES_ACTIVOS = {
    # ===== Modificadores que afectan a λ =====
    'decay':              True,   # Ponderación exponencial por recencia (0.85^n)
    'suavizado':          True,   # Shrinkage hacia promedio de liga (k=5)
    'localia_generica':   True,   # 1.15 / 0.90 por defecto
    'localia_empirica':   True,   # Localía calculada del equipo
    'localia_liga':       True,   # Localía calculada de la liga
    'tendencia':          True,   # Subiendo/bajando/estable
    'racha':              True,   # Racha larga (5+ partidos)
    'racha_v2':           True,   # Racha últimos 3 partidos
    'ratio':              True,   # Ratio ataque/defensa
    'diferencial':        True,   # Diferencial de goles
    'peso_competicion':   True,   # Peso por tipo de competición
    'peso_rival':         False,  # ⚠️ Desactivado por FASE A (Δ MAE = -0.0142)
    'negbin':             True,   # NegBin si overdispersion
    'dixon_coles':        True,   # Corrección de marcadores bajos
    'aprendizaje_sesgo':  True,   # Corrección por sesgo aprendido
    
    # ===== Modificadores que NO afectan a λ (solo contexto) =====
    'contexto':           True,   # clean sheets, failed to score, CV
}


def modificador_activo(nombre):
    """Comprueba si un modificador está activo. Default: True."""
    return MODIFICADORES_ACTIVOS.get(nombre, True)


def set_modificador(nombre, activo):
    """Activa/desactiva un modificador en runtime (no persiste)."""
    if nombre in MODIFICADORES_ACTIVOS:
        MODIFICADORES_ACTIVOS[nombre] = bool(activo)
        return True
    return False


def reset_modificadores():
    """Restaura todos los modificadores a True."""
    for k in MODIFICADORES_ACTIVOS:
        MODIFICADORES_ACTIVOS[k] = True

from collections import defaultdict
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "football.db")

# ============================================================
# CONFIGURACIÓN
# ============================================================
VERSION_MOTOR = "v2.0"

# Antigüedad máxima: 18 meses (548 días)
ANTIGUEDAD_MAXIMA_DIAS = 548

# Ponderación exponencial
FACTOR_DECAY = 0.85

# Pesos por tipo de competición
PESO_COMPETICION = {
    "misma": 1.00,  # Misma competición del partido a pronosticar
    "internacional_top": 0.80,  # Champions League
    "internacional_media": 0.70,  # Europa League, Conference
    "copa_nacional": 0.60,  # Copa del Rey, FA Cup, etc.
    "otras_ligas": 0.50,  # Otras competiciones domésticas
    "amistoso": 0.00,  # Amistosos (se ignoran)
}

# Ventanas temporales y sus pesos base
VENTANAS = {
    "ultimos_5": {"n": 5, "peso_base": 1.00},
    "ultimos_10": {"n": 10, "peso_base": 0.85},
    "temporada": {"n": 999, "peso_base": 0.70},
}

# Mínimo de partidos para distintos niveles
MIN_PARTIDOS_BAJO = 3
MIN_PARTIDOS_MEDIO = 5
MIN_PARTIDOS_ALTO = 10

# Umbral para considerar un jugador "activo"
UMBRAL_JUGADOR_ACTIVO = 3  # Aparece en últimos 3 partidos

# ============================================================
# CONFIGURACIÓN DE SUAVIZADO Y FUERZA DEL RIVAL (5B)
# ============================================================
FACTOR_SUAVIZADO = 5.0

SUAVIZAR_METRICAS = {
    "goles": True,
    "tiros": True,
    "tiros_puerta": True,
    "corners": False,
    "faltas": False,
    "tarjetas_amarillas": False,
    "tarjetas_rojas": False,
    "paradas": False,
    "tiros_bloqueados": False,
}

PONDERAR_POR_RIVAL = True
AJUSTE_RIVAL_MIN = 0.67
AJUSTE_RIVAL_MAX = 1.50

# ✅ AÑADIR ESTO:
# ============================================================
# CONFIGURACIÓN DE LOCALÍA (5B.3)
# ============================================================
FACTOR_LOCALIA_GENERICO_LOCAL = 1.15
FACTOR_LOCALIA_GENERICO_VISITANTE = 0.90
MIN_PARTIDOS_LOCALIA = 3

VENTANAS_MULTIPLES = {
    "ultimos_3": {"n": 3, "peso": 1.10},
    "ultimos_5": {"n": 5, "peso": 1.00},
    "ultimos_8": {"n": 8, "peso": 0.90},
    "ultimos_10": {"n": 10, "peso": 0.85},
    "temporada": {"n": 999, "peso": 0.75},
}

# Rachas
RACHA_MINIMA = 3  # Mínimo partidos para considerar racha
AJUSTE_RACHA_MAX = 0.15  # ±15% máximo de ajuste


# ============================================================
# UTILIDADES
# ============================================================
def _parsear_fecha(fecha_str):
    """Convierte string de fecha a objeto date"""
    if not fecha_str:
        return None
    try:
        if "T" in fecha_str:
            return datetime.fromisoformat(fecha_str).date()
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _calcular_dias_atras(fecha_str):
    """Días transcurridos desde la fecha hasta hoy"""
    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return 99999
    return (datetime.now().date() - fecha).days


def _clasificar_competicion(liga_partido, liga_pronostico):
    """Devuelve el peso de una competición según el contexto"""
    if not liga_partido:
        return PESO_COMPETICION["otras_ligas"]

    if liga_partido == liga_pronostico:
        return PESO_COMPETICION["misma"]

    lp = liga_partido.lower()

    if "champions" in lp:
        return PESO_COMPETICION["internacional_top"]
    if "europa league" in lp or "conference" in lp:
        return PESO_COMPETICION["internacional_media"]
    if "copa" in lp or "cup" in lp or "coupe" in lp:
        return PESO_COMPETICION["copa_nacional"]
    if "amistoso" in lp or "friendl" in lp or "test" in lp:
        return PESO_COMPETICION["amistoso"]

    return PESO_COMPETICION["otras_ligas"]


# ============================================================
# FEATURES AVANZADAS (FASE 8.6)
# ============================================================


def _calcular_factor_ratio(stats_equipo, stats_rival):
    """
    Factor basado en el ratio ataque/defensa del equipo.

    Lógica:
    - ratio > 1.2 → equipo ofensivo → λ sube (factor > 1)
    - ratio < 0.8 → equipo defensivo → λ baja (factor < 1)
    - entre 0.8 y 1.2 → neutro (factor = 1)

    Cap: ±5%.
    """
    goles_propios = stats_equipo.get("goles")
    goles_recibidos = stats_equipo.get("rival_goles")

    if goles_propios is None or goles_recibidos is None:
        return 1.0, None

    # Evitar división por 0
    if goles_recibidos == 0:
        goles_recibidos = 0.1

    ratio = goles_propios / goles_recibidos

    # Mapeo a factor: neutro en 1.0, ±5% según desviación
    if 0.8 <= ratio <= 1.2:
        factor = 1.0
    elif ratio > 1.2:
        # Equipo ofensivo: sube hasta +5%
        factor = 1.0 + min((ratio - 1.2) * 0.1, 0.05)
    else:
        # Equipo defensivo: baja hasta -5%
        factor = 1.0 - min((0.8 - ratio) * 0.1, 0.05)

    return round(factor, 4), round(ratio, 3)


def _calcular_factor_diferencial(stats_equipo):
    """
    Factor basado en el diferencial de goles (marcados - recibidos).

    Lógica:
    - diff > +5 → equipo dominante → λ sube (+5%)
    - diff < -5 → equipo flojo → λ baja (-5%)
    - entre -5 y +5 → neutro

    Cap: ±5%.
    """
    goles_propios = stats_equipo.get("goles")
    goles_recibidos = stats_equipo.get("rival_goles")

    if goles_propios is None or goles_recibidos is None:
        return 1.0, None

    diff = goles_propios - goles_recibidos

    # Mapeo a factor: neutro en 0, ±5% según desviación
    if diff > 5:
        factor = 1.05
    elif diff < -5:
        factor = 0.95
    else:
        # Escala lineal entre -5 y +5 → ±5%
        factor = 1.0 + (diff * 0.01)

    return round(factor, 4), round(diff, 3)


def _calcular_factor_racha_v2(equipo, liga_pronostico=None, como_local=None, fecha_corte=None):
    """
    Factor de racha reciente mejorada.

    Mira los últimos 3 partidos y calcula un factor según:
    - Victorias seguidas → +3%
    - Derrotas seguidas → -3%
    - Mixto → neutro

    Cap: ±3%.
    """
    # Obtener últimos 5 partidos (para tener margen)
    partidos = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=5,
        fecha_corte=fecha_corte
    )

    if len(partidos) < 3:
        return 1.0, "sin_datos"

    # Ordenar por fecha descendente
    partidos_ordenados = sorted(
        partidos, key=lambda x: x.get("fecha") or "", reverse=True
    )

    # Analizar últimos 3
    ultimos_3 = partidos_ordenados[:3]

    victorias = 0
    derrotas = 0
    empates = 0

    for p in ultimos_3:
        goles_propios = p.get("goles")
        goles_rival = p.get("rival_goles")
        if goles_propios is None or goles_rival is None:
            continue
        if goles_propios > goles_rival:
            victorias += 1
        elif goles_propios < goles_rival:
            derrotas += 1
        else:
            empates += 1

    if victorias == 3:
        factor = 1.03
        tipo = "3_victorias"
    elif derrotas == 3:
        factor = 0.97
        tipo = "3_derrotas"
    elif victorias == 2 and derrotas == 0:
        factor = 1.02
        tipo = "2v_1e"
    elif derrotas == 2 and victorias == 0:
        factor = 0.98
        tipo = "2d_1e"
    else:
        factor = 1.0
        tipo = "mixto"

    return round(factor, 4), tipo


def calcular_contexto_features(partidos, stats_equipo=None):
    """
    Calcula features de contexto para un equipo:
    - Clean Sheets %: % de partidos sin recibir goles
    - Failed to Score %: % de partidos sin marcar
    - CV de goles: coeficiente de variación (regularidad del ataque)
    - CV de goles recibidos: regularidad de la defensa

    Args:
        partidos: lista de dicts con 'goles' y 'rival_goles'
        stats_equipo: opcional, para reusar promedios ya calculados

    Returns:
        {
            'clean_sheets_pct': float (0-100),
            'failed_to_score_pct': float (0-100),
            'cv_goles': float,
            'cv_goles_recibidos': float,
            'partidos_analizados': int,
            'interpretacion': {
                'defensa': str,  # 'solida' | 'normal' | 'floja'
                'ataque': str,   # 'regular' | 'normal' | 'irregular'
                'fiabilidad': str,  # 'alta' | 'media' | 'baja'
            }
        }
    """
    import statistics

    if not partidos:
        return {
            "clean_sheets_pct": None,
            "failed_to_score_pct": None,
            "cv_goles": None,
            "cv_goles_recibidos": None,
            "partidos_analizados": 0,
            "interpretacion": {
                "defensa": "sin_datos",
                "ataque": "sin_datos",
                "fiabilidad": "sin_datos",
            },
        }

    # Filtrar partidos con datos válidos
    goles_list = [p.get("goles") for p in partidos if p.get("goles") is not None]
    rival_goles_list = [
        p.get("rival_goles") for p in partidos if p.get("rival_goles") is not None
    ]

    n_goles = len(goles_list)
    n_rival = len(rival_goles_list)

    # Clean sheets
    clean_sheets_pct = None
    if n_rival > 0:
        clean_sheets = sum(1 for g in rival_goles_list if g == 0)
        clean_sheets_pct = round(clean_sheets / n_rival * 100, 1)

    # Failed to score
    failed_to_score_pct = None
    if n_goles > 0:
        fts = sum(1 for g in goles_list if g == 0)
        failed_to_score_pct = round(fts / n_goles * 100, 1)

    # CV de goles marcados
    cv_goles = None
    if n_goles >= 3:
        media = statistics.mean(goles_list)
        if media > 0:
            desv = statistics.stdev(goles_list)
            cv_goles = round(desv / media, 3)

    # CV de goles recibidos
    cv_goles_recibidos = None
    if n_rival >= 3:
        media_r = statistics.mean(rival_goles_list)
        if media_r > 0:
            desv_r = statistics.stdev(rival_goles_list)
            cv_goles_recibidos = round(desv_r / media_r, 3)

    # ========== Interpretaciones ==========
    # Defensa
    if clean_sheets_pct is None:
        defensa_interp = "sin_datos"
    elif clean_sheets_pct >= 50:
        defensa_interp = "solida"
    elif clean_sheets_pct >= 25:
        defensa_interp = "normal"
    else:
        defensa_interp = "floja"

    # Ataque (según consistencia)
    if cv_goles is None:
        ataque_interp = "sin_datos"
    elif cv_goles < 0.7:
        ataque_interp = "regular"
    elif cv_goles < 1.2:
        ataque_interp = "normal"
    else:
        ataque_interp = "irregular"

    # Fiabilidad global
    if cv_goles is None or cv_goles_recibidos is None:
        fiabilidad = "sin_datos"
    else:
        cv_promedio = (cv_goles + cv_goles_recibidos) / 2
        if cv_promedio < 0.8:
            fiabilidad = "alta"
        elif cv_promedio < 1.3:
            fiabilidad = "media"
        else:
            fiabilidad = "baja"

    return {
        "clean_sheets_pct": clean_sheets_pct,
        "failed_to_score_pct": failed_to_score_pct,
        "cv_goles": cv_goles,
        "cv_goles_recibidos": cv_goles_recibidos,
        "partidos_analizados": len(partidos),
        "interpretacion": {
            "defensa": defensa_interp,
            "ataque": ataque_interp,
            "fiabilidad": fiabilidad,
        },
    }


# ============================================================
# OBTENER PARTIDOS HISTÓRICOS
# ============================================================
def obtener_partidos_historicos(
    equipo, como_local=None, liga_pronostico=None, limite=30, fecha_corte=None
):
    """
    Obtiene los partidos históricos de un equipo con estadísticas propias Y del rival.
    
    Args:
        equipo: nombre del equipo
        como_local: None (ambos) | True (solo local) | False (solo visitante)
        liga_pronostico: liga de contexto
        limite: máximo de partidos a devolver
        fecha_corte: si se especifica (formato 'YYYY-MM-DD'), solo devuelve partidos
                     con fecha < fecha_corte. Útil para backtesting sin data leakage.
                     Si es None, comportamiento actual (sin filtro).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    partidos = []
    # ========== Construir filtro dinámico de fecha ==========
    filtro_fecha = ''
    params_fecha = []
    if fecha_corte:
        filtro_fecha = ' AND p.fecha < ?'
        params_fecha = [fecha_corte]

    try:
        # ===== Como LOCAL =====
        if como_local is None or como_local is True:
            c.execute(
                f"""
                SELECT 
                    p.id, p.fecha, p.liga, p.temporada,
                    p.local as equipo, p.visitante as rival,
                    'local' as condicion,
                    SUM(el.G) as goles,
                    SUM(el.S) as tiros,
                    SUM(el.SOnT) as tiros_puerta,
                    SUM(el.Crn) as corners,
                    SUM(el.FC) as faltas,
                    SUM(el.FR) as faltas_recibidas,
                    SUM(el.SAV) as paradas,
                    SUM(el.TA) as tarjetas_amarillas,
                    SUM(el.TR) as tarjetas_rojas,
                    SUM(el.P) as pases,
                    SUM(el.C) as centros,
                    SUM(el.E) as entradas,
                    SUM(el.O) as fueras_juego,
                    SUM(el.BS) as tiros_bloqueados,
                    (SELECT COALESCE(SUM(G), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_goles,
                    (SELECT COALESCE(SUM(S), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_tiros,
                    (SELECT COALESCE(SUM(SOnT), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_tiros_puerta,
                    (SELECT COALESCE(SUM(Crn), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_corners,
                    (SELECT COALESCE(SUM(FC), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_faltas,
                    (SELECT COALESCE(SUM(FR), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_faltas_recibidas,
                    (SELECT COALESCE(SUM(SAV), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_paradas,
                    (SELECT COALESCE(SUM(TA), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_tarjetas_amarillas,
                    (SELECT COALESCE(SUM(TR), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_tarjetas_rojas,
                    (SELECT COALESCE(SUM(P), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_pases,
                    (SELECT COALESCE(SUM(C), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_centros,
                    (SELECT COALESCE(SUM(E), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_entradas,
                    (SELECT COALESCE(SUM(O), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_fueras_juego,
                    (SELECT COALESCE(SUM(BS), 0) FROM estadisticas_visitante WHERE partido_id = p.id) as rival_tiros_bloqueados,
                    COALESCE(p.og_local, 0) as og_propio,
                    COALESCE(p.og_visitante, 0) as og_rival
                FROM partidos p
                JOIN estadisticas_local el ON el.partido_id = p.id
                WHERE p.local = ?{filtro_fecha}
                GROUP BY p.id
                ORDER BY p.fecha DESC
                LIMIT ?
            """,
                [equipo] + params_fecha + [limite],
            )
            for row in c.fetchall():
                partidos.append(dict(row))

        # ===== Como VISITANTE =====
        if como_local is None or como_local is False:
            c.execute(
                f"""
                SELECT 
                    p.id, p.fecha, p.liga, p.temporada,
                    p.visitante as equipo, p.local as rival,
                    'visitante' as condicion,
                    SUM(ev.G) as goles,
                    SUM(ev.S) as tiros,
                    SUM(ev.SOnT) as tiros_puerta,
                    SUM(ev.Crn) as corners,
                    SUM(ev.FC) as faltas,
                    SUM(ev.FR) as faltas_recibidas,
                    SUM(ev.SAV) as paradas,
                    SUM(ev.TA) as tarjetas_amarillas,
                    SUM(ev.TR) as tarjetas_rojas,
                    SUM(ev.P) as pases,
                    SUM(ev.C) as centros,
                    SUM(ev.E) as entradas,
                    SUM(ev.O) as fueras_juego,
                    SUM(ev.BS) as tiros_bloqueados,
                    (SELECT COALESCE(SUM(G), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_goles,
                    (SELECT COALESCE(SUM(S), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_tiros,
                    (SELECT COALESCE(SUM(SOnT), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_tiros_puerta,
                    (SELECT COALESCE(SUM(Crn), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_corners,
                    (SELECT COALESCE(SUM(FC), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_faltas,
                    (SELECT COALESCE(SUM(FR), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_faltas_recibidas,
                    (SELECT COALESCE(SUM(SAV), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_paradas,
                    (SELECT COALESCE(SUM(TA), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_tarjetas_amarillas,
                    (SELECT COALESCE(SUM(TR), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_tarjetas_rojas,
                    (SELECT COALESCE(SUM(P), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_pases,
                    (SELECT COALESCE(SUM(C), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_centros,
                    (SELECT COALESCE(SUM(E), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_entradas,
                    (SELECT COALESCE(SUM(O), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_fueras_juego,
                    (SELECT COALESCE(SUM(BS), 0) FROM estadisticas_local WHERE partido_id = p.id) as rival_tiros_bloqueados,
                    COALESCE(p.og_visitante, 0) as og_propio,
                    COALESCE(p.og_local, 0) as og_rival
                FROM partidos p
                JOIN estadisticas_visitante ev ON ev.partido_id = p.id
                WHERE p.visitante = ?{filtro_fecha}
                GROUP BY p.id
                ORDER BY p.fecha DESC
                LIMIT ?
            """,
                [equipo] + params_fecha + [limite],
            )
            for row in c.fetchall():
                partidos.append(dict(row))

    finally:
        conn.close()

    # ========== FILOSOFÍA C: APLICAR OG A LA DEFENSA ==========
    # Regla:
    #   - goles (ataque propio) → NO se toca. Los OG del rival NO cuentan como ataque.
    #   - rival_goles (defensa propia, goles recibidos) → SE SUMA el OG propio.
    # Un equipo que mete un OG recibe ese gol, así que se penaliza su defensa.
    for p in partidos:
        og_propio = p.get("og_propio", 0) or 0
        if og_propio > 0 and p.get("rival_goles") is not None:
            p["rival_goles"] = p["rival_goles"] + og_propio
        # Limpiamos las claves auxiliares para no ensuciar el resto del pipeline
        p.pop("og_propio", None)
        p.pop("og_rival", None)

    # Ordenar TODOS por fecha descendente
    partidos.sort(key=lambda x: x["fecha"] or "0000", reverse=True)

    # Aplicar filtros (antigüedad y competición)
    partidos_filtrados = []
    for p in partidos:
        dias = _calcular_dias_atras(p["fecha"])
        if dias > ANTIGUEDAD_MAXIMA_DIAS:
            continue

        peso_comp = _clasificar_competicion(p.get("liga"), liga_pronostico)
        if peso_comp == 0.0:
            continue

        p["dias_atras"] = dias
        p["peso_competicion"] = peso_comp
        partidos_filtrados.append(p)

    return partidos_filtrados[:limite]


def _calcular_promedios_equipo(equipo, liga_pronostico=None, limite=15):
    """
    Calcula los promedios de un equipo (ataque y defensa).
    Se usa para evaluar la fuerza del rival en cada partido.

    Returns:
        {
            'goles_marcados': float,
            'goles_recibidos': float,
            'partidos': int,
            'fuerza_ataque': float,   # ratio vs promedio liga
            'fuerza_defensa': float,  # ratio vs promedio liga (más bajo = mejor defensa)
        }
    """
    partidos = obtener_partidos_historicos(
        equipo, liga_pronostico=liga_pronostico, limite=limite
    )

    if not partidos:
        return None

    # Calcular promedios directos
    goles_marcados = [p.get("goles") for p in partidos if p.get("goles") is not None]
    goles_recibidos = [
        p.get("rival_goles") for p in partidos if p.get("rival_goles") is not None
    ]

    if not goles_marcados or not goles_recibidos:
        return None

    prom_marcados = sum(goles_marcados) / len(goles_marcados)
    prom_recibidos = sum(goles_recibidos) / len(goles_recibidos)

    # Comparar con promedio de liga
    ligas = [p["liga"] for p in partidos if p.get("liga")]
    liga_principal = max(set(ligas), key=ligas.count) if ligas else liga_pronostico

    prom_liga = 1.4  # fallback
    if liga_principal:
        promedios_liga = calcular_promedios_liga(liga_principal)
        if promedios_liga:
            prom_liga = promedios_liga["goles"]["media"]

    return {
        "goles_marcados": round(prom_marcados, 3),
        "goles_recibidos": round(prom_recibidos, 3),
        "partidos": len(partidos),
        "fuerza_ataque": round(prom_marcados / prom_liga, 3) if prom_liga > 0 else 1.0,
        "fuerza_defensa": (
            round(prom_recibidos / prom_liga, 3) if prom_liga > 0 else 1.0
        ),
    }


def _calcular_ajuste_por_rival(rival, liga_pronostico=None):
    """
    Calcula un multiplicador para ponderar partidos según la fuerza del rival.

    Lógica:
    - Si el rival es fuerte defensivamente (recibe pocos goles):
      → los goles que marcaste contra ellos valen MÁS
    - Si el rival es débil defensivamente (recibe muchos goles):
      → los goles que marcaste contra ellos valen MENOS

    Returns:
        float: ajuste multiplicador entre AJUSTE_RIVAL_MIN y AJUSTE_RIVAL_MAX
    """
    if not PONDERAR_POR_RIVAL:
        return 1.0

    promedios = _calcular_promedios_equipo(
        rival, liga_pronostico=liga_pronostico, limite=10
    )

    if not promedios or promedios["partidos"] < 3:
        return 1.0

    # Invertir fuerza_defensa: defensa fuerte → número bajo → ajuste alto
    # fuerza_defensa = 0.5 → defensa muy fuerte → ajuste = 1/0.5 = 2.0
    # fuerza_defensa = 1.5 → defensa débil → ajuste = 1/1.5 = 0.67
    fuerza_def = promedios["fuerza_defensa"]

    if fuerza_def <= 0:
        return 1.0

    ajuste = 1.0 / fuerza_def

    # Limitar al rango permitido
    ajuste = max(AJUSTE_RIVAL_MIN, min(AJUSTE_RIVAL_MAX, ajuste))

    return round(ajuste, 3)


# ============================================================
# LOCALÍA POR LIGA (FASE 8.5)
# ============================================================

# Cache en memoria para evitar recalcular la misma liga múltiples veces
_CACHE_LOCALIA_LIGA = {}


def calcular_localia_liga(liga, temporada=None, min_partidos=20, fecha_corte=None):
    """
    Calcula el factor de localía empírico de una liga.

    Fórmula:
        factor = goles_promedio_local / goles_promedio_visitante

    Args:
        liga: nombre de la liga
        temporada: opcional, para filtrar
        min_partidos: mínimo de partidos para calcular (default 20)

    Returns:
        {
            'factor': float,          # Factor de localía (>1 = ventaja local)
            'goles_local': float,     # Media goles del local
            'goles_visitante': float, # Media goles del visitante
            'partidos': int,          # Número de partidos analizados
            'fuente': str,            # 'empirico' | 'generico' | 'sin_datos'
        }
    """
    # ========== Cache ==========
    cache_key = f"{liga}|{temporada or 'all'}|{fecha_corte or 'all'}"
    if cache_key in _CACHE_LOCALIA_LIGA:
        return _CACHE_LOCALIA_LIGA[cache_key]

    # ========== Fallback genérico ==========
    fallback = {
        "factor": FACTOR_LOCALIA_GENERICO_LOCAL,  # 1.15 por defecto
        "goles_local": None,
        "goles_visitante": None,
        "partidos": 0,
        "fuente": "generico",
    }

    if not liga:
        _CACHE_LOCALIA_LIGA[cache_key] = fallback
        return fallback

    # ========== Consulta a BD ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Filtrar por liga y temporada (si aplica)
        condiciones = ["liga = ?"]
        params = [liga]

        if temporada:
            condiciones.append("temporada = ?")
            params.append(temporada)

        if fecha_corte:
            condiciones.append("fecha < ?")
            params.append(fecha_corte)

        filtro = "WHERE " + " AND ".join(condiciones)
        params = tuple(params)

        # Contar partidos
        c.execute(f"SELECT COUNT(*) FROM partidos {filtro}", params)
        total_partidos = c.fetchone()[0] or 0

        if total_partidos < min_partidos:
            fallback["partidos"] = total_partidos
            fallback["fuente"] = "sin_datos"
            _CACHE_LOCALIA_LIGA[cache_key] = fallback
            return fallback

        # Sumar goles del local
        c.execute(
            f"""
            SELECT SUM(sub.total)
            FROM (
                SELECT (SELECT SUM(G) FROM estadisticas_local WHERE partido_id = p.id) as total
                FROM partidos p {filtro}
            ) sub
        """,
            params,
        )
        goles_local_total = c.fetchone()[0] or 0

        # Sumar goles del visitante
        c.execute(
            f"""
            SELECT SUM(sub.total)
            FROM (
                SELECT (SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = p.id) as total
                FROM partidos p {filtro}
            ) sub
        """,
            params,
        )
        goles_visit_total = c.fetchone()[0] or 0

        if goles_visit_total <= 0 or goles_local_total <= 0:
            fallback["partidos"] = total_partidos
            fallback["fuente"] = "sin_datos"
            _CACHE_LOCALIA_LIGA[cache_key] = fallback
            return fallback

        # Promedios
        prom_local = goles_local_total / total_partidos
        prom_visit = goles_visit_total / total_partidos

        # Factor
        factor = prom_local / prom_visit if prom_visit > 0 else 1.15

        # Cap
        factor = max(0.90, min(1.40, factor))

        resultado = {
            "factor": round(factor, 4),
            "goles_local": round(prom_local, 3),
            "goles_visitante": round(prom_visit, 3),
            "partidos": total_partidos,
            "fuente": "empirico",
        }

        _CACHE_LOCALIA_LIGA[cache_key] = resultado
        return resultado

    finally:
        conn.close()


def _calcular_factor_localia(equipo, como_local, liga_pronostico=None, fecha_corte=None,usar_generica=True, usar_empirica=True, usar_liga=True):
    """
    Calcula el factor de localía combinando:
    1. Empírico del equipo (sus propios partidos como local/visitante)
    2. Empírico de la liga (si hay suficientes partidos)
    3. Genérico (fallback)

    Prioridad:
    - Si el equipo tiene >= 5 partidos en la condición → mezcla 60% equipo + 40% liga
    - Si el equipo tiene < 5 partidos → mezcla 30% equipo + 70% liga
    - Si la liga no tiene datos → solo equipo + genérico

    Returns:
        float: factor de localía
    """
    # ========== 1. Factor genérico ==========
    factor_generico = (
        FACTOR_LOCALIA_GENERICO_LOCAL
        if como_local
        else FACTOR_LOCALIA_GENERICO_VISITANTE
    ) if usar_generica else 1.0

    # ========== 2. Factor de liga ==========
    if usar_liga and liga_pronostico:
        liga_info = calcular_localia_liga(liga_pronostico)
    else:
        liga_info = {"factor": 1.0, "fuente": "desactivado", "partidos": 0}
    
    # ... resto de la función, respetando `usar_empirica` cuando toque

    # El factor de liga mide ventaja local. Para el visitante, aplicamos el inverso.
    if como_local:
        factor_liga = liga_info["factor"]
    else:
        # Si la localía es 1.20 (local marca 20% más), el visitante marca ~17% menos
        # Inversa: 1 / 1.20 = 0.833. Pero queremos un factor cercano a 0.90.
        # Usamos una aproximación más suave: 2 - factor_liga (2 - 1.20 = 0.80)
        # Ajustamos: 1 / factor_liga (1 / 1.20 = 0.833), luego suavizamos con genérico.
        factor_liga = (
            1.0 / liga_info["factor"]
            if liga_info["factor"] > 0
            else FACTOR_LOCALIA_GENERICO_VISITANTE
        )
        # Suavizar con genérico 0.90 para no ser demasiado agresivo
        factor_liga = (factor_liga + FACTOR_LOCALIA_GENERICO_VISITANTE) / 2

    # ========== 3. Factor empírico del equipo ==========
    partidos_condicion = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    partidos_general = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    n_condicion = len(partidos_condicion)

    # Si no hay suficientes datos, usar el factor de liga directamente
    if n_condicion < MIN_PARTIDOS_LOCALIA or not partidos_general:
        # Si la liga tiene datos, usar 70% liga + 30% genérico
        if liga_info["fuente"] == "empirico":
            factor_final = (factor_liga * 0.7) + (factor_generico * 0.3)
        else:
            factor_final = factor_generico
        return round(max(0.70, min(1.40, factor_final)), 3)

    # Calcular factor empírico del equipo
    stats_condicion = calcular_estadisticas_ponderadas(
        partidos_condicion, liga_pronostico
    )
    stats_general = calcular_estadisticas_ponderadas(partidos_general, liga_pronostico)

    if not stats_condicion or not stats_general:
        return round(
            factor_liga if liga_info["fuente"] == "empirico" else factor_generico, 3
        )

    prom_condicion = stats_condicion.get("goles")
    prom_general = stats_general.get("goles")

    if prom_condicion is None or prom_general is None or prom_general <= 0:
        return round(
            factor_liga if liga_info["fuente"] == "empirico" else factor_generico, 3
        )

    factor_empirico = prom_condicion / prom_general

    # Suavizar con el genérico
    n = n_condicion
    k = FACTOR_SUAVIZADO
    factor_empirico_suav = (n * factor_empirico + k * factor_generico) / (n + k)

    # ========== 4. Combinar equipo + liga ==========
    # Pesos: 60% equipo si tiene >= 5 partidos, 30% si tiene menos
    peso_equipo = 0.6 if n_condicion >= 5 else 0.3
    peso_liga = 1.0 - peso_equipo

    if liga_info["fuente"] == "empirico":
        factor_final = (factor_empirico_suav * peso_equipo) + (factor_liga * peso_liga)
    else:
        # Sin datos de liga → solo equipo + genérico
        factor_final = factor_empirico_suav

    # Limitar a rango razonable
    factor_final = max(0.70, min(1.40, factor_final))

    return round(factor_final, 3)


# ============================================================
# ESTADÍSTICAS PONDERADAS
# ============================================================
def calcular_estadisticas_ponderadas(partidos, liga_pronostico=None):
    """
    Calcula estadísticas ponderadas por recencia Y fuerza del rival.

    IMPORTANTE:
    - Ignora valores NULL (no los convierte en 0)
    - Pondera cada partido por su peso (recencia × competición × fuerza del rival)
    - Devuelve también la cobertura de datos por campo
    """
    if not partidos:
        return None

    # Campos a calcular
    campos = [
        "goles",
        "tiros",
        "tiros_puerta",
        "corners",
        "faltas",
        "faltas_recibidas",
        "paradas",
        "tarjetas_amarillas",
        "tarjetas_rojas",
        "pases",
        "centros",
        "entradas",
        "fueras_juego",
        "tiros_bloqueados",
        # ✅ RIVAL (para calcular ataque/defensa)
        "rival_goles",
        "rival_tiros",
        "rival_tiros_puerta",
        "rival_corners",
        "rival_faltas",
        "rival_faltas_recibidas",
        "rival_paradas",
        "rival_tarjetas_amarillas",
        "rival_tarjetas_rojas",
        "rival_pases",
        "rival_centros",
        "rival_entradas",
        "rival_fueras_juego",
        "rival_tiros_bloqueados",
    ]

    # Calcular peso de cada partido (incluyendo fuerza del rival)
    suma_pesos_total = 0
    pesos_por_partido = []

    # Cache de ajustes por rival (evita recalcular)
    cache_rival = {}

    for i, p in enumerate(partidos):
        # Peso por posición (más reciente = más peso)
        peso_pos = FACTOR_DECAY**i if modificador_activo('decay') else 1.0

        # Peso por competición
        peso_comp = p.get("peso_competicion", 1.0) if modificador_activo('peso_competicion') else 1.0

        # Peso por fuerza del rival
        rival = p.get("rival")
        if rival and modificador_activo('peso_rival'):
            if rival not in cache_rival:
                cache_rival[rival] = _calcular_ajuste_por_rival(rival, liga_pronostico)
            peso_rival = cache_rival[rival]
        else:
            peso_rival = 1.0

        # Peso final
        peso = peso_pos * peso_comp * peso_rival
        pesos_por_partido.append(peso)
        suma_pesos_total += peso

    if suma_pesos_total == 0:
        return None

    # ===== Calcular promedios IGNORANDO NULL =====
    resultado = {}
    cobertura = {}

    for campo in campos:
        suma_ponderada = 0
        suma_pesos_validos = 0

        for i, p in enumerate(partidos):
            valor = p.get(campo)

            if valor is None:
                continue

            peso = pesos_por_partido[i]
            suma_ponderada += valor * peso
            suma_pesos_validos += peso

        if suma_pesos_validos > 0:
            resultado[campo] = round(suma_ponderada / suma_pesos_validos, 3)
        else:
            resultado[campo] = None

        # Cobertura
        valores_presentes = sum(1 for p in partidos if p.get(campo) is not None)
        cobertura[campo] = {
            "presentes": valores_presentes,
            "total": len(partidos),
            "porcentaje": round(valores_presentes / len(partidos) * 100, 1),
        }

    resultado["partidos"] = len(partidos)
    resultado["suma_pesos"] = round(suma_pesos_total, 3)
    resultado["cobertura"] = cobertura
    resultado["pesos_individuales"] = [round(p, 3) for p in pesos_por_partido]

    return resultado


# ============================================================
# DETECCIÓN DE TENDENCIAS
# ============================================================
def detectar_tendencia(partidos, campo="goles"):
    """
    Detecta si un equipo está subiendo, bajando o estable.
    Ignora NULL en el cálculo.
    """
    if len(partidos) < 6:
        return {
            "direccion": "sin_datos",
            "factor": 1.0,
            "descripcion": "Sin datos suficientes",
            "prom_reciente": None,
            "prom_anterior": None,
            "cambio_pct": 0,
            "cobertura_reciente": 0,
            "cobertura_anterior": 0,
        }

    ultimos_5 = partidos[:5]
    anteriores_5 = partidos[5:10] if len(partidos) >= 10 else partidos[5:]

    # Filtrar solo valores válidos
    def extraer_validos(lista):
        return [p.get(campo) for p in lista if p.get(campo) is not None]

    valores_recientes = extraer_validos(ultimos_5)
    valores_anteriores = extraer_validos(anteriores_5)

    # Si no hay suficientes datos en alguna ventana
    if len(valores_recientes) < 2 or len(valores_anteriores) < 2:
        return {
            "direccion": "sin_datos",
            "factor": 1.0,
            "descripcion": "Datos insuficientes para comparar",
            "prom_reciente": None,
            "prom_anterior": None,
            "cambio_pct": 0,
            "cobertura_reciente": len(valores_recientes),
            "cobertura_anterior": len(valores_anteriores),
        }

    prom_reciente = sum(valores_recientes) / len(valores_recientes)
    prom_anterior = sum(valores_anteriores) / len(valores_anteriores)

    if prom_anterior == 0:
        return {
            "direccion": "sin_datos",
            "factor": 1.0,
            "descripcion": "Sin base de comparación",
            "prom_reciente": round(prom_reciente, 2),
            "prom_anterior": 0,
            "cambio_pct": 0,
            "cobertura_reciente": len(valores_recientes),
            "cobertura_anterior": len(valores_anteriores),
        }

    cambio = (prom_reciente - prom_anterior) / prom_anterior

    # Requerir cobertura razonable (mínimo 3 de 5)
    cobertura_ok = len(valores_recientes) >= 3 and len(valores_anteriores) >= 3

    if not cobertura_ok:
        return {
            "direccion": "sin_datos",
            "factor": 1.0,
            "descripcion": f"Cobertura insuficiente ({len(valores_recientes)}/{len(valores_anteriores)})",
            "prom_reciente": round(prom_reciente, 2),
            "prom_anterior": round(prom_anterior, 2),
            "cambio_pct": round(cambio * 100, 1),
            "cobertura_reciente": len(valores_recientes),
            "cobertura_anterior": len(valores_anteriores),
        }

    if cambio > 0.15:
        direccion = "subiendo"
        descripcion = f"📈 Subiendo ({cambio*100:+.1f}%)"
        factor = 1 + min(cambio, 0.20)
    elif cambio < -0.15:
        direccion = "bajando"
        descripcion = f"📉 Bajando ({cambio*100:+.1f}%)"
        factor = 1 + max(cambio, -0.20)
    else:
        direccion = "estable"
        descripcion = f"➡️ Estable ({cambio*100:+.1f}%)"
        factor = 1.0

    return {
        "direccion": direccion,
        "factor": round(factor, 3),
        "descripcion": descripcion,
        "prom_reciente": round(prom_reciente, 2),
        "prom_anterior": round(prom_anterior, 2),
        "cambio_pct": round(cambio * 100, 1),
        "cobertura_reciente": len(valores_recientes),
        "cobertura_anterior": len(valores_anteriores),
    }


# ============================================================
# JUGADORES ACTIVOS
# ============================================================
def obtener_jugadores_activos(equipo, como_local=None, ultimos_n=5):
    """
    Devuelve un dict {jugador: factor_actividad}.

    factor_actividad:
        1.0  → aparece en últimos ultimos_n partidos
        0.5  → aparece en partidos 6-10
        0.1  → no aparece hace mucho (probablemente se fue)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Obtener los últimos partidos (IDs)
        if como_local is True or como_local is None:
            c.execute(
                """
                SELECT p.id FROM partidos p
                WHERE p.local = ?
                ORDER BY p.fecha DESC LIMIT 10
            """,
                (equipo,),
            )
            ids_local = [r[0] for r in c.fetchall()]
        else:
            ids_local = []

        if como_local is False or como_local is None:
            c.execute(
                """
                SELECT p.id FROM partidos p
                WHERE p.visitante = ?
                ORDER BY p.fecha DESC LIMIT 10
            """,
                (equipo,),
            )
            ids_visit = [r[0] for r in c.fetchall()]
        else:
            ids_visit = []

        todos_ids = ids_local + ids_visit
        if not todos_ids:
            return {}

        # Obtener jugadores que aparecen en los últimos N partidos
        placeholders = ",".join("?" * len(todos_ids))
        jugadores_activos = defaultdict(int)

        # Del lado local
        if ids_local:
            ph = ",".join("?" * len(ids_local))
            c.execute(
                f"""
                SELECT jugador, COUNT(DISTINCT partido_id) as apariciones
                FROM estadisticas_local
                WHERE partido_id IN ({ph})
                GROUP BY jugador
            """,
                ids_local,
            )
            for jugador, apariciones in c.fetchall():
                jugadores_activos[jugador] += apariciones

        # Del lado visitante
        if ids_visit:
            ph = ",".join("?" * len(ids_visit))
            c.execute(
                f"""
                SELECT jugador, COUNT(DISTINCT partido_id) as apariciones
                FROM estadisticas_visitante
                WHERE partido_id IN ({ph})
                GROUP BY jugador
            """,
                ids_visit,
            )
            for jugador, apariciones in c.fetchall():
                jugadores_activos[jugador] += apariciones

        # Calcular factor de actividad
        resultado = {}
        for jugador, apariciones in jugadores_activos.items():
            if apariciones >= ultimos_n:
                resultado[jugador] = 1.0
            elif apariciones >= 2:
                resultado[jugador] = 0.5
            else:
                resultado[jugador] = 0.1

        return resultado

    finally:
        conn.close()


# ============================================================
# CÁLCULO DE LAMBDA (Poisson)
# ============================================================
def calcular_lambda_poisson(equipo, rival, como_local, liga_pronostico=None, fecha_corte=None):
    """
    Calcula λ (goles esperados) usando ATAQUE vs DEFENSA real
    CON suavizado (shrinkage) y ponderación por fuerza del rival.
    ...
    """
    # ========== BLINDAJE: variables por defecto ==========
    prom_liga_fuente = 'fallback'
    prom_liga_partidos = 0
    factor_fuente = 1.00
    ataque_fuente = 'fallback_sin_datos'
    defensa_fuente = 'fallback_sin_datos'
    
    # ========== 0. Calcular ventanas múltiples ==========
    
    ventanas_info = calcular_stats_multiples_ventanas(
        equipo, liga_pronostico, como_local, fecha_corte=fecha_corte
    )

    # ========== 1. Partidos del equipo y rival ==========
    partidos_equipo = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    if len(partidos_equipo) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {equipo} ({len(partidos_equipo)} partidos)",
            "lambda": None,
            "partidos": len(partidos_equipo),
        }

    partidos_rival = obtener_partidos_historicos(
        rival, como_local=None, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    if len(partidos_rival) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {rival} ({len(partidos_rival)} partidos)",
            "lambda": None,
            "partidos": len(partidos_equipo),
        }

    # ========== 2. Estadísticas ponderadas ==========
    stats_equipo = calcular_estadisticas_ponderadas(partidos_equipo, liga_pronostico)
    stats_rival = calcular_estadisticas_ponderadas(partidos_rival, liga_pronostico)

    if not stats_equipo or not stats_rival:
        return {"error": "Error calculando estadísticas", "lambda": None}

    # ========== 3. Promedios de liga ==========
    ligas = [p["liga"] for p in partidos_equipo if p.get("liga")]
    liga_principal = max(set(ligas), key=ligas.count) if ligas else liga_pronostico

    promedios_liga = None
    if liga_principal:
        promedios_liga = calcular_promedios_liga(liga_principal)

    # ⚠️ BUG FIX (BLOQUE 1): distinguir observado vs estimado vs fallback
    FALLBACK_GOLES_LIGA = 1.4
    UMBRAL_OBSERVADO = 20  # mínimo de partidos para considerar "observado"

    if not promedios_liga:
        prom_goles_liga = FALLBACK_GOLES_LIGA
        prom_liga_fuente = 'fallback'
        prom_liga_partidos = 0
    else:
        prom_goles_liga = promedios_liga["goles"]["media"]
        prom_liga_partidos = promedios_liga.get("partidos", 0)
        if prom_liga_partidos >= UMBRAL_OBSERVADO:
            prom_liga_fuente = 'observado'
        else:
            prom_liga_fuente = 'estimado'
            
    # ========== 4. Ataque propio (con suavizado) ==========
    goles_propios = stats_equipo.get("goles")
    if goles_propios is None:
        goles_propios = prom_goles_liga
        ataque_fuente = 'fallback_sin_datos'
    else:
        ataque_fuente = 'observado'
    # Ajustar por condición (local/visitante)
    partidos_condicion = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=10,
        fecha_corte=fecha_corte
    )

    if len(partidos_condicion) >= 3:
        stats_condicion = calcular_estadisticas_ponderadas(
            partidos_condicion, liga_pronostico
        )
        if stats_condicion and stats_condicion.get("goles") is not None:
            goles_condicion = stats_condicion["goles"]
            # Mezcla: 60% condicional + 40% general
            goles_propios = 0.6 * goles_condicion + 0.4 * goles_propios

    # ========== Ajuste por racha ==========
    if modificador_activo('racha'):
        racha_equipo = detectar_racha(equipo, liga_pronostico, fecha_corte=fecha_corte)
        factor_racha = racha_equipo["factor"]
    else:
        racha_equipo = {'tipo': 'desactivado', 'longitud': 0, 'factor': 1.0, 'descripcion': ''}
        factor_racha = 1.0

    ataque_crudo = goles_propios * factor_racha

    # ✅ SUAVIZADO (shrinkage) del ataque
    n_partidos = len(partidos_equipo)
    if modificador_activo('suavizado'):
        ataque_suavizado = (
            n_partidos * ataque_crudo + FACTOR_SUAVIZADO * prom_goles_liga
        ) / (n_partidos + FACTOR_SUAVIZADO)
    else:
        # Sin suavizado: usar el crudo tal cual
        ataque_suavizado = ataque_crudo

    # ========== 5. Defensa del rival (con suavizado) ==========
    goles_permitidos_rival = stats_rival.get("rival_goles")

    # ⚠️ BUG FIX (BLOQUE 1): distinguir None (sin dato) de 0 (dato real)
    if goles_permitidos_rival is None:
        # Sin datos: usar promedio de liga como fallback
        defensa_cruda = prom_goles_liga
        defensa_fuente = 'fallback_sin_datos'
    else:
        # Sí hay dato (incluido 0): usarlo tal cual
        # Si es 0, aplicar mínimo MUY bajo para evitar divisiones por 0
        # pero respetando que la defensa es excelente
        defensa_cruda = max(0.1, goles_permitidos_rival)
        defensa_fuente = 'observado' if goles_permitidos_rival > 0 else 'observado_cero'

    # ✅ SUAVIZADO de la defensa
    n_partidos_rival = len(partidos_rival)
    if modificador_activo('suavizado'):
        defensa_suavizada = (
            n_partidos_rival * defensa_cruda + FACTOR_SUAVIZADO * prom_goles_liga
        ) / (n_partidos_rival + FACTOR_SUAVIZADO)
    else:
        defensa_suavizada = defensa_cruda

    # ========== 6. Tendencia ==========
    tendencia = detectar_tendencia(partidos_equipo, campo="goles")
    factor_tendencia = tendencia.get("factor", 1.0) if modificador_activo('tendencia') else 1.0

    # ========== 7. Factor de localía ==========
    # Solo calcular si algún modificador de localía está activo
    # ========== 7. Factor de localía ==========
    # Si CUALQUIERA de los 3 está activo, calcular localía
    # pero respetar los que estén desactivados individualmente
    factor_localia = _calcular_factor_localia(
        equipo, como_local, liga_pronostico,
        usar_generica=modificador_activo('localia_generica'),
        usar_empirica=modificador_activo('localia_empirica'),
        usar_liga=modificador_activo('localia_liga'),
    )
    
    localia_liga_info = (
        calcular_localia_liga(liga_pronostico)
        if liga_pronostico and modificador_activo('localia_liga')
        else {"factor": None, "fuente": "sin_datos", "partidos": 0}
    )

    # ========== 8. Fórmula Poisson con suavizado ==========
    if prom_goles_liga <= 0:
        prom_goles_liga = 1.4

    # ========== FEATURES AVANZADAS (FASE 8.6) ==========
    if modificador_activo('ratio'):
        factor_ratio, ratio_valor = _calcular_factor_ratio(stats_equipo, stats_rival)
    else:
        factor_ratio, ratio_valor = 1.0, None
    
    if modificador_activo('diferencial'):
        factor_diferencial, dif_valor = _calcular_factor_diferencial(stats_equipo)
    else:
        factor_diferencial, dif_valor = 1.0, None
    
    if modificador_activo('racha_v2'):
        factor_racha_v2, racha_v2_tipo = _calcular_factor_racha_v2(
            equipo, liga_pronostico, como_local, fecha_corte=fecha_corte
        )
    else:
        factor_racha_v2, racha_v2_tipo = 1.0, 'desactivado'
        
    if prom_liga_fuente == 'fallback':
        factor_fuente = 0.90
    elif prom_liga_fuente == 'estimado':
        factor_fuente = 0.95
    # else: factor_fuente = 1.00 (ya inicializado)

    lam = (ataque_suavizado * defensa_suavizada) / prom_goles_liga
    lam = lam * factor_localia * factor_tendencia
    lam = lam * factor_ratio * factor_diferencial * factor_racha_v2
    lam = lam * factor_fuente
    # ========== APRENDIZAJE: corrección de sesgo por equipo ==========
    if modificador_activo('aprendizaje_sesgo'):
        from database.aprendizaje import aplicar_correccion_lambda
        lam = aplicar_correccion_lambda(lam, equipo, como_local, fecha_corte=fecha_corte)

    # Limitar a rango razonable
    lam = max(0.2, min(5.0, lam))

    # ========== 9. Cobertura ==========
    campos_clave = ["goles", "tiros", "tiros_puerta", "corners"]
    cobertura = stats_equipo.get("cobertura", {})

    cobertura_promedio = 0
    if cobertura:
        porcentajes = [cobertura.get(c, {}).get("porcentaje", 0) for c in campos_clave]
        cobertura_promedio = sum(porcentajes) / len(porcentajes) if porcentajes else 0

    # ========== 10. Features de contexto (FE-2) ==========
    contexto_features = calcular_contexto_features(partidos_equipo, stats_equipo)

    return {
        "lambda": round(lam, 3),
        "contexto": contexto_features,
        "promedio_liga_fuente": prom_liga_fuente,       # ← NUEVO
        "promedio_liga_partidos": prom_liga_partidos,   # ← NUEVO
        "factor_fuente": factor_fuente,                 # ← NUEVO
        # Valores crudos
        "ataque_crudo": round(ataque_crudo, 3),
        "defensa_cruda": round(defensa_cruda, 3),
        "ataque_fuente": ataque_fuente,  # ← NUEVO
        "defensa_fuente": defensa_fuente,  # ← NUEVO: trazabilidad        
        # Valores suavizados
        "ataque_suavizado": round(ataque_suavizado, 3),
        "defensa_suavizada": round(defensa_suavizada, 3),
        "ataque_equipo": round(ataque_suavizado, 3),  # retrocompatibilidad
        "defensa_rival": round(defensa_suavizada, 3),  # retrocompatibilidad
        # Contexto
        "promedio_liga": round(prom_goles_liga, 3),
        "factor_localia": factor_localia,
        "factor_localia_generico": (
            FACTOR_LOCALIA_GENERICO_LOCAL
            if como_local
            else FACTOR_LOCALIA_GENERICO_VISITANTE
        ),
        "factor_localia_empirico": True,
        "factor_tendencia": factor_tendencia,
        "factor_suavizado_k": FACTOR_SUAVIZADO,
        "factor_racha": factor_racha,
        # ========== NUEVAS FEATURES (FE-1) ==========
        "factor_ratio": factor_ratio,
        "ratio_valor": ratio_valor,
        "factor_diferencial": factor_diferencial,
        "diferencial_valor": dif_valor,
        "factor_racha_v2": factor_racha_v2,
        "racha_v2_tipo": racha_v2_tipo,
        "factor_localia": factor_localia,
        # ========== NUEVO: localía de liga (FASE 8.5) ==========
        "localia_liga": localia_liga_info,
        # ========== ==========
        "factor_localia_generico": (
            FACTOR_LOCALIA_GENERICO_LOCAL
            if como_local
            else FACTOR_LOCALIA_GENERICO_VISITANTE
        ),
        "racha_info": racha_equipo,
        "ventanas_info": ventanas_info,
        "tendencia": tendencia,
        "partidos": len(partidos_equipo),
        "partidos_rival": len(partidos_rival),
        "stats_equipo": stats_equipo,
        "stats_rival": stats_rival,
        "cobertura_promedio": round(cobertura_promedio, 1),
        "error": None,
    }


# ============================================================
# BINOMIAL NEGATIVA (FASE 8.4)
# ============================================================
def negbin_pmf(k, mu, alpha):
    """
    PMF de la distribución Binomial Negativa (parametrización por media y dispersión).

    Fórmula:
        P(X=k) = Γ(k + 1/α) / (k! · Γ(1/α)) · (1/(1+α·μ))^(1/α) · (α·μ/(1+α·μ))^k

    Args:
        k: número de eventos (goles)
        mu: media esperada (λ)
        alpha: parámetro de dispersión
               - alpha → 0: NegBin ≈ Poisson
               - alpha > 0: overdispersion (varianza > media)

    Returns:
        Probabilidad de exactamente k eventos.

    Nota: usamos una aproximación numérica estable para evitar overflow
    con factoriales grandes y gammas.
    """
    import math

    if k < 0:
        return 0.0
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    if alpha <= 0:
        # Fallback a Poisson
        return poisson_pmf(k, mu)

    # Aproximación estable: usamos lgamma para evitar overflow
    try:
        # Γ(k + 1/α) / Γ(1/α)
        log_gamma_ratio = math.lgamma(k + 1.0 / alpha) - math.lgamma(1.0 / alpha)
        # log(k!)
        log_k_fact = math.lgamma(k + 1)
        # log(1/(1+α·μ)) · 1/α
        log_prob_1 = (1.0 / alpha) * math.log(1.0 / (1.0 + alpha * mu))
        # log(α·μ/(1+α·μ)) · k
        log_prob_2 = k * math.log(alpha * mu / (1.0 + alpha * mu))

        log_p = log_gamma_ratio - log_k_fact + log_prob_1 + log_prob_2

        return math.exp(log_p)
    except (ValueError, OverflowError):
        # Si falla, fallback a Poisson
        return poisson_pmf(k, mu)


def estimar_alpha(media, varianza):
    """
    Estima el parámetro de dispersión α de la NegBin.

    Fórmula:
        Var(X) = μ + α·μ²
        α = (Var - μ) / μ²

    Args:
        media: media de la muestra
        varianza: varianza de la muestra

    Returns:
        alpha (≥ 0). Si varianza <= media, devuelve 0 (usa Poisson).
    """
    if media is None or varianza is None or media <= 0:
        return 0.0

    if varianza <= media:
        # Sin overdispersion → Poisson
        return 0.0

    alpha = (varianza - media) / (media**2)

    # Limitar alpha a un rango razonable (evita valores absurdos con pocos datos)
    return max(0.0, min(alpha, 1.0))


def decidir_modelo(partidos_equipo, partidos_rival, umbral_dispersion=0.20):
    """
    Decide si usar Poisson o NegBin según la dispersión de los datos.

    Lógica:
    - Calcular la varianza de los goles en los partidos.
    - Si varianza > media × (1 + umbral_dispersion) → NegBin.
    - Si no → Poisson.

    Args:
        partidos_equipo: lista de partidos del equipo
        partidos_rival: lista de partidos del rival
        umbral_dispersion: mínimo de overdispersion para usar NegBin (default 20%)

    Returns:
        {
            'modelo': 'poisson' | 'negbin',
            'alpha_local': float,
            'alpha_visitante': float,
            'dispersion_local': float,
            'dispersion_visitante': float,
            'razon': str,
        }
    """
    import statistics

    def _analizar_dispersion(partidos):
        goles = [p.get("goles") for p in partidos if p.get("goles") is not None]
        if len(goles) < 5:
            return None, None

        media = statistics.mean(goles)
        if len(goles) < 2:
            return media, 0.0

        varianza = statistics.variance(goles)

        if media <= 0:
            return media, 0.0

        # Overdispersion: varianza / media
        dispersion = varianza / media

        return media, dispersion

    media_local, disp_local = _analizar_dispersion(partidos_equipo)
    media_rival, disp_rival = _analizar_dispersion(partidos_rival)

    # Si no hay datos suficientes → Poisson
    if media_local is None or media_rival is None:
        return {
            "modelo": "poisson",
            "alpha_local": 0.0,
            "alpha_visitante": 0.0,
            "dispersion_local": None,
            "dispersion_visitante": None,
            "razon": "Datos insuficientes para estimar dispersión",
        }

    # Calcular alpha por equipo
    goles_local = [
        p.get("goles") for p in partidos_equipo if p.get("goles") is not None
    ]
    goles_rival = [p.get("goles") for p in partidos_rival if p.get("goles") is not None]

    var_local = (
        statistics.variance(goles_local) if len(goles_local) >= 2 else media_local
    )
    var_rival = (
        statistics.variance(goles_rival) if len(goles_rival) >= 2 else media_rival
    )

    alpha_local = estimar_alpha(media_local, var_local)
    alpha_rival = estimar_alpha(media_rival, var_rival)

    # Decisión global
    umbral = 1.0 + umbral_dispersion
    usa_negbin_local = disp_local is not None and disp_local > umbral
    usa_negbin_rival = disp_rival is not None and disp_rival > umbral

    if usa_negbin_local or usa_negbin_rival:
        modelo = "negbin"
        razon = f"Overdispersion detectada (local: {disp_local:.2f}x, rival: {disp_rival:.2f}x)"
    else:
        modelo = "poisson"
        razon = f"Sin overdispersion significativa (local: {disp_local:.2f}x, rival: {disp_rival:.2f}x)"

    return {
        "modelo": modelo,
        "alpha_local": round(alpha_local, 4),
        "alpha_visitante": round(alpha_rival, 4),
        "dispersion_local": round(disp_local, 3) if disp_local is not None else None,
        "dispersion_visitante": (
            round(disp_rival, 3) if disp_rival is not None else None
        ),
        "razon": razon,
    }

# ============================================================
# DIXON-COLES (FASE 8.3)
# ============================================================

# Cache de rho por liga
_CACHE_RHO_LIGA = {}

# Valor de rho por defecto (típico empírico)
RHO_DEFAULT = -0.10


def estimar_rho_dixon_coles(liga=None, temporada=None, min_partidos=30, fecha_corte=None):
    """
    Estima el parámetro ρ de Dixon-Coles empíricamente del histórico.
    
    Método: máxima verosimilitud aproximada mediante grid search sobre
    el rango [-0.20, 0.00]. Busca el ρ que mejor explica los resultados
    de la liga.
    
    Args:
        liga: nombre de la liga (opcional)
        temporada: temporada (opcional)
        min_partidos: mínimo de partidos para estimar (default 30)
    
    Returns:
        {
            'rho': float,
            'partidos': int,
            'fuente': 'empirico' | 'default' | 'sin_datos',
            'log_likelihood': float or None,
        }
    """
    cache_key = f"{liga or 'all'}|{temporada or 'all'}|{fecha_corte or 'all'}"
    if cache_key in _CACHE_RHO_LIGA:
        return _CACHE_RHO_LIGA[cache_key]
    
    fallback = {
        'rho': RHO_DEFAULT,
        'partidos': 0,
        'fuente': 'default',
        'log_likelihood': None,
    }
    
    # ========== Consulta a BD ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Construir filtro dinámico
        condiciones = []
        params = []

        if liga:
            condiciones.append("p.liga = ?")
            params.append(liga)
        if temporada:
            condiciones.append("p.temporada = ?")
            params.append(temporada)
        if fecha_corte:
            condiciones.append("p.fecha < ?")
            params.append(fecha_corte)

        filtro = "WHERE " + " AND ".join(condiciones) if condiciones else ""
        params = tuple(params)
        
        c.execute(f"""
            SELECT 
                p.id,
                (SELECT SUM(G) FROM estadisticas_local WHERE partido_id = p.id) as goles_local,
                (SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = p.id) as goles_visitante
            FROM partidos p
            {filtro}
        """, params)
        
        rows = c.fetchall()
    finally:
        conn.close()
    
    # Filtrar partidos válidos
    partidos = []
    for row in rows:
        gl = row[1] if row[1] is not None else 0
        gv = row[2] if row[2] is not None else 0
        partidos.append((gl, gv))
    
    if len(partidos) < min_partidos:
        fallback['partidos'] = len(partidos)
        fallback['fuente'] = 'sin_datos'
        _CACHE_RHO_LIGA[cache_key] = fallback
        return fallback
    
    # ========== Calcular lambdas medias ==========
    total_gl = sum(p[0] for p in partidos)
    total_gv = sum(p[1] for p in partidos)
    n = len(partidos)
    
    lambda_avg = total_gl / n
    mu_avg = total_gv / n
    
    # ========== Grid search sobre rho ==========
    # Rango [-0.25, 0.00], paso 0.01
    mejor_rho = RHO_DEFAULT
    mejor_ll = float('-inf')
    
    for rho_candidate in [x / 100.0 for x in range(-25, 1, 1)]:
        ll = _log_likelihood_dixon_coles(partidos, lambda_avg, mu_avg, rho_candidate)
        if ll > mejor_ll:
            mejor_ll = ll
            mejor_rho = rho_candidate
    
    resultado = {
        'rho': round(mejor_rho, 4),
        'partidos': len(partidos),
        'fuente': 'empirico',
        'log_likelihood': round(mejor_ll, 2),
    }
    
    _CACHE_RHO_LIGA[cache_key] = resultado
    return resultado


def _log_likelihood_dixon_coles(partidos, lambda_local, lambda_visitante, rho):
    """
    Calcula la log-verosimilitud de un conjunto de partidos dado un rho.
    Usa Poisson + factor Dixon-Coles.
    """
    import math
    
    ll = 0.0
    for gl, gv in partidos:
        # Probabilidad Poisson base
        p_base = poisson_pmf(gl, lambda_local) * poisson_pmf(gv, lambda_visitante)
        
        if p_base <= 0:
            continue
        
        # Factor Dixon-Coles
        tau = _factor_tau(gl, gv, lambda_local, lambda_visitante, rho)
        
        if tau <= 0:
            # Factor inválido → penalizar
            ll -= 10
            continue
        
        ll += math.log(p_base * tau)
    
    return ll


def _factor_tau(x, y, lambda_local, lambda_visitante, rho):
    """
    Factor τ de Dixon-Coles para ajustar la matriz de marcadores.
    
    Solo se aplica a las celdas (0,0), (0,1), (1,0), (1,1).
    Para el resto, τ = 1.
    """
    if x == 0 and y == 0:
        return 1 - lambda_local * lambda_visitante * rho
    elif x == 0 and y == 1:
        return 1 + lambda_local * rho
    elif x == 1 and y == 0:
        return 1 + lambda_visitante * rho
    elif x == 1 and y == 1:
        return 1 - rho
    else:
        return 1.0
    
def aplicar_dixon_coles(matriz, lambda_local, lambda_visitante, rho):
    """
    Aplica el factor Dixon-Coles a la matriz de marcadores y renormaliza.
    
    Args:
        matriz: dict {(i, j): prob}
        lambda_local, lambda_visitante: lambdas
        rho: parámetro Dixon-Coles
    
    Returns:
        Nueva matriz ajustada y renormalizada.
    """
    if rho == 0:
        return matriz
    
    matriz_ajustada = {}
    suma_original = sum(matriz.values())
    
    for (i, j), p in matriz.items():
        tau = _factor_tau(i, j, lambda_local, lambda_visitante, rho)
        matriz_ajustada[(i, j)] = p * tau
    
    # Renormalizar
    suma_nueva = sum(matriz_ajustada.values())
    if suma_nueva <= 0:
        return matriz  # fallback
    
    for k in matriz_ajustada:
        matriz_ajustada[k] /= suma_nueva
    
    return matriz_ajustada

# ============================================================
# MERCADOS A PARTIR DE POISSON
# ============================================================
def poisson_pmf(k, lam):
    """Distribución de probabilidad de Poisson"""
    import math

    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k) * math.exp(-lam) / math.factorial(k)


def calcular_mercados_poisson(lambda_local, lambda_visitante, max_goles=8,
                              alpha_local=0.0, alpha_visitante=0.0,
                              usar_negbin=False,
                              rho_dixon_coles=0.0):
    """
    Calcula TODOS los mercados de goles usando Poisson, NegBin y Dixon-Coles.
    
    Pipeline:
    1. Generar matriz base con Poisson o NegBin.
    2. Aplicar factor Dixon-Coles (si rho ≠ 0).
    3. Renormalizar.
    4. Derivar mercados.
    
    Args:
        lambda_local, lambda_visitante: goles esperados
        max_goles: máximo de goles a considerar
        alpha_local, alpha_visitante: parámetros de dispersión NegBin
        usar_negbin: si True, usa NegBin; si False, usa Poisson
        rho_dixon_coles: parámetro ρ de Dixon-Coles (0 = desactivado)
    """
    # ========== 1. Matriz base ==========
    matriz = {}
    
    if usar_negbin:
        pmf_local = (lambda k: negbin_pmf(k, lambda_local, alpha_local)) if alpha_local > 0 else (lambda k: poisson_pmf(k, lambda_local))
        pmf_visit = (lambda k: negbin_pmf(k, lambda_visitante, alpha_visitante)) if alpha_visitante > 0 else (lambda k: poisson_pmf(k, lambda_visitante))
    else:
        pmf_local = lambda k: poisson_pmf(k, lambda_local)
        pmf_visit = lambda k: poisson_pmf(k, lambda_visitante)
    
    for i in range(max_goles + 1):
        for j in range(max_goles + 1):
            matriz[(i, j)] = pmf_local(i) * pmf_visit(j)
    
    # ========== 2. Normalizar ==========
    total = sum(matriz.values())
    for k in matriz:
        matriz[k] /= total
    
    # ========== 3. Dixon-Coles ==========
    if rho_dixon_coles != 0:
        matriz = aplicar_dixon_coles(matriz, lambda_local, lambda_visitante, rho_dixon_coles)

    # Derivar mercados
    prob_local = sum(p for (i, j), p in matriz.items() if i > j)
    prob_empate = sum(p for (i, j), p in matriz.items() if i == j)
    prob_visitante = sum(p for (i, j), p in matriz.items() if i < j)

    prob_btts = sum(p for (i, j), p in matriz.items() if i > 0 and j > 0)
    prob_local_marca = sum(p for (i, j), p in matriz.items() if i > 0)
    prob_visit_marca = sum(p for (i, j), p in matriz.items() if j > 0)

    # Over/Under
    def prob_total_mas_de(n):
        return sum(p for (i, j), p in matriz.items() if i + j > n)

    overs = {}
    unders = {}
    for linea in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        overs[linea] = prob_total_mas_de(linea)
        unders[linea] = 1 - overs[linea]

    # Goles por equipo
    prob_local_0 = sum(p for (i, j), p in matriz.items() if i == 0)
    prob_local_1 = sum(p for (i, j), p in matriz.items() if i == 1)
    prob_local_2 = sum(p for (i, j), p in matriz.items() if i == 2)
    prob_local_3mas = sum(p for (i, j), p in matriz.items() if i >= 3)

    prob_visit_0 = sum(p for (i, j), p in matriz.items() if j == 0)
    prob_visit_1 = sum(p for (i, j), p in matriz.items() if j == 1)
    prob_visit_2 = sum(p for (i, j), p in matriz.items() if j == 2)
    prob_visit_3mas = sum(p for (i, j), p in matriz.items() if j >= 3)

    # Top marcadores exactos
    top_marcadores = sorted(matriz.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        '1X2': {
            'local': prob_local,
            'empate': prob_empate,
            'visitante': prob_visitante
        },
        'BTTS': prob_btts,
        'doble_oportunidad': {
            '1X': prob_local + prob_empate,
            '12': prob_local + prob_visitante,
            'X2': prob_empate + prob_visitante
        },
        'over': overs,
        'under': unders,
        'local_marca': prob_local_marca,
        'visitante_marca': prob_visit_marca,
        'goles_local': {
            '0': prob_local_0,
            '1': prob_local_1,
            '2': prob_local_2,
            '3+': prob_local_3mas
        },
        'goles_visitante': {
            '0': prob_visit_0,
            '1': prob_visit_1,
            '2': prob_visit_2,
            '3+': prob_visit_3mas
        },
        'top_marcadores': [
            {'marcador': f'{i}-{j}', 'probabilidad': round(p, 4)}
            for (i, j), p in top_marcadores
        ],
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
        # ========== NUEVO: modelo usado (FASE 8.4) ==========
        'modelo': 'negbin' if usar_negbin else 'poisson',
        'alpha_local': alpha_local,
        'alpha_visitante': alpha_visitante,
    }


# ============================================================
# H2H
# ============================================================
def obtener_h2h(equipo1, equipo2, limite=10, fecha_corte=None):
    """
    Devuelve los últimos enfrentamientos directos entre 2 equipos.
    Sin límite mínimo.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Filtro dinámico de fecha
        filtro_fecha = ''
        params_extra = []
        if fecha_corte:
            filtro_fecha = ' AND p.fecha < ?'
            params_extra = [fecha_corte]

        c.execute(
            f"""
            SELECT 
                p.id, p.fecha, p.liga, p.temporada,
                p.local, p.visitante,
                (SELECT SUM(G) FROM estadisticas_local WHERE partido_id = p.id) as goles_local,
                (SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = p.id) as goles_visitante
            FROM partidos p
            WHERE ((p.local = ? AND p.visitante = ?)
               OR (p.local = ? AND p.visitante = ?)){filtro_fecha}
            ORDER BY p.fecha DESC
            LIMIT ?
        """,
            [equipo1, equipo2, equipo2, equipo1] + params_extra + [limite],
        )

        partidos = []
        for row in c.fetchall():
            partidos.append(
                {
                    "id": row["id"],
                    "fecha": row["fecha"],
                    "liga": row["liga"],
                    "local": row["local"],
                    "visitante": row["visitante"],
                    "goles_local": row["goles_local"] or 0,
                    "goles_visitante": row["goles_visitante"] or 0,
                }
            )

        if not partidos:
            return {
                "partidos": [],
                "total": 0,
                "victorias_equipo1": 0,
                "victorias_equipo2": 0,
                "empates": 0,
                "goles_equipo1": 0,
                "goles_equipo2": 0,
            }

        # Analizar
        v1 = v2 = emp = 0
        g1 = g2 = 0
        for p in partidos:
            if p["local"] == equipo1:
                goles_e1, goles_e2 = p["goles_local"], p["goles_visitante"]
            else:
                goles_e1, goles_e2 = p["goles_visitante"], p["goles_local"]

            g1 += goles_e1
            g2 += goles_e2

            if goles_e1 > goles_e2:
                v1 += 1
            elif goles_e1 < goles_e2:
                v2 += 1
            else:
                emp += 1

        return {
            "partidos": partidos,
            "total": len(partidos),
            "victorias_equipo1": v1,
            "victorias_equipo2": v2,
            "empates": emp,
            "goles_equipo1": g1,
            "goles_equipo2": g2,
            "promedio_goles": round((g1 + g2) / len(partidos), 2),
        }

    finally:
        conn.close()


# ============================================================
# NIVEL DE CONFIANZA
# ============================================================
def calcular_nivel_confianza(
    partidos_local, partidos_visitante, tiene_h2h, tiene_tendencia_clara
):
    """
    Devuelve nivel de confianza: alta, media, baja.
    """
    if partidos_local >= MIN_PARTIDOS_ALTO and partidos_visitante >= MIN_PARTIDOS_ALTO:
        nivel = "alta"
        emoji = "🟢"
        color = "#00ff88"
    elif (
        partidos_local >= MIN_PARTIDOS_MEDIO
        and partidos_visitante >= MIN_PARTIDOS_MEDIO
    ):
        nivel = "media"
        emoji = "🟡"
        color = "#ffaa00"
    else:
        nivel = "baja"
        emoji = "🔴"
        color = "#ff4455"

    factores = []
    if partidos_local < MIN_PARTIDOS_MEDIO:
        factores.append(f"Solo {partidos_local} partidos de local")
    if partidos_visitante < MIN_PARTIDOS_MEDIO:
        factores.append(f"Solo {partidos_visitante} partidos de visitante")
    if not tiene_h2h:
        factores.append("Sin H2H disponible")
    if not tiene_tendencia_clara:
        factores.append("Tendencia no clara")

    return {
        "nivel": nivel,
        "emoji": emoji,
        "color": color,
        "factores": factores,
        "partidos_local": partidos_local,
        "partidos_visitante": partidos_visitante,
        "tiene_h2h": tiene_h2h,
    }


# ============================================================
# PROBABILIDADES POR JUGADOR
# ============================================================
def _probabilidad_binomial(prob_evento, n_intentos, k_exitos):
    """
    P(X >= k) usando distribución binomial.
    Retorna la probabilidad de que ocurra al menos k veces en n intentos.
    """
    from math import comb

    if prob_evento <= 0:
        return 0.0 if k_exitos > 0 else 1.0
    if prob_evento >= 1:
        return 1.0

    # P(X < k) = sumatoria de P(X = i) para i=0..k-1
    p_menor_que_k = sum(
        comb(n_intentos, i) * (prob_evento**i) * ((1 - prob_evento) ** (n_intentos - i))
        for i in range(k_exitos)
    )
    return 1 - p_menor_que_k


def calcular_probabilidades_jugador(
    jugador, equipo, como_local=None, liga_pronostico=None, fecha_corte=None
):
    """
    Calcula probabilidades de eventos futuros para un jugador
    basándose en su histórico ponderado.
    Ignora NULL (no los convierte en 0).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Obtener los partidos del equipo (máx 10 recientes, sin filtro de localía)
        # Filtro dinámico de fecha
        filtro_fecha = ''
        params_extra = []
        if fecha_corte:
            filtro_fecha = ' AND p.fecha < ?'
            params_extra = [fecha_corte]

        c.execute(
            f"""
            SELECT p.id, p.fecha
            FROM partidos p
            WHERE (p.local = ? OR p.visitante = ?){filtro_fecha}
            ORDER BY p.fecha DESC
            LIMIT 10
        """,
            [equipo, equipo] + params_extra,
        )
        partidos_recientes = [r["id"] for r in c.fetchall()]

        if not partidos_recientes:
            return None

        # Obtener las estadísticas del jugador en esos partidos
        placeholders = ",".join("?" * len(partidos_recientes))

        # Como local
        c.execute(
            f"""
            SELECT el.*, p.fecha, p.id as partido_id
            FROM estadisticas_local el
            JOIN partidos p ON el.partido_id = p.id
            WHERE el.jugador = ? AND el.partido_id IN ({placeholders})
            ORDER BY p.fecha DESC
        """,
            [jugador] + partidos_recientes,
        )
        partidos_local = [dict(r) for r in c.fetchall()]

        # Como visitante
        c.execute(
            f"""
            SELECT ev.*, p.fecha, p.id as partido_id
            FROM estadisticas_visitante ev
            JOIN partidos p ON ev.partido_id = p.id
            WHERE ev.jugador = ? AND ev.partido_id IN ({placeholders})
            ORDER BY p.fecha DESC
        """,
            [jugador] + partidos_recientes,
        )
        partidos_visit = [dict(r) for r in c.fetchall()]

        # Combinar
        todos_partidos = []
        for p in partidos_local:
            todos_partidos.append({"fecha": p["fecha"], "stats": p})
        for p in partidos_visit:
            todos_partidos.append({"fecha": p["fecha"], "stats": p})

        if not todos_partidos:
            return None

        # Ordenar por fecha descendente
        todos_partidos.sort(key=lambda x: x["fecha"] or "0000", reverse=True)

        # ============================================================
        # CAMBIO 1: Declarar el tracking de pesos válidos por campo
        # ============================================================
        # Aquí se acumularán los pesos de SOLO los partidos donde el campo tiene dato.
        # Si un partido tiene SAV = None, ese partido NO contribuye al promedio de SAV.
        # Este dict permite saber cuál es el peso total "válido" para cada campo.
        pesos_por_campo = defaultdict(float)

        n_partidos = len(todos_partidos)
        suma_pesos = 0
        stats_ponderadas = defaultdict(float)
        campos = [
            "G",
            "A",
            "TR",
            "TA",
            "Crn",
            "S",
            "SOnT",
            "BS",
            "P",
            "C",
            "E",
            "O",
            "FC",
            "FR",
            "SAV",
        ]

        # Ponderar por recencia (0.85^índice)
        for i, partido in enumerate(todos_partidos):
            peso = 0.85**i
            suma_pesos += peso

            for campo in campos:
                valor = partido["stats"].get(campo)  # Sin or 0

                if valor is None:  # ← Ignorar NULL
                    continue

                # Acumular valor ponderado
                stats_ponderadas[campo] += valor * peso

                # Acumular peso SOLO para este campo (importante: cada campo tiene su propio peso válido)
                pesos_por_campo[campo] += peso

        # ============================================================
        # CAMBIO 2: Calcular promedio usando SOLO pesos válidos por campo
        # ============================================================
        promedios = {}
        cobertura_campos = {}

        for campo in campos:
            peso_valido = pesos_por_campo.get(campo, 0)

            if peso_valido > 0:
                # Hay datos válidos para este campo
                promedios[campo] = stats_ponderadas[campo] / peso_valido
            else:
                # Ningún partido tenía dato para este campo
                promedios[campo] = None

            # Calcular cobertura: cuántos partidos tenían este dato
            apariciones = sum(
                1 for p in todos_partidos if p["stats"].get(campo) is not None
            )
            cobertura_campos[campo] = {
                "presentes": apariciones,
                "total": n_partidos,
                "porcentaje": (
                    round(apariciones / n_partidos * 100, 1) if n_partidos > 0 else 0
                ),
            }

        # ========== CALCULAR PROBABILIDADES ==========
        def prob_poisson_al_menos_k(lam, k):
            """P(X >= k) con Poisson"""
            import math

            if lam is None or lam <= 0:
                return 0
            p_menor = sum(
                (lam**i) * math.exp(-lam) / math.factorial(i) for i in range(k)
            )
            return 1 - p_menor

        eventos = {}

        # Faltas
        lam_fc = promedios.get("FC")
        if lam_fc is not None:
            eventos["faltas"] = {
                "promedio": round(lam_fc, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_fc, 1), 3),
                ">=2": round(prob_poisson_al_menos_k(lam_fc, 2), 3),
                ">=3": round(prob_poisson_al_menos_k(lam_fc, 3), 3),
                "cobertura": cobertura_campos["FC"]["porcentaje"],
            }
        else:
            eventos["faltas"] = {"promedio": None, "cobertura": 0}

        # Tiros
        lam_s = promedios.get("S")
        if lam_s is not None:
            eventos["tiros"] = {
                "promedio": round(lam_s, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_s, 1), 3),
                ">=2": round(prob_poisson_al_menos_k(lam_s, 2), 3),
                ">=3": round(prob_poisson_al_menos_k(lam_s, 3), 3),
                "cobertura": cobertura_campos["S"]["porcentaje"],
            }
        else:
            eventos["tiros"] = {"promedio": None, "cobertura": 0}

        # Tiros a puerta
        lam_sont = promedios.get("SOnT")
        if lam_sont is not None:
            eventos["tiros_puerta"] = {
                "promedio": round(lam_sont, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_sont, 1), 3),
                ">=2": round(prob_poisson_al_menos_k(lam_sont, 2), 3),
                "cobertura": cobertura_campos["SOnT"]["porcentaje"],
            }
        else:
            eventos["tiros_puerta"] = {"promedio": None, "cobertura": 0}

        # Goles
        lam_g = promedios.get("G")
        if lam_g is not None:
            eventos["goles"] = {
                "promedio": round(lam_g, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_g, 1), 3),
                "cobertura": cobertura_campos["G"]["porcentaje"],
            }
        else:
            eventos["goles"] = {"promedio": None, "cobertura": 0}

        # Asistencias
        lam_a = promedios.get("A")
        if lam_a is not None:
            eventos["asistencias"] = {
                "promedio": round(lam_a, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_a, 1), 3),
                "cobertura": cobertura_campos["A"]["porcentaje"],
            }
        else:
            eventos["asistencias"] = {"promedio": None, "cobertura": 0}

        # Tarjetas amarillas
        lam_ta = promedios.get("TA")
        if lam_ta is not None:
            eventos["tarjetas_amarillas"] = {
                "promedio": round(lam_ta, 2),
                ">=1": round(prob_poisson_al_menos_k(lam_ta, 1), 3),
                "cobertura": cobertura_campos["TA"]["porcentaje"],
            }
        else:
            eventos["tarjetas_amarillas"] = {"promedio": None, "cobertura": 0}

        # Paradas (portero)
        lam_sav = promedios.get("SAV")
        if lam_sav is not None and lam_sav > 0:
            eventos["paradas"] = {
                "promedio": round(lam_sav, 2),
                ">=2": round(prob_poisson_al_menos_k(lam_sav, 2), 3),
                ">=3": round(prob_poisson_al_menos_k(lam_sav, 3), 3),
                ">=4": round(prob_poisson_al_menos_k(lam_sav, 4), 3),
                "cobertura": cobertura_campos["SAV"]["porcentaje"],
            }
        else:
            eventos["paradas"] = {
                "promedio": lam_sav,
                "cobertura": cobertura_campos["SAV"]["porcentaje"],
            }

        # ============================================================
        # CAMBIO 3: Añadir 'cobertura' al return
        # ============================================================
        return {
            "nombre": jugador,
            "equipo": equipo,
            "partidos": n_partidos,
            "eventos": eventos,
            "cobertura": cobertura_campos,  # ← NUEVO: cobertura por campo
        }

    finally:
        conn.close()

# ============================================================
# DETECCIÓN DE PORTEROS (FASE 9.2)
# ============================================================
def detectar_porteros(equipo, min_partidos=3, ventana=10, fecha_corte=None):
    """
    Detecta jugadores que son porteros usando una heurística multi-señal.
    
    Un jugador es portero si cumple AL MENOS 2 de estas 3 condiciones
    sobre sus últimos `ventana` partidos:
    
    1. Frecuencia de SAV > 0 ≥ 60% de los partidos.
    2. SAV promedio ≥ 1.5 por partido.
    3. Cero goles y cero asistencias (en los últimos N partidos).
    
    Args:
        equipo: nombre del equipo
        min_partidos: mínimo de partidos para evaluar (default 3)
        ventana: cuántos partidos recientes mirar (default 10)
    
    Returns:
        {
            'porteros': [
                {
                    'nombre': str,
                    'partidos': int,
                    'sav_promedio': float,
                    'sav_frecuencia': float,   # % de partidos con SAV > 0
                    'goles': int,
                    'asistencias': int,
                    'condiciones_cumplidas': int,
                    'confianza': 'alta' | 'media',
                },
                ...
            ],
            'total_jugadores_analizados': int,
        }
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Obtener IDs de los últimos `ventana` partidos del equipo
        # Filtro dinámico de fecha
        filtro_fecha = ''
        params_extra = []
        if fecha_corte:
            filtro_fecha = ' AND p.fecha < ?'
            params_extra = [fecha_corte]

        c.execute(f'''
            SELECT p.id FROM partidos p
            WHERE (p.local = ? OR p.visitante = ?){filtro_fecha}
            ORDER BY p.fecha DESC LIMIT ?
        ''', [equipo, equipo] + params_extra + [ventana])
        partidos_ids = [r[0] for r in c.fetchall()]
        
        if not partidos_ids:
            return {'porteros': [], 'total_jugadores_analizados': 0}
        
        placeholders = ','.join('?' * len(partidos_ids))
        
        # Recolectar stats por jugador (local + visitante)
        jugadores_stats = defaultdict(lambda: {
            'partidos': 0,
            'sav_total': 0,
            'sav_presentes': 0,   # partidos con SAV > 0
            'goles': 0,
            'asistencias': 0,
        })
        
        # Como local
        c.execute(f'''
            SELECT jugador, SAV, G, A
            FROM estadisticas_local
            WHERE partido_id IN ({placeholders})
        ''', partidos_ids)
        for row in c.fetchall():
            jug = row['jugador']
            if not jug:
                continue
            jugadores_stats[jug]['partidos'] += 1
            sav = row['SAV']
            if sav is not None:
                jugadores_stats[jug]['sav_total'] += sav
                if sav > 0:
                    jugadores_stats[jug]['sav_presentes'] += 1
            if row['G']:
                jugadores_stats[jug]['goles'] += row['G']
            if row['A']:
                jugadores_stats[jug]['asistencias'] += row['A']
        
        # Como visitante
        c.execute(f'''
            SELECT jugador, SAV, G, A
            FROM estadisticas_visitante
            WHERE partido_id IN ({placeholders})
        ''', partidos_ids)
        for row in c.fetchall():
            jug = row['jugador']
            if not jug:
                continue
            jugadores_stats[jug]['partidos'] += 1
            sav = row['SAV']
            if sav is not None:
                jugadores_stats[jug]['sav_total'] += sav
                if sav > 0:
                    jugadores_stats[jug]['sav_presentes'] += 1
            if row['G']:
                jugadores_stats[jug]['goles'] += row['G']
            if row['A']:
                jugadores_stats[jug]['asistencias'] += row['A']
        
        # ========== Aplicar heurística ==========
        porteros = []
        
        for nombre, stats in jugadores_stats.items():
            n_partidos = stats['partidos']
            if n_partidos < min_partidos:
                continue
            
            sav_prom = stats['sav_total'] / n_partidos if n_partidos > 0 else 0
            sav_freq = stats['sav_presentes'] / n_partidos if n_partidos > 0 else 0
            
            # Condiciones
            cond_1 = sav_freq >= 0.60                    # Frecuencia alta
            cond_2 = sav_prom >= 1.5                     # Promedio alto
            cond_3 = (stats['goles'] == 0 and stats['asistencias'] == 0)
            
            condiciones_cumplidas = sum([cond_1, cond_2, cond_3])
            
            # Mínimo 2 de 3 para considerar portero
            if condiciones_cumplidas >= 2:
                confianza = 'alta' if condiciones_cumplidas == 3 else 'media'
                porteros.append({
                    'nombre': nombre,
                    'partidos': n_partidos,
                    'sav_promedio': round(sav_prom, 2),
                    'sav_frecuencia': round(sav_freq * 100, 1),
                    'goles': stats['goles'],
                    'asistencias': stats['asistencias'],
                    'condiciones_cumplidas': condiciones_cumplidas,
                    'confianza': confianza,
                })
        
        # Ordenar por confianza y SAV promedio
        porteros.sort(key=lambda x: (
            0 if x['confianza'] == 'alta' else 1,
            -x['sav_promedio']
        ))
        
        return {
            'porteros': porteros,
            'total_jugadores_analizados': len(jugadores_stats),
        }
        
    finally:
        conn.close()

def obtener_top_jugadores_probabilidades(
    equipo, categoria="goleadores", limite=5, liga_pronostico=None, fecha_corte=None
):
    """
    Devuelve los top N jugadores con sus probabilidades calculadas.

    Args:
        equipo: nombre del equipo
        categoria: 'goleadores' | 'faltas' | 'porteros' | 'tiros'
        limite: cuántos jugadores devolver

    Returns:
        Lista de dicts con probabilidades
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Obtener los últimos 10 partidos del equipo
        # Filtro dinámico de fecha
        filtro_fecha = ''
        params_extra = []
        if fecha_corte:
            filtro_fecha = ' AND p.fecha < ?'
            params_extra = [fecha_corte]

        c.execute(
            f"""
            SELECT p.id FROM partidos p
            WHERE (p.local = ? OR p.visitante = ?){filtro_fecha}
            ORDER BY p.fecha DESC LIMIT 10
        """,
            [equipo, equipo] + params_extra,
        )
        partidos_ids = [r[0] for r in c.fetchall()]

        if not partidos_ids:
            return []

        # Obtener candidatos según categoría
        placeholders = ",".join("?" * len(partidos_ids))

        if categoria == "goleadores":
            # Buscar en local y visitante
            c.execute(
                f"""
                SELECT DISTINCT jugador FROM estadisticas_local
                WHERE partido_id IN ({placeholders}) AND G > 0
                UNION
                SELECT DISTINCT jugador FROM estadisticas_visitante
                WHERE partido_id IN ({placeholders}) AND G > 0
            """,
                partidos_ids + partidos_ids,
            )
        elif categoria == "faltas":
            c.execute(
                f"""
                SELECT DISTINCT jugador FROM estadisticas_local
                WHERE partido_id IN ({placeholders}) AND FC > 0
                UNION
                SELECT DISTINCT jugador FROM estadisticas_visitante
                WHERE partido_id IN ({placeholders}) AND FC > 0
            """,
                partidos_ids + partidos_ids,
            )
        elif categoria == 'porteros':
            # ========== NUEVA LÓGICA (FASE 9.2): heurística de detección ==========
            deteccion = detectar_porteros(equipo, min_partidos=3, ventana=10, fecha_corte=fecha_corte)
            candidatos = [p['nombre'] for p in deteccion['porteros']]
            
        elif categoria == "tiros":
            c.execute(
                f"""
                SELECT DISTINCT jugador FROM estadisticas_local
                WHERE partido_id IN ({placeholders}) AND S > 0
                UNION
                SELECT DISTINCT jugador FROM estadisticas_visitante
                WHERE partido_id IN ({placeholders}) AND S > 0
            """,
                partidos_ids + partidos_ids,
            )
        else:
            return []

        candidatos = [r[0] for r in c.fetchall()]

        # Calcular probabilidades para cada candidato
        resultados = []
        for jugador in candidatos:
            probs = calcular_probabilidades_jugador(
                jugador, equipo, liga_pronostico=liga_pronostico,
                fecha_corte=fecha_corte
            )
            if probs:
                resultados.append(probs)

        # Ordenar según categoría
        if categoria == "goleadores":
            resultados.sort(
                key=lambda x: (
                    x["eventos"]["goles"][">=1"],
                    x["eventos"]["goles"]["promedio"],
                ),
                reverse=True,
            )
        elif categoria == "faltas":
            resultados.sort(
                key=lambda x: (
                    x["eventos"]["faltas"][">=1"],
                    x["eventos"]["faltas"]["promedio"],
                ),
                reverse=True,
            )
        elif categoria == 'porteros':
            # Ordenamos por probabilidad de >=2 paradas, con fallback al promedio
            def _key_portero(x):
                ev = x['eventos'].get('paradas', {})
                return (
                    ev.get('>=2', 0) or 0,
                    ev.get('promedio', 0) or 0
                )
            resultados.sort(key=_key_portero, reverse=True)
            
        elif categoria == "tiros":
            resultados.sort(
                key=lambda x: (
                    x["eventos"]["tiros"][">=1"],
                    x["eventos"]["tiros"]["promedio"],
                ),
                reverse=True,
            )

            # Filtrar jugadores con al menos 3 partidos
        MIN_PARTIDOS_JUGADOR = 3
        resultados_filtrados = [
            r for r in resultados if r.get("partidos", 0) >= MIN_PARTIDOS_JUGADOR
        ]

        # Si después de filtrar quedan menos, devolver los disponibles
        if len(resultados_filtrados) < 3:
            return resultados[:limite]

        return resultados_filtrados[:limite]

    finally:
        conn.close()


# ============================================================
# PROMEDIOS DE LIGA (A3.2)
# ============================================================
def calcular_promedios_liga(liga, temporada=None, fecha_corte=None):
    """
    Calcula los promedios de referencia de una liga.
    Usa media y mediana para robustez.

    Returns:
        {
            'liga': str,
            'temporada': str or None,
            'partidos': int,
            'goles': {'media': float, 'mediana': float},
            'tiros': {'media': float, 'mediana': float},
            'tiros_puerta': {'media': float, 'mediana': float},
            'corners': {'media': float, 'mediana': float},
            'faltas': {'media': float, 'mediana': float},
            'tarjetas_amarillas': {'media': float, 'mediana': float},
            'tarjetas_rojas': {'media': float, 'mediana': float},
            'paradas': {'media': float, 'mediana': float},
            'tiros_bloqueados': {'media': float, 'mediana': float},
        }
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Filtro de temporada + fecha_corte
        condiciones = ["liga = ?"]
        params = [liga]

        if temporada:
            condiciones.append("temporada = ?")
            params.append(temporada)

        if fecha_corte:
            condiciones.append("fecha < ?")
            params.append(fecha_corte)

        filtro = "WHERE " + " AND ".join(condiciones)
        params = tuple(params)

        # ===== Obtener todos los partidos de la liga =====
        c.execute(
            f"""
            SELECT id FROM partidos {filtro}
        """,
            params,
        )
        partidos_ids = [r[0] for r in c.fetchall()]

        if not partidos_ids:
            return None

        # ===== Extraer estadísticas por partido (local + visitante) =====
        stats_por_partido = []

        for pid in partidos_ids:
            # Obtener stats agregadas del LOCAL
            c.execute(
                """
                SELECT 
                    COALESCE(SUM(G), 0) as goles,
                    COALESCE(SUM(S), 0) as tiros,
                    COALESCE(SUM(SOnT), 0) as tiros_puerta,
                    COALESCE(SUM(Crn), 0) as corners,
                    COALESCE(SUM(FC), 0) as faltas,
                    COALESCE(SUM(TA), 0) as tarjetas_amarillas,
                    COALESCE(SUM(TR), 0) as tarjetas_rojas,
                    COALESCE(SUM(SAV), 0) as paradas,
                    COALESCE(SUM(BS), 0) as tiros_bloqueados
                FROM estadisticas_local
                WHERE partido_id = ?
            """,
                (pid,),
            )
            row_local = c.fetchone()

            # Obtener stats agregadas del VISITANTE
            c.execute(
                """
                SELECT 
                    COALESCE(SUM(G), 0) as goles,
                    COALESCE(SUM(S), 0) as tiros,
                    COALESCE(SUM(SOnT), 0) as tiros_puerta,
                    COALESCE(SUM(Crn), 0) as corners,
                    COALESCE(SUM(FC), 0) as faltas,
                    COALESCE(SUM(TA), 0) as tarjetas_amarillas,
                    COALESCE(SUM(TR), 0) as tarjetas_rojas,
                    COALESCE(SUM(SAV), 0) as paradas,
                    COALESCE(SUM(BS), 0) as tiros_bloqueados
                FROM estadisticas_visitante
                WHERE partido_id = ?
            """,
                (pid,),
            )
            row_visit = c.fetchone()

            if not row_local or not row_visit:
                continue

            # Añadir ambos (local y visitante) al conjunto de la liga
            stats_por_partido.append(row_local)
            stats_por_partido.append(row_visit)

        if not stats_por_partido:
            return None

        # ===== Calcular media y mediana para cada campo =====
        campos = [
            "goles",
            "tiros",
            "tiros_puerta",
            "corners",
            "faltas",
            "tarjetas_amarillas",
            "tarjetas_rojas",
            "paradas",
            "tiros_bloqueados",
        ]

        resultados = {}

        for i, campo in enumerate(campos):
            valores = [row[i] for row in stats_por_partido]
            valores.sort()

            n = len(valores)
            media = sum(valores) / n

            # Mediana
            if n % 2 == 0:
                mediana = (valores[n // 2 - 1] + valores[n // 2]) / 2
            else:
                mediana = valores[n // 2]

            resultados[campo] = {"media": round(media, 3), "mediana": round(mediana, 3)}

        return {
            "liga": liga,
            "temporada": temporada,
            "partidos": len(partidos_ids),
            "equipos_observados": len(stats_por_partido),
            **resultados,
        }

    finally:
        conn.close()


# ============================================================
# FUNCIONES AUXILIARES POR ID (5C.1)
# ============================================================
def obtener_id_equipo(nombre):
    """Devuelve el ID de un equipo por su nombre canónico"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM teams WHERE name = ?", (nombre,))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def obtener_nombre_equipo(team_id):
    """Devuelve el nombre canónico de un equipo por su ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def obtener_id_jugador(nombre):
    """Devuelve el ID de un jugador por su nombre"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM players WHERE name = ?", (nombre,))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def obtener_nombre_jugador(player_id):
    """Devuelve el nombre de un jugador por su ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT name FROM players WHERE id = ?", (player_id,))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def obtener_partidos_historicos_por_id(
    team_id, como_local=None, liga_pronostico=None, limite=30
):
    """
    Versión por ID de obtener_partidos_historicos().
    Internamente usa el ID para consultar, y devuelve los mismos datos.
    """
    # Obtener nombre canónico
    nombre = obtener_nombre_equipo(team_id)
    if not nombre:
        return []

    # Reutilizar la función existente
    return obtener_partidos_historicos(
        nombre, como_local=como_local, liga_pronostico=liga_pronostico, limite=limite
    )


# ============================================================
# FEATURES AVANZADAS PARA CÓRNERS Y TARJETAS (FASE 8.6 / FE-3)
# ============================================================


def _calcular_factor_racha_metrica(partidos, campo, umbral_alto, umbral_bajo, cap=0.03):
    """
    Factor de racha para una métrica específica (córners, tarjetas).

    Analiza los últimos 3 partidos y compara con el promedio general.

    Args:
        partidos: lista de dicts con la métrica
        campo: nombre del campo ('corners', 'tarjetas_amarillas', etc.)
        umbral_alto: valor a partir del cual consideramos "racha alta"
        umbral_bajo: valor por debajo del cual consideramos "racha baja"
        cap: máximo ajuste (±3% por defecto)

    Returns:
        (factor, tipo)
    """
    if not partidos or len(partidos) < 3:
        return 1.0, "sin_datos"

    # Ordenar por fecha descendente
    ordenados = sorted(partidos, key=lambda x: x.get("fecha") or "", reverse=True)
    ultimos_3 = ordenados[:3]

    # Valores de los últimos 3
    valores = [p.get(campo) for p in ultimos_3 if p.get(campo) is not None]

    if len(valores) < 3:
        return 1.0, "sin_datos"

    promedio_reciente = sum(valores) / len(valores)

    # Comparar con el promedio general del equipo
    todos_valores = [p.get(campo) for p in partidos if p.get(campo) is not None]
    if not todos_valores:
        return 1.0, "sin_datos"

    promedio_general = sum(todos_valores) / len(todos_valores)

    if promedio_general <= 0:
        return 1.0, "sin_datos"

    # Ratio reciente vs general
    ratio = promedio_reciente / promedio_general

    if ratio > 1.2 and promedio_reciente >= umbral_alto:
        factor = 1.0 + cap
        tipo = "alta"
    elif ratio < 0.8 and promedio_reciente <= umbral_bajo:
        factor = 1.0 - cap
        tipo = "baja"
    else:
        factor = 1.0
        tipo = "normal"

    return round(factor, 4), tipo


def _calcular_factor_tendencia_metrica(partidos, campo, cap=0.04):
    """
    Factor de tendencia para una métrica específica.

    Compara los últimos 5 partidos con los 5 anteriores.

    Args:
        partidos: lista de dicts con la métrica
        campo: nombre del campo
        cap: máximo ajuste (±4% por defecto)

    Returns:
        (factor, tipo)
    """
    if not partidos or len(partidos) < 6:
        return 1.0, "sin_datos"

    ordenados = sorted(partidos, key=lambda x: x.get("fecha") or "", reverse=True)
    ultimos_5 = ordenados[:5]
    anteriores_5 = ordenados[5:10]

    vals_recientes = [p.get(campo) for p in ultimos_5 if p.get(campo) is not None]
    vals_anteriores = [p.get(campo) for p in anteriores_5 if p.get(campo) is not None]

    if len(vals_recientes) < 3 or len(vals_anteriores) < 3:
        return 1.0, "sin_datos"

    prom_reciente = sum(vals_recientes) / len(vals_recientes)
    prom_anterior = sum(vals_anteriores) / len(vals_anteriores)

    if prom_anterior <= 0:
        return 1.0, "sin_datos"

    cambio = (prom_reciente - prom_anterior) / prom_anterior

    if cambio > 0.15:
        factor = 1.0 + min(cambio, cap)
        tipo = "subiendo"
    elif cambio < -0.15:
        factor = 1.0 + max(cambio, -cap)
        tipo = "bajando"
    else:
        factor = 1.0
        tipo = "estable"

    return round(factor, 4), tipo


# ============================================================
# MODELO DE CÓRNERS (5D.1)
# ============================================================
def calcular_lambda_corners(equipo, rival, como_local, liga_pronostico=None, fecha_corte=None):
    """
    Calcula λ (córners esperados) para un equipo.

    Fórmula:
        λ_corners = (corners_propios_suav × corners_permitidos_rival_suav)
                    / promedio_liga_corners
                    × factor_localia
    """
    # Partidos del equipo
    partidos_equipo = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    if len(partidos_equipo) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {equipo} ({len(partidos_equipo)} partidos)",
            "lambda": None,
        }

    # Partidos del rival
    partidos_rival = obtener_partidos_historicos(
        rival, como_local=None, liga_pronostico=liga_pronostico, limite=15,
        fecha_corte=fecha_corte
    )

    if len(partidos_rival) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {rival} ({len(partidos_rival)} partidos)",
            "lambda": None,
        }

    # Estadísticas ponderadas
    stats_equipo = calcular_estadisticas_ponderadas(partidos_equipo, liga_pronostico)
    stats_rival = calcular_estadisticas_ponderadas(partidos_rival, liga_pronostico)

    if not stats_equipo or not stats_rival:
        return {"error": "Error calculando estadísticas de córners", "lambda": None}

    # Promedio de liga
    ligas = [p["liga"] for p in partidos_equipo if p.get("liga")]
    liga_principal = max(set(ligas), key=ligas.count) if ligas else liga_pronostico

    promedios_liga = None
    if liga_principal:
        promedios_liga = calcular_promedios_liga(liga_principal)

    prom_corners_liga = 5.0  # fallback
    if promedios_liga and promedios_liga.get("corners"):
        prom_corners_liga = promedios_liga["corners"]["media"]

    # Ataque de córners del equipo
    corners_propios = stats_equipo.get("corners") or prom_corners_liga

    # Ajustar por condición
    partidos_condicion = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=10,
        fecha_corte=fecha_corte
    )

    if len(partidos_condicion) >= 3:
        stats_cond = calcular_estadisticas_ponderadas(
            partidos_condicion, liga_pronostico
        )
        if stats_cond and stats_cond.get("corners") is not None:
            corners_propios = 0.6 * stats_cond["corners"] + 0.4 * corners_propios

    # Córners permitidos por el rival
    corners_permitidos_rival = stats_rival.get("rival_corners")
    if corners_permitidos_rival is None or corners_permitidos_rival == 0:
        corners_permitidos_rival = prom_corners_liga

    # Suavizado
    n_equipo = len(partidos_equipo)
    n_rival = len(partidos_rival)

    corners_propios_suav = (
        n_equipo * corners_propios + FACTOR_SUAVIZADO * prom_corners_liga
    ) / (n_equipo + FACTOR_SUAVIZADO)

    corners_permitidos_suav = (
        n_rival * corners_permitidos_rival + FACTOR_SUAVIZADO * prom_corners_liga
    ) / (n_rival + FACTOR_SUAVIZADO)

    # Factor localía
    factor_localia = _calcular_factor_localia(equipo, como_local, liga_pronostico, fecha_corte=fecha_corte)

    # ========== FEATURES AVANZADAS (FE-3) ==========
    factor_racha_c, tipo_racha_c = _calcular_factor_racha_metrica(
        partidos_equipo, "corners", umbral_alto=6.5, umbral_bajo=3.5, cap=0.03
    )
    factor_tend_c, tipo_tend_c = _calcular_factor_tendencia_metrica(
        partidos_equipo, "corners", cap=0.04
    )

    # λ
    if prom_corners_liga <= 0:
        prom_corners_liga = 5.0

    lam = (corners_propios_suav * corners_permitidos_suav) / prom_corners_liga
    lam = lam * factor_localia
    lam = lam * factor_racha_c * factor_tend_c
    lam = max(1.0, min(12.0, lam))

    return {
        "lambda": round(lam, 3),
        "corners_propios": round(corners_propios_suav, 3),
        "corners_permitidos_rival": round(corners_permitidos_suav, 3),
        "promedio_liga": round(prom_corners_liga, 3),
        "factor_localia": factor_localia,
        # ========== NUEVAS FEATURES ==========
        "factor_racha_corners": factor_racha_c,
        "tipo_racha_corners": tipo_racha_c,
        "factor_tendencia_corners": factor_tend_c,
        "tipo_tendencia_corners": tipo_tend_c,
        # ========== ==========
        "partidos": len(partidos_equipo),
        "partidos_rival": len(partidos_rival),
        "error": None,
    }


# ============================================================
# MODELO DE TARJETAS (5D.2)
# ============================================================
def calcular_lambda_tarjetas(equipo, rival, como_local, liga_pronostico=None, fecha_corte=None):
    """
    Calcula λ (tarjetas esperadas) para un equipo.

    Considera tarjetas amarillas (TA) y rojas (TR).
    Las rojas cuentan como 2 puntos (más graves).
    """
    partidos_equipo = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=15, fecha_corte=fecha_corte
    )

    if len(partidos_equipo) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {equipo} ({len(partidos_equipo)} partidos)",
            "lambda": None,
        }

    partidos_rival = obtener_partidos_historicos(
        rival, como_local=None, liga_pronostico=liga_pronostico, limite=15, fecha_corte=fecha_corte
    )

    if len(partidos_rival) < MIN_PARTIDOS_BAJO:
        return {
            "error": f"Datos insuficientes para {rival} ({len(partidos_rival)} partidos)",
            "lambda": None,
        }

    stats_equipo = calcular_estadisticas_ponderadas(partidos_equipo, liga_pronostico)
    stats_rival = calcular_estadisticas_ponderadas(partidos_rival, liga_pronostico)

    if not stats_equipo or not stats_rival:
        return {"error": "Error calculando estadísticas de tarjetas", "lambda": None}

    # Promedio de liga
    ligas = [p["liga"] for p in partidos_equipo if p.get("liga")]
    liga_principal = max(set(ligas), key=ligas.count) if ligas else liga_pronostico

    promedios_liga = None
    if liga_principal:
        promedios_liga = calcular_promedios_liga(liga_principal)

    prom_ta_liga = 2.0  # fallback
    if promedios_liga and promedios_liga.get("tarjetas_amarillas"):
        prom_ta_liga = promedios_liga["tarjetas_amarillas"]["media"]

    # Tarjetas del equipo (amarillas + rojas × 2)
    ta_equipo = stats_equipo.get("tarjetas_amarillas") or prom_ta_liga
    tr_equipo = stats_equipo.get("tarjetas_rojas") or 0
    tarjetas_equipo = ta_equipo + (tr_equipo * 2)

    # Tarjetas del rival
    ta_rival = stats_rival.get("tarjetas_amarillas") or prom_ta_liga
    tr_rival = stats_rival.get("tarjetas_rojas") or 0
    tarjetas_rival = ta_rival + (tr_rival * 2)

    # Suavizado
    n_equipo = len(partidos_equipo)
    n_rival = len(partidos_rival)

    tarjetas_equipo_suav = (
        n_equipo * tarjetas_equipo + FACTOR_SUAVIZADO * prom_ta_liga
    ) / (n_equipo + FACTOR_SUAVIZADO)

    tarjetas_rival_suav = (
        n_rival * tarjetas_rival + FACTOR_SUAVIZADO * prom_ta_liga
    ) / (n_rival + FACTOR_SUAVIZADO)

    # ========== FEATURES AVANZADAS (FE-3) ==========
    factor_racha_t, tipo_racha_t = _calcular_factor_racha_metrica(
        partidos_equipo,
        "tarjetas_amarillas",
        umbral_alto=3.0,
        umbral_bajo=1.0,
        cap=0.03,
    )
    factor_tend_t, tipo_tend_t = _calcular_factor_tendencia_metrica(
        partidos_equipo, "tarjetas_amarillas", cap=0.04
    )

    # Factor localía (para tarjetas, el local suele tener MENOS, no más)
    factor_localia = 0.95 if como_local else 1.05

    # λ
    lam = (tarjetas_equipo_suav + tarjetas_rival_suav) / 2
    lam = lam * factor_localia
    lam = lam * factor_racha_t * factor_tend_t
    lam = max(0.5, min(8.0, lam))

    return {
        "lambda": round(lam, 3),
        "tarjetas_equipo": round(tarjetas_equipo_suav, 3),
        "tarjetas_rival": round(tarjetas_rival_suav, 3),
        "promedio_liga": round(prom_ta_liga, 3),
        "factor_localia": factor_localia,
        # ========== NUEVAS FEATURES ==========
        "factor_racha_tarjetas": factor_racha_t,
        "tipo_racha_tarjetas": tipo_racha_t,
        "factor_tendencia_tarjetas": factor_tend_t,
        "tipo_tendencia_tarjetas": tipo_tend_t,
        # ========== ==========
        "partidos": len(partidos_equipo),
        "partidos_rival": len(partidos_rival),
        "error": None,
    }


# ============================================================
# MERCADOS DE CÓRNERS (Poisson)
# ============================================================
def calcular_mercados_corners(lambda_local, lambda_visitante, max_corners=20):
    """
    Calcula mercados de córners usando Poisson.

    Returns:
        {
            'total_esperado': float,
            'local_esperado': float,
            'visitante_esperado': float,
            'over': {7.5: p, 8.5: p, 9.5: p, 10.5: p, 11.5: p},
            'under': {...},
            'top_totales': [(8, p), (9, p), ...]  # córners totales más probables
        }
    """
    import math

    def poisson_pmf(k, lam):
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return (lam**k) * math.exp(-lam) / math.factorial(k)

    # Distribución de córners totales (suma de 2 Poisson)
    # Poisson(λ1) + Poisson(λ2) = Poisson(λ1+λ2)
    lambda_total = lambda_local + lambda_visitante

    total_dist = {}
    for i in range(max_corners + 1):
        total_dist[i] = poisson_pmf(i, lambda_total)

    # Normalizar
    suma = sum(total_dist.values())
    if suma > 0:
        for k in total_dist:
            total_dist[k] /= suma

    # Over/Under
    overs = {}
    unders = {}
    for linea in [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5]:
        p_over = sum(p for k, p in total_dist.items() if k > linea)
        overs[linea] = round(p_over, 4)
        unders[linea] = round(1 - p_over, 4)

    # Distribución individual
    local_dist = {i: poisson_pmf(i, lambda_local) for i in range(max_corners + 1)}
    visit_dist = {i: poisson_pmf(i, lambda_visitante) for i in range(max_corners + 1)}

    # Top 10 totales más probables
    top_totales = sorted(total_dist.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_esperado": round(lambda_total, 2),
        "local_esperado": round(lambda_local, 2),
        "visitante_esperado": round(lambda_visitante, 2),
        "over": overs,
        "under": unders,
        "top_totales": [
            {"corners": k, "probabilidad": round(p, 4)} for k, p in top_totales
        ],
    }


# ============================================================
# MERCADOS DE TARJETAS (Poisson)
# ============================================================
def calcular_mercados_tarjetas(lambda_local, lambda_visitante, max_tarjetas=15):
    """
    Calcula mercados de tarjetas usando Poisson.

    Returns:
        {
            'total_esperado': float,
            'local_esperado': float,
            'visitante_esperado': float,
            'over': {2.5: p, 3.5: p, 4.5: p, 5.5: p, 6.5: p},
            'under': {...},
            'top_totales': [(3, p), (4, p), ...]
        }
    """
    import math

    def poisson_pmf(k, lam):
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return (lam**k) * math.exp(-lam) / math.factorial(k)

    lambda_total = lambda_local + lambda_visitante

    total_dist = {}
    for i in range(max_tarjetas + 1):
        total_dist[i] = poisson_pmf(i, lambda_total)

    suma = sum(total_dist.values())
    if suma > 0:
        for k in total_dist:
            total_dist[k] /= suma

    overs = {}
    unders = {}
    for linea in [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
        p_over = sum(p for k, p in total_dist.items() if k > linea)
        overs[linea] = round(p_over, 4)
        unders[linea] = round(1 - p_over, 4)

    top_totales = sorted(total_dist.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_esperado": round(lambda_total, 2),
        "local_esperado": round(lambda_local, 2),
        "visitante_esperado": round(lambda_visitante, 2),
        "over": overs,
        "under": unders,
        "top_totales": [
            {"tarjetas": k, "probabilidad": round(p, 4)} for k, p in top_totales
        ],
    }


# ============================================================
# DETECCIÓN DE RACHAS (5E)
# ============================================================
def detectar_racha(equipo, liga_pronostico=None, limite=10, fecha_corte=None):
    """
    Detecta la racha actual de un equipo.

    Returns:
        {
            'tipo': 'ganadora' | 'perdedora' | 'invicto' | 'sin_ganar' | 'empates' | 'normal',
            'longitud': int,
            'factor': float,   # ajuste a aplicar
            'descripcion': str
        }
    """
    # Obtener partidos (con resultado)
    partidos = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=limite,
        fecha_corte=fecha_corte
    )

    if len(partidos) < RACHA_MINIMA:
        return {
            "tipo": "sin_datos",
            "longitud": 0,
            "factor": 1.0,
            "descripcion": "Sin datos suficientes",
        }

    # Ordenar por fecha descendente (más reciente primero)
    partidos_ordenados = sorted(partidos, key=lambda x: x["fecha"] or "", reverse=True)

    # Determinar resultados
    resultados = []  # 'V' = victoria, 'D' = derrota, 'E' = empate
    for p in partidos_ordenados:
        goles_propios = p.get("goles")
        goles_rival = p.get("rival_goles")

        if goles_propios is None or goles_rival is None:
            continue

        if goles_propios > goles_rival:
            resultados.append("V")
        elif goles_propios < goles_rival:
            resultados.append("D")
        else:
            resultados.append("E")

    if len(resultados) < RACHA_MINIMA:
        return {
            "tipo": "sin_datos",
            "longitud": 0,
            "factor": 1.0,
            "descripcion": "Sin resultados suficientes",
        }

    # Contar racha actual (primeros resultados iguales)
    primer_resultado = resultados[0]
    longitud = 1
    for r in resultados[1:]:
        if r == primer_resultado:
            longitud += 1
        else:
            break

    # Clasificar
    if primer_resultado == "V" and longitud >= RACHA_MINIMA:
        factor = 1 + min(longitud * 0.02, AJUSTE_RACHA_MAX)
        return {
            "tipo": "ganadora",
            "longitud": longitud,
            "factor": round(factor, 3),
            "descripcion": f"🔥 {longitud} victorias seguidas (+{(factor-1)*100:.0f}%)",
        }
    elif primer_resultado == "D" and longitud >= RACHA_MINIMA:
        factor = 1 - min(longitud * 0.02, AJUSTE_RACHA_MAX)
        return {
            "tipo": "perdedora",
            "longitud": longitud,
            "factor": round(factor, 3),
            "descripcion": f"❄️ {longitud} derrotas seguidas ({(factor-1)*100:.0f}%)",
        }
    elif primer_resultado == "E" and longitud >= RACHA_MINIMA:
        return {
            "tipo": "empates",
            "longitud": longitud,
            "factor": 0.98,
            "descripcion": f"⚖️ {longitud} empates seguidos",
        }

    # Verificar si está invicto (V + E)
    victorias_empates = 0
    for r in resultados:
        if r == "V" or r == "E":
            victorias_empates += 1
        else:
            break

    if victorias_empates >= 5:
        return {
            "tipo": "invicto",
            "longitud": victorias_empates,
            "factor": 1.03,
            "descripcion": f"✅ {victorias_empates} partidos sin perder (+3%)",
        }

    # Sin ganar (D + E)
    sin_ganar = 0
    for r in resultados:
        if r == "D" or r == "E":
            sin_ganar += 1
        else:
            break

    if sin_ganar >= 5:
        return {
            "tipo": "sin_ganar",
            "longitud": sin_ganar,
            "factor": 0.97,
            "descripcion": f"⚠️ {sin_ganar} partidos sin ganar (-3%)",
        }

    return {
        "tipo": "normal",
        "longitud": 0,
        "factor": 1.0,
        "descripcion": "Sin racha significativa",
    }


# ============================================================
# VENTANAS MÚLTIPLES (5E)
# ============================================================
def calcular_stats_multiples_ventanas(equipo, liga_pronostico=None, como_local=None, fecha_corte=None):
    """
    Calcula estadísticas usando múltiples ventanas temporales y las combina.

    Returns:
        {
            'stats_combinadas': {...},   # promedio ponderado de las ventanas
            'stats_por_ventana': {...},  # detalle de cada ventana
            'ventana_mas_representativa': str,
        }
    """
    resultados = {}
    pesos_totales = 0
    campos_suma = defaultdict(float)

    for nombre_ventana, config in VENTANAS_MULTIPLES.items():
        n = config["n"]
        peso_ventana = config["peso"]

        # Obtener partidos
        partidos = obtener_partidos_historicos(
            equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=n,
            fecha_corte=fecha_corte
        )

        if len(partidos) < 3:
            resultados[nombre_ventana] = {
                "disponible": False,
                "partidos": len(partidos),
                "peso_aplicado": 0,
            }
            continue

        # Calcular stats ponderadas de esta ventana
        stats = calcular_estadisticas_ponderadas(partidos, liga_pronostico)

        if not stats:
            resultados[nombre_ventana] = {
                "disponible": False,
                "partidos": len(partidos),
                "peso_aplicado": 0,
            }
            continue

        # Registrar
        resultados[nombre_ventana] = {
            "disponible": True,
            "partidos": len(partidos),
            "peso_aplicado": peso_ventana,
            "stats": {
                "goles": stats.get("goles"),
                "tiros": stats.get("tiros"),
                "tiros_puerta": stats.get("tiros_puerta"),
                "corners": stats.get("corners"),
                "faltas": stats.get("faltas"),
                "tarjetas_amarillas": stats.get("tarjetas_amarillas"),
            },
        }

        # Sumar ponderado
        campos_clave = [
            "goles",
            "tiros",
            "tiros_puerta",
            "corners",
            "faltas",
            "tarjetas_amarillas",
            "rival_goles",
            "rival_tiros",
            "rival_corners",
            "rival_faltas",
        ]

        for campo in campos_clave:
            val = stats.get(campo)
            if val is not None:
                campos_suma[campo] += val * peso_ventana

        pesos_totales += peso_ventana

    if pesos_totales == 0:
        return None

    # Promedio ponderado
    stats_combinadas = {}
    for campo, suma in campos_suma.items():
        stats_combinadas[campo] = round(suma / pesos_totales, 3)

    # Ventana más representativa (la que tenga más peso y datos)
    ventana_top = None
    mejor_score = 0
    for nombre, info in resultados.items():
        if info.get("disponible"):
            score = info["peso_aplicado"] * info["partidos"]
            if score > mejor_score:
                mejor_score = score
                ventana_top = nombre

    return {
        "stats_combinadas": stats_combinadas,
        "stats_por_ventana": resultados,
        "ventana_mas_representativa": ventana_top,
    }


# ============================================================
# SAMPLE QUALITY SCORE (B.1)
# ============================================================
def calcular_sample_quality_score(equipo, liga_pronostico=None, como_local=None, fecha_corte=None):
    """
    Calcula un score de 0 a 100 que indica qué tan fiable es la muestra
    de datos disponible para un equipo.

    Componentes:
    - Cantidad de partidos (0-30 puntos)
    - Cobertura de datos (0-20 puntos)
    - Cobertura específica local/visitante (0-15 puntos)
    - Consistencia (varianza) (0-15 puntos)
    - H2H disponible (0-10 puntos)
    - Tendencia clara (0-10 puntos)

    Returns:
        {
            'score': int,
            'nivel': 'alta' | 'media' | 'baja',
            'color': str,
            'componentes': {...},
            'factores': [str],   # Explicación de por qué el score es bajo
        }
    """
    # ========== 1. CANTIDAD DE PARTIDOS (0-30) ==========
    partidos = obtener_partidos_historicos(
        equipo, como_local=None, liga_pronostico=liga_pronostico, limite=30, fecha_corte=fecha_corte
    )
    n_partidos = len(partidos)

    if n_partidos >= 15:
        score_partidos = 30
    elif n_partidos >= 10:
        score_partidos = 25
    elif n_partidos >= 5:
        score_partidos = 18
    elif n_partidos >= 3:
        score_partidos = 10
    else:
        score_partidos = 0

    # ========== 2. COBERTURA DE DATOS (0-20) ==========
    stats = calcular_estadisticas_ponderadas(partidos, liga_pronostico)

    cobertura_promedio = 0
    if stats and stats.get("cobertura"):
        campos_clave = ["goles", "tiros", "tiros_puerta", "corners"]
        porcentajes = [
            stats["cobertura"].get(c, {}).get("porcentaje", 0) for c in campos_clave
        ]
        cobertura_promedio = sum(porcentajes) / len(porcentajes) if porcentajes else 0

    score_cobertura = int(cobertura_promedio / 100 * 20)

    # ========== 3. COBERTURA LOCAL/VISITANTE (0-15) ==========
    partidos_condicion = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=15, fecha_corte=fecha_corte
    )
    n_condicion = len(partidos_condicion)

    if n_condicion >= 8:
        score_condicion = 15
    elif n_condicion >= 5:
        score_condicion = 12
    elif n_condicion >= 3:
        score_condicion = 7
    else:
        score_condicion = 2

    # ========== 4. CONSISTENCIA (0-15) ==========
    # Menos varianza = más consistencia
    score_consistencia = 0
    if len(partidos) >= 5:
        goles_list = [p.get("goles") for p in partidos if p.get("goles") is not None]
        if len(goles_list) >= 5:
            media = sum(goles_list) / len(goles_list)
            if media > 0:
                varianza = sum((x - media) ** 2 for x in goles_list) / len(goles_list)
                desv = varianza**0.5
                cv = desv / media  # Coeficiente de variación

                # CV bajo = consistente, CV alto = inconsistente
                if cv < 0.6:
                    score_consistencia = 15
                elif cv < 1.0:
                    score_consistencia = 10
                elif cv < 1.5:
                    score_consistencia = 5
                else:
                    score_consistencia = 2

        # ========== 5. H2H — NO CONTRIBUYE AL SCORE ==========
    # H2H es contexto, no calidad de muestra.
    # Se muestra por separado en la sección "H2H" del pronóstico.
    score_h2h = 0  # No suma

    # ========== 6. TENDENCIA CLARA (0-10) ==========
    tendencia = detectar_tendencia(partidos, campo="goles")
    if tendencia.get("direccion") in ["subiendo", "bajando"]:
        score_tendencia = 10
    elif tendencia.get("direccion") == "estable":
        score_tendencia = 5
    else:
        score_tendencia = 0

    # ========== TOTAL ==========
    score_total = (
        score_partidos
        + score_cobertura
        + score_condicion
        + score_consistencia
        + score_tendencia
    )

    # ========== NIVEL ==========
    if score_total >= 70:
        nivel = "alta"
        color = "#00ff88"
        emoji = "🟢"
    elif score_total >= 45:
        nivel = "media"
        color = "#ffaa00"
        emoji = "🟡"
    else:
        nivel = "baja"
        color = "#ff4455"
        emoji = "🔴"

    # ========== FACTORES ==========
    factores = []
    if score_partidos < 20:
        factores.append(f"Solo {n_partidos} partidos en el histórico")
    if score_cobertura < 15:
        factores.append(f"Cobertura de datos baja ({cobertura_promedio:.0f}%)")
    if score_condicion < 10:
        factores.append(
            f'Solo {n_condicion} partidos como {"local" if como_local else "visitante"}'
        )
    if score_consistencia < 8:
        factores.append("Rendimiento irregular")
    if score_tendencia == 0:
        factores.append("Sin tendencia clara")

    return {
        "score": score_total,
        "nivel": nivel,
        "emoji": emoji,
        "color": color,
        "componentes": {
            "partidos": score_partidos,
            "cobertura": score_cobertura,
            "condicion": score_condicion,
            "consistencia": score_consistencia,
            "tendencia": score_tendencia,
        },
        "detalles": {
            "n_partidos": n_partidos,
            "cobertura_promedio": round(cobertura_promedio, 1),
            "n_condicion": n_condicion,
        },
        "factores": factores,
    }


# ============================================================
# INTERVALOS DE CONFIANZA (B.2)
# ============================================================
def calcular_intervalo_confianza(prob, n_muestras, confidence=0.90):
    """
    Calcula un intervalo de confianza para una probabilidad estimada.
    Usa la aproximación de Wilson (más robusta que la normal).

    IMPORTANTE: El ancho del intervalo está limitado para que sea útil
    incluso con muestras muy pequeñas.
    """
    import math

    # ========== Casos extremos ==========
    if n_muestras < 2 or prob <= 0 or prob >= 1:
        # Sin datos suficientes: intervalo amplio pero limitado
        return (max(0.01, prob - 0.20), min(0.99, prob + 0.20))

    # ========== Wilson Score Interval ==========
    z = 1.645 if confidence == 0.90 else 1.96

    # Fórmula de Wilson
    denominador = 1 + (z**2) / n_muestras
    centro = (prob + (z**2) / (2 * n_muestras)) / denominador
    margen = (
        z * math.sqrt(prob * (1 - prob) / n_muestras + (z**2) / (4 * n_muestras**2))
    ) / denominador

    min_prob = max(0, centro - margen)
    max_prob = min(1, centro + margen)

    # ========== Limitar el ancho máximo ==========
    # Incluso con pocos datos, el intervalo no debe ser mayor a ±25%
    MAX_ANCHO = 0.25

    if (max_prob - min_prob) > (2 * MAX_ANCHO):
        min_prob = max(0, prob - MAX_ANCHO)
        max_prob = min(1, prob + MAX_ANCHO)

    # ========== Limitar mínimo ancho ==========
    # Con muchos datos, no menos de ±1%
    MIN_ANCHO = 0.01
    if (max_prob - min_prob) < (2 * MIN_ANCHO):
        min_prob = max(0, prob - MIN_ANCHO)
        max_prob = min(1, prob + MIN_ANCHO)

    return (round(min_prob, 4), round(max_prob, 4))


# ============================================================
# EDGE AJUSTADO POR INCERTIDUMBRE (B.3)
# ============================================================
def calcular_edge_ajustado(prob, prob_min, prob_max, cuota, n_efectivo):
    """
    Calcula el EV considerando la incertidumbre del modelo.

    Args:
        prob: probabilidad estimada
        prob_min: límite inferior del intervalo
        prob_max: límite superior del intervalo
        cuota: cuota ofrecida por la casa
        n_efectivo: tamaño efectivo de muestra

    Returns:
        {
            'ev_central': float,        # EV con prob central
            'ev_min': float,            # EV con prob mínima (peor caso)
            'ev_max': float,            # EV con prob máxima (mejor caso)
            'edge_ajustado': float,     # EV con incertidumbre penalizada
            'decision': str,            # 'VALUE_FUERTE' | 'VALUE' | 'MARGINAL' | 'NO_BET'
            'razon': str,
        }
    """
    if cuota <= 1 or prob <= 0:
        return None

    # EV con probabilidad central
    ev_central = ((prob * cuota) - 1) * 100

    # EV con probabilidad mínima (peor caso)
    ev_min = ((prob_min * cuota) - 1) * 100

    # EV con probabilidad máxima (mejor caso)
    ev_max = ((prob_max * cuota) - 1) * 100

    # Edge ajustado = EV central - penalización por incertidumbre
    # La penalización depende de la amplitud del intervalo
    amplitud = (prob_max - prob_min) * 100
    penalizacion = amplitud * 0.5

    edge_ajustado = ev_central - penalizacion

    # Penalización adicional si hay pocos datos
    if n_efectivo < 5:
        edge_ajustado -= 3
    elif n_efectivo < 10:
        edge_ajustado -= 1.5

    # ========== DECISIÓN ==========
    if ev_min <= 0:
        decision = "NO_BET"
        razon = f"🔴 NO BET: incluso en el mejor caso (intervalo bajo), el EV es {ev_min:.1f}%"
    elif edge_ajustado >= 5:
        decision = "VALUE_FUERTE"
        razon = f"🟢 VALUE FUERTE: edge ajustado +{edge_ajustado:.1f}%"
    elif edge_ajustado >= 2:
        decision = "VALUE"
        razon = f"🟢 VALUE: edge ajustado +{edge_ajustado:.1f}%"
    elif edge_ajustado >= 0:
        decision = "MARGINAL"
        razon = f"🟡 MARGINAL: edge ajustado +{edge_ajustado:.1f}%"
    else:
        decision = "NO_BET"
        razon = f"🔴 NO BET: edge ajustado {edge_ajustado:.1f}%"

    return {
        "ev_central": round(ev_central, 2),
        "ev_min": round(ev_min, 2),
        "ev_max": round(ev_max, 2),
        "edge_ajustado": round(edge_ajustado, 2),
        "penalizacion": round(penalizacion, 2),
        "decision": decision,
        "razon": razon,
    }


# ============================================================
# N EFECTIVO PONDERADO (P1.4)
# ============================================================
def calcular_n_efectivo(partidos):
    """
    Calcula el tamaño efectivo de muestra, ponderando cada partido por:
    - Recencia (peso exponencial)
    - Competición
    - Cobertura de datos

    Returns:
        {
            'n_fisico': int,              # partidos totales
            'n_efectivo': float,          # muestra efectiva ponderada
            'n_condicion': int,           # partidos en la condición (local/visitante)
            'n_recientes': int,           # partidos en últimos 30 días
            'cobertura_promedio': float,  # % promedio de cobertura
            'pesos': [float],             # peso de cada partido
        }
    """
    if not partidos:
        return {
            "n_fisico": 0,
            "n_efectivo": 0,
            "n_condicion": 0,
            "n_recientes": 0,
            "cobertura_promedio": 0,
            "pesos": [],
        }

    n_fisico = len(partidos)
    pesos = []
    n_recientes = 0
    coberturas = []

    for i, p in enumerate(partidos):
        # ========== 1. Peso por recencia (0.85^índice) ==========
        peso_recencia = FACTOR_DECAY**i

        # ========== 2. Peso por competición ==========
        peso_comp = p.get("peso_competicion", 1.0)

        # ========== 3. Peso por cobertura de datos ==========
        # Si el partido tiene menos campos, vale menos
        campos_clave = ["goles", "tiros", "tiros_puerta", "corners", "faltas"]
        campos_presentes = sum(1 for c in campos_clave if p.get(c) is not None)
        peso_cobertura = campos_presentes / len(campos_clave)
        coberturas.append(peso_cobertura)

        # ========== 4. Peso por antigüedad (30 días) ==========
        dias = p.get("dias_atras", 999)
        if dias <= 30:
            n_recientes += 1

        # ========== Peso final ==========
        peso_final = peso_recencia * peso_comp * peso_cobertura
        pesos.append(peso_final)

    n_efectivo = sum(pesos)
    cobertura_promedio = sum(coberturas) / len(coberturas) if coberturas else 0

    # n_condicion se calcula afuera (porque depende de cómo llamamos)
    return {
        "n_fisico": n_fisico,
        "n_efectivo": round(n_efectivo, 2),
        "n_recientes": n_recientes,
        "cobertura_promedio": round(cobertura_promedio * 100, 1),
        "pesos": [round(p, 3) for p in pesos],
    }


def calcular_n_efectivo_por_condicion(
    equipo, como_local, liga_pronostico=None, limite=15, fecha_corte=None
):
    """
    Calcula el N efectivo para un equipo en una condición específica.
    Combina:
    - Partidos en la condición (peso alto)
    - Partidos en la otra condición (peso bajo, solo si hay pocos)
    """
    # Partidos en la condición correcta
    partidos_condicion = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=limite, fecha_corte=fecha_corte
    )
    n_cond = calcular_n_efectivo(partidos_condicion)
    n_cond["n_condicion"] = len(partidos_condicion)

    # Partidos en la otra condición (complemento)
    partidos_opuestos = obtener_partidos_historicos(
        equipo,
        como_local=(not como_local),
        liga_pronostico=liga_pronostico,
        limite=limite,
        fecha_corte=fecha_corte
    )
    n_op = calcular_n_efectivo(partidos_opuestos)

    # N efectivo combinado:
    # - 100% del n_condicion
    # - 40% del n_opuesto (menos peso porque es diferente condición)
    n_combinado = n_cond["n_efectivo"] + (n_op["n_efectivo"] * 0.4)

    return {
        "n_condicion": n_cond["n_fisico"],
        "n_efectivo_condicion": n_cond["n_efectivo"],
        "n_total": n_cond["n_fisico"] + n_op["n_fisico"],
        "n_efectivo_total": round(n_combinado, 2),
        "n_recientes": n_cond["n_recientes"] + n_op["n_recientes"],
        "cobertura_promedio": n_cond["cobertura_promedio"],
    }


# ============================================================
# DISTRIBUCIONES Y PERCENTILES (P3.1)
# ============================================================
def calcular_distribucion(valores):
    """
    Calcula estadísticas de distribución para una lista de valores.
    Ignora None.
    """
    import statistics

    valores_validos = [v for v in valores if v is not None]

    if not valores_validos:
        return {
            "n": 0,
            "media": None,
            "mediana": None,
            "desviacion": None,
            "varianza": None,
            "cv": None,
            "min": None,
            "max": None,
            "rango": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p90": None,
        }

    n = len(valores_validos)

    media = statistics.mean(valores_validos)

    if n >= 2:
        desviacion = statistics.stdev(valores_validos)
        varianza = statistics.variance(valores_validos)
        cv = desviacion / media if media > 0 else None
    else:
        desviacion = 0
        varianza = 0
        cv = 0

    mediana = statistics.median(valores_validos)

    def percentil(data, p):
        if not data:
            return None
        data_ord = sorted(data)
        k = (len(data_ord) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(data_ord) else f
        if f == c:
            return data_ord[f]
        d0 = data_ord[f] * (c - k)
        d1 = data_ord[c] * (k - f)
        return d0 + d1

    return {
        "n": n,
        "media": round(media, 3),
        "mediana": round(mediana, 3),
        "desviacion": round(desviacion, 3),
        "varianza": round(varianza, 3),
        "cv": round(cv, 3) if cv is not None else None,
        "min": round(min(valores_validos), 3),
        "max": round(max(valores_validos), 3),
        "rango": round(max(valores_validos) - min(valores_validos), 3),
        "p25": round(percentil(valores_validos, 25), 3),
        "p50": round(percentil(valores_validos, 50), 3),
        "p75": round(percentil(valores_validos, 75), 3),
        "p90": round(percentil(valores_validos, 90), 3),
    }


# ============================================================
# HIT RATES POR LÍNEA (P3.2)
# ============================================================
def calcular_hit_rates(valores, lineas):
    """
    Calcula el % de veces que un valor superó cada línea.
    """
    valores_validos = [v for v in valores if v is not None]
    n = len(valores_validos)

    if n == 0:
        return {
            "n": 0,
            "over": {l: None for l in lineas},
            "under": {l: None for l in lineas},
        }

    over = {}
    under = {}

    for linea in lineas:
        over_count = sum(1 for v in valores_validos if v > linea)
        under_count = n - over_count
        over[linea] = round(over_count / n, 4)
        under[linea] = round(under_count / n, 4)

    return {
        "n": n,
        "over": over,
        "under": under,
    }


# ============================================================
# DISTRIBUCIÓN COMPLETA DE UN EQUIPO (P3)
# ============================================================
def calcular_distribucion_equipo(
    equipo, liga_pronostico=None, como_local=None, limite=15, fecha_corte=None
):
    """
    Calcula la distribución completa de un equipo para todas las métricas clave.
    """
    partidos = obtener_partidos_historicos(
        equipo, como_local=como_local, liga_pronostico=liga_pronostico, limite=limite, fecha_corte=fecha_corte
    )

    if not partidos:
        return None

    metricas = {
        "goles": "goles",
        "tiros": "tiros",
        "tiros_puerta": "tiros_puerta",
        "corners": "corners",
        "faltas": "faltas",
        "tarjetas_amarillas": "tarjetas_amarillas",
        "rival_goles": "rival_goles",
        "rival_tiros": "rival_tiros",
        "rival_corners": "rival_corners",
    }

    resultado = {}

    for nombre, campo in metricas.items():
        valores = [p.get(campo) for p in partidos if p.get(campo) is not None]
        resultado[nombre] = calcular_distribucion(valores)

    goles_list = [p.get("goles") for p in partidos if p.get("goles") is not None]
    corners_list = [p.get("corners") for p in partidos if p.get("corners") is not None]
    tarjetas_list = [
        p.get("tarjetas_amarillas")
        for p in partidos
        if p.get("tarjetas_amarillas") is not None
    ]

    hit_rates = {
        "goles": calcular_hit_rates(goles_list, [0.5, 1.5, 2.5, 3.5, 4.5]),
        "corners": calcular_hit_rates(corners_list, [4.5, 5.5, 6.5, 7.5, 8.5]),
        "tarjetas_amarillas": calcular_hit_rates(tarjetas_list, [0.5, 1.5, 2.5, 3.5]),
    }

    return {
        "partidos": len(partidos),
        "metricas": resultado,
        "hit_rates": hit_rates,
    }


# ============================================================
# DETECCIÓN DE ANOMALÍAS (P3.5)
# ============================================================
def detectar_anomalias(
    mercados_poisson, dist_local, dist_visit, umbral_moderado=0.10, umbral_alto=0.20
):
    """
    Compara las probabilidades del modelo Poisson con los hit rates históricos.
    Detecta anomalías importantes.

    Args:
        mercados_poisson: dict de mercados calculados por Poisson
        dist_local: distribución del equipo local
        dist_visit: distribución del equipo visitante
        umbral_moderado: diferencia para alerta moderada (default 10%)
        umbral_alto: diferencia para alerta alta (default 20%)

    Returns:
        {
            'anomalias': [ {mercado, poisson, historico, diferencia, nivel, mensaje}, ... ],
            'total_anomalias': int,
            'nivel_global': 'normal' | 'moderado' | 'alto',
        }
    """
    anomalias = []

    # ========== Verificar datos suficientes ==========
    if not dist_local or not dist_visit:
        return {
            "anomalias": [],
            "total_anomalias": 0,
            "nivel_global": "sin_datos",
        }

    n_local = dist_local.get("partidos", 0)
    n_visit = dist_visit.get("partidos", 0)

    if n_local < 5 or n_visit < 5:
        return {
            "anomalias": [],
            "total_anomalias": 0,
            "nivel_global": "pocos_datos",
            "mensaje": f"Pocos datos para comparar (local: {n_local}, visitante: {n_visit}, mínimo: 5)",
        }

    # ========== Comparaciones ==========

    # --- Over/Under de goles ---
    hit_rates_goles_local = dist_local.get("hit_rates", {}).get("goles", {})
    hit_rates_goles_visit = dist_visit.get("hit_rates", {}).get("goles", {})

    if "over" in mercados_poisson and hit_rates_goles_local.get("n", 0) >= 5:
        for linea, prob_poisson in mercados_poisson["over"].items():
            # Convertir línea a string para buscar en hit rates
            linea_key = str(linea)
            if linea_key in hit_rates_goles_local.get("over", {}):
                hit_local = hit_rates_goles_local["over"][linea_key]
                if hit_local is not None:
                    # Comparar con la suma del local y visitante sería ideal, pero
                    # por simplicidad comparamos con el total esperado
                    # (Esto es una aproximación)
                    diferencia = prob_poisson - hit_local
                    diff_abs = abs(diferencia)

                    if diff_abs >= umbral_alto:
                        nivel = "alto"
                    elif diff_abs >= umbral_moderado:
                        nivel = "moderado"
                    else:
                        continue

                    tipo = "sobreestima" if diferencia > 0 else "subestima"

                    anomalias.append(
                        {
                            "mercado": f"Over {linea} goles",
                            "categoria": "goles",
                            "poisson": round(prob_poisson, 4),
                            "historico": round(hit_local, 4),
                            "diferencia": round(diferencia, 4),
                            "nivel": nivel,
                            "tipo": tipo,
                            "mensaje": f"Poisson {tipo} Over {linea} ({prob_poisson*100:.0f}% modelo vs {hit_local*100:.0f}% histórico)",
                            "base": f'{hit_rates_goles_local["n"]} partidos',
                        }
                    )

    # --- Over/Under de córners ---
    hit_rates_corners = dist_local.get("hit_rates", {}).get("corners", {})
    if hit_rates_corners.get("n", 0) >= 5:
        # Comparar Over 8.5, 9.5, 10.5 (típicos)
        # Nota: el modelo actual de córners está en mercados_corners, no en mercados_poisson
        # Por eso esto requiere pasar mercados_corners también
        pass  # Lo dejamos para una futura iteración

    # --- Tarjetas amarillas ---
    hit_rates_ta = dist_local.get("hit_rates", {}).get("tarjetas_amarillas", {})
    if hit_rates_ta.get("n", 0) >= 5:
        # Similar, requiere mercados_tarjetas
        pass

    # ========== Determinar nivel global ==========
    if any(a["nivel"] == "alto" for a in anomalias):
        nivel_global = "alto"
    elif any(a["nivel"] == "moderado" for a in anomalias):
        nivel_global = "moderado"
    else:
        nivel_global = "normal"

    # Ordenar por magnitud de diferencia
    anomalias.sort(key=lambda x: abs(x["diferencia"]), reverse=True)

    return {
        "anomalias": anomalias,
        "total_anomalias": len(anomalias),
        "nivel_global": nivel_global,
    }


def detectar_anomalias_completo(
    mercados_poisson, mercados_corners, mercados_tarjetas, dist_local, dist_visit
):
    """
    Versión completa que compara goles, córners y tarjetas.
    """
    import statistics

    anomalias = []

    # Verificar datos suficientes
    if not dist_local or not dist_visit:
        return {"anomalias": [], "total_anomalias": 0, "nivel_global": "sin_datos"}

    n_min = min(dist_local.get("partidos", 0), dist_visit.get("partidos", 0))
    if n_min < 5:
        return {
            "anomalias": [],
            "total_anomalias": 0,
            "nivel_global": "pocos_datos",
            "mensaje": f"Pocos datos (mínimo: 5 partidos, actual: {n_min})",
        }

    umbral_moderado = 0.10
    umbral_alto = 0.20

    def agregar_anomalia(mercado, categoria, prob_poisson, hit_historico, n):
        if hit_historico is None or prob_poisson is None:
            return
        diferencia = prob_poisson - hit_historico
        diff_abs = abs(diferencia)

        if diff_abs >= umbral_alto:
            nivel = "alto"
        elif diff_abs >= umbral_moderado:
            nivel = "moderado"
        else:
            return

        tipo = "sobreestima" if diferencia > 0 else "subestima"

        anomalias.append(
            {
                "mercado": mercado,
                "categoria": categoria,
                "poisson": round(prob_poisson, 4),
                "historico": round(hit_historico, 4),
                "diferencia": round(diferencia, 4),
                "nivel": nivel,
                "tipo": tipo,
                "mensaje": f"{mercado}: Modelo {prob_poisson*100:.0f}% vs Histórico {hit_historico*100:.0f}% ({tipo})",
                "base": f"{n} partidos",
            }
        )

    # ========== GOLES ==========
    if mercados_poisson:
        # Comparamos con la suma del local como proxy
        # El hit rate de goles totales = goles_local + goles_visitante (aproximación)
        hit_goles_local = dist_local.get("hit_rates", {}).get("goles", {})
        hit_goles_visit = dist_visit.get("hit_rates", {}).get("goles", {})

        if "over" in mercados_poisson:
            for linea, prob_poisson in mercados_poisson["over"].items():
                linea_key = str(linea)

                # Promedio de hit rates entre local y visitante
                h_l = hit_goles_local.get("over", {}).get(linea_key)
                h_v = hit_goles_visit.get("over", {}).get(linea_key)

                if h_l is not None and h_v is not None:
                    h_avg = (h_l + h_v) / 2
                    agregar_anomalia(
                        f"Over {linea} goles",
                        "goles",
                        prob_poisson,
                        h_avg,
                        hit_goles_local.get("n", 0),
                    )

    # ========== CÓRNERS ==========
    if mercados_corners and mercados_corners.get("over"):
        hit_corners = dist_local.get("hit_rates", {}).get("corners", {})
        n_corners = hit_corners.get("n", 0)

        if n_corners >= 5:
            for linea, prob_poisson in mercados_corners["over"].items():
                linea_key = str(linea)
                hit_local = hit_corners.get("over", {}).get(linea_key)

                if hit_local is not None:
                    # Ajustar: la poisson es del total, el hit rate es del local
                    # Hacemos una comparación aproximada
                    # (El local suele tener ~50% de los córners totales)
                    prob_local_aprox = prob_poisson * 0.5
                    agregar_anomalia(
                        f"Over {linea} córners (local)",
                        "corners",
                        prob_local_aprox,
                        hit_local,
                        n_corners,
                    )

    # ========== TARJETAS ==========
    if mercados_tarjetas and mercados_tarjetas.get("over"):
        hit_tarjetas = dist_local.get("hit_rates", {}).get("tarjetas_amarillas", {})
        n_tarjetas = hit_tarjetas.get("n", 0)

        if n_tarjetas >= 5:
            for linea, prob_poisson in mercados_tarjetas["over"].items():
                linea_key = str(linea)
                hit_local = hit_tarjetas.get("over", {}).get(linea_key)

                if hit_local is not None:
                    prob_local_aprox = prob_poisson * 0.5
                    agregar_anomalia(
                        f"Over {linea} tarjetas (local)",
                        "tarjetas",
                        prob_local_aprox,
                        hit_local,
                        n_tarjetas,
                    )

    # ========== Nivel global ==========
    if any(a["nivel"] == "alto" for a in anomalias):
        nivel_global = "alto"
    elif any(a["nivel"] == "moderado" for a in anomalias):
        nivel_global = "moderado"
    else:
        nivel_global = "normal"

    # Ordenar
    anomalias.sort(key=lambda x: abs(x["diferencia"]), reverse=True)

    return {
        "anomalias": anomalias,
        "total_anomalias": len(anomalias),
        "nivel_global": nivel_global,
        "n_min": n_min,
    }


# ============================================================
# MÉTRICAS DE BACKTESTING PROFESIONAL (P4)
# ============================================================
def calcular_brier_score(predicciones):
    """
    Calcula el Brier Score.

    Brier = promedio de (prob_predicha - resultado_real)^2

    Menor es mejor. Rango: 0 (perfecto) a 1 (peor).

    Args:
        predicciones: lista de dicts con 'prob' y 'resultado' (0 o 1)
    """
    if not predicciones:
        return None

    suma = 0
    for p in predicciones:
        prob = p.get("prob")
        resultado = p.get("resultado")
        if prob is None or resultado is None:
            continue
        suma += (prob - resultado) ** 2

    return round(suma / len(predicciones), 4)


def calcular_log_loss(predicciones):
    """
    Calcula el Log Loss (Cross-Entropy).

    Penaliza más las confianzas erróneas.

    Args:
        predicciones: lista de dicts con 'prob' y 'resultado' (0 o 1)
    """
    import math

    if not predicciones:
        return None

    suma = 0
    n = 0
    for p in predicciones:
        prob = p.get("prob")
        resultado = p.get("resultado")
        if prob is None or resultado is None:
            continue

        # Clipping para evitar log(0)
        prob = max(0.001, min(0.999, prob))

        if resultado == 1:
            suma -= math.log(prob)
        else:
            suma -= math.log(1 - prob)
        n += 1

    return round(suma / n, 4) if n > 0 else None


def calcular_mae_goles(predicciones):
    """
    Calcula el MAE (Mean Absolute Error) para goles.

    Args:
        predicciones: lista de dicts con 'lambda' y 'goles_reales'
    """
    if not predicciones:
        return None

    suma = 0
    n = 0
    for p in predicciones:
        lam = p.get("lambda")
        real = p.get("goles_reales")
        if lam is None or real is None:
            continue
        suma += abs(lam - real)
        n += 1

    return round(suma / n, 4) if n > 0 else None


def calcular_rmse_goles(predicciones):
    """
    Calcula el RMSE (Root Mean Squared Error) para goles.
    """
    import math

    if not predicciones:
        return None

    suma = 0
    n = 0
    for p in predicciones:
        lam = p.get("lambda")
        real = p.get("goles_reales")
        if lam is None or real is None:
            continue
        suma += (lam - real) ** 2
        n += 1

    if n == 0:
        return None

    return round(math.sqrt(suma / n), 4)


def calcular_calibracion_avanzada(predicciones, n_bins=10):
    """
    Calcula la curva de calibración.

    Divide las probabilidades en bins y compara:
    - Probabilidad promedio predicha
    - Frecuencia real observada

    Args:
        predicciones: lista de dicts con 'prob' y 'resultado' (0 o 1)
        n_bins: número de bins (default 10)
    """
    if not predicciones:
        return []

    # Inicializar bins
    bins = [[] for _ in range(n_bins)]

    for p in predicciones:
        prob = p.get("prob")
        resultado = p.get("resultado")
        if prob is None or resultado is None:
            continue

        # Determinar bin
        bin_idx = min(int(prob * n_bins), n_bins - 1)
        bins[bin_idx].append({"prob": prob, "resultado": resultado})

    # Calcular estadísticas por bin
    resultado_bins = []
    for i, bin_data in enumerate(bins):
        if not bin_data:
            continue

        prob_promedio = sum(b["prob"] for b in bin_data) / len(bin_data)
        frecuencia_real = sum(b["resultado"] for b in bin_data) / len(bin_data)
        diferencia = frecuencia_real - prob_promedio

        resultado_bins.append(
            {
                "bin": f"{i*10}-{(i+1)*10}%",
                "n": len(bin_data),
                "prob_promedio": round(prob_promedio, 4),
                "frecuencia_real": round(frecuencia_real, 4),
                "diferencia": round(diferencia, 4),
            }
        )

    return resultado_bins


def calcular_roi_avanzado(apuestas):
    """
    Calcula métricas económicas avanzadas.

    Args:
        apuestas: lista de dicts con:
            - 'stake' (cantidad apostada)
            - 'cuota' (cuota tomada)
            - 'ganada' (True/False)

    Returns:
        {
            'total_apuestas': int,
            'stake_total': float,
            'profit_total': float,
            'roi': float,          # profit / stake_total * 100
            'yield': float,        # igual que ROI en apuestas unitarias
            'drawdown_max': float, # máxima caída desde un pico
            'bankroll_final': float,
        }
    """
    if not apuestas:
        return None

    stake_total = 0
    profit_total = 0
    bankroll = 0
    bankroll_pico = 0
    drawdown_max = 0

    for a in apuestas:
        stake = a.get("stake", 1)
        cuota = a.get("cuota", 0)
        ganada = a.get("ganada", False)

        stake_total += stake

        if ganada:
            profit = stake * (cuota - 1)
        else:
            profit = -stake

        profit_total += profit
        bankroll += profit

        # Actualizar drawdown
        if bankroll > bankroll_pico:
            bankroll_pico = bankroll
        dd = bankroll_pico - bankroll
        if dd > drawdown_max:
            drawdown_max = dd

    roi = (profit_total / stake_total * 100) if stake_total > 0 else 0

    return {
        "total_apuestas": len(apuestas),
        "stake_total": round(stake_total, 2),
        "profit_total": round(profit_total, 2),
        "roi": round(roi, 2),
        "yield": round(roi, 2),  # Igual si stake = 1
        "drawdown_max": round(drawdown_max, 2),
        "bankroll_final": round(bankroll, 2),
    }


# ============================================================
# KELLY CRITERION (11.3)
# ============================================================
def calcular_kelly(prob, cuota, fraccion=0.25, bankroll=1.0, cap_max=0.20):
    """
    Calcula el stake óptimo usando el Criterio de Kelly fraccionado.

    Args:
        prob: probabilidad estimada de ganar (0 a 1)
        cuota: cuota decimal ofrecida por la casa (ej: 2.50)
        fraccion: fracción de Kelly a aplicar
                  1.0 = Kelly completo
                  0.5 = 1/2 Kelly
                  0.25 = 1/4 Kelly (recomendado)
                  0.125 = 1/8 Kelly (conservador)
        bankroll: capital total disponible (para calcular stake en dinero)
        cap_max: límite máximo del stake como fracción del bankroll (por defecto 20%)

    Returns:
        {
            'kelly_completo': float,        # f* sin fraccionar (puede ser negativo)
            'kelly_fraccionado': float,     # f* × fraccion, limitado a [0, cap_max]
            'stake_pct': float,             # % del bankroll a apostar (0 a cap_max)
            'stake_dinero': float,          # cantidad en dinero según bankroll
            'b': float,                     # cuota - 1
            'es_value': bool,               # True si Kelly > 0
            'recomendacion': str,           # 'VALUE' | 'NO_BET' | 'MARGINAL'
            'razon': str,                   # Explicación legible
        }
    """
    import math

    # ========== Validaciones ==========
    if prob is None or cuota is None:
        return None
    if cuota <= 1.0:
        return None
    if prob <= 0 or prob >= 1:
        # Probabilidad fuera de rango razonable
        if prob <= 0:
            return {
                "kelly_completo": 0.0,
                "kelly_fraccionado": 0.0,
                "stake_pct": 0.0,
                "stake_dinero": 0.0,
                "b": round(cuota - 1, 4),
                "es_value": False,
                "recomendacion": "NO_BET",
                "razon": "Probabilidad estimada fuera de rango (0)",
            }
        prob = 0.999  # clamp para evitar división por 0

    # ========== Cálculo de Kelly ==========
    b = cuota - 1.0  # ganancia neta por unidad apostada
    p = prob  # probabilidad de ganar
    q = 1.0 - p  # probabilidad de perder

    # Fórmula de Kelly: f* = (b·p - q) / b
    kelly_completo = (b * p - q) / b

    # Kelly fraccionado
    kelly_fraccionado = kelly_completo * fraccion

    # ========== Cap y clamping ==========
    # No apostar más del cap_max del bankroll
    kelly_fraccionado_capped = max(0.0, min(kelly_fraccionado, cap_max))

    stake_pct = kelly_fraccionado_capped
    stake_dinero = bankroll * stake_pct

    # ========== Determinar si es value ==========
    es_value = kelly_completo > 0

    # ========== Recomendación cualitativa ==========
    if kelly_completo <= 0:
        recomendacion = "NO_BET"
        razon = f"Kelly negativo ({kelly_completo*100:.2f}%): la cuota no compensa el riesgo"
    elif kelly_completo < 0.02:
        recomendacion = "MARGINAL"
        razon = f"Kelly muy bajo ({kelly_completo*100:.2f}%): edge pequeño, apostar con cautela"
    elif kelly_completo < 0.05:
        recomendacion = "VALUE"
        razon = f"Kelly moderado ({kelly_completo*100:.2f}%): value razonable"
    else:
        recomendacion = "VALUE_FUERTE"
        razon = f"Kelly alto ({kelly_completo*100:.2f}%): value fuerte"

    return {
        "kelly_completo": round(kelly_completo, 4),
        "kelly_fraccionado": round(kelly_fraccionado, 4),
        "stake_pct": round(stake_pct, 4),
        "stake_dinero": round(stake_dinero, 2),
        "b": round(b, 4),
        "es_value": es_value,
        "recomendacion": recomendacion,
        "razon": razon,
    }


def calcular_kelly_multiples_fracciones(prob, cuota, bankroll=1.0):
    """
    Calcula Kelly con las 4 fracciones estándar de una sola vez.
    Útil para que el frontend muestre todas las opciones.

    Returns:
        {
            'completo': {...},   # fraccion=1.0
            'medio': {...},      # fraccion=0.5
            'cuarto': {...},     # fraccion=0.25
            'octavo': {...},     # fraccion=0.125
        }
    """
    return {
        "completo": calcular_kelly(prob, cuota, fraccion=1.0, bankroll=bankroll),
        "medio": calcular_kelly(prob, cuota, fraccion=0.5, bankroll=bankroll),
        "cuarto": calcular_kelly(prob, cuota, fraccion=0.25, bankroll=bankroll),
        "octavo": calcular_kelly(prob, cuota, fraccion=0.125, bankroll=bankroll),
    }

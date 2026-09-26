# ============================================================
# backend/rutas_pronosticos.py
# Blueprint: CRUD de pronósticos guardados.
# Endpoints:
#   POST /api/pronosticos/guardar
#   GET  /api/pronosticos/lista
#   GET  /api/pronosticos/<id>
#   POST /api/pronosticos/resultado
#   POST /api/pronosticos/pendientes-para-partido
#   POST /api/pronosticos/vincular-partido
# ============================================================

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime

from backend.db import DB_PATH
from backend.rutas_pronostico import pronosticar_partido


bp_pronosticos = Blueprint('pronosticos', __name__)


# ============================================================
# CONSTRUIR JSON DE MERCADOS REALES
# ============================================================
def construir_resultado_mercados(partido_id=None, goles_local=None, goles_visitante=None):
    """
    Construye el JSON con las métricas reales del partido.
    
    Dos modos:
    - Si partido_id se proporciona → lee estadísticas completas del histórico.
    - Si solo goles_local/goles_visitante → calcula solo mercados de goles.
    
    Devuelve un dict que se serializa como JSON.
    """
    mercados = {
        'goles_local': 0,
        'goles_visitante': 0,
        'btts': 0,
        'over15': 0,
        'over25': 0,
        'over35': 0,
        'over45': 0,
        'under15': 0,
        'under25': 0,
        'under35': 0,
        'local_over15': 0,
        'local_over25': 0,
        'visitante_over15': 0,
        'visitante_over25': 0,
        'doble_1X': 0,
        'doble_12': 0,
        'doble_X2': 0,
        # Córners (solo si hay partido_id)
        'corners_local': None,
        'corners_visitante': None,
        'corners_total': None,
        'corners_over75': None,
        'corners_over85': None,
        'corners_over95': None,
        'corners_over105': None,
        'corners_over115': None,
        # Tarjetas (solo si hay partido_id)
        'tarjetas_amarillas_local': None,
        'tarjetas_amarillas_visitante': None,
        'tarjetas_total': None,
        'tarjetas_over15': None,
        'tarjetas_over25': None,
        'tarjetas_over35': None,
        'tarjetas_over45': None,
        # Goles por jugador (solo si hay partido_id)
        'goles_jugadores': None,
    }
    
    # ========== MODO 1: Con partido_id (histórico completo) ==========
    if partido_id is not None:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            # Goles del partido
            c.execute('SELECT SUM(G) FROM estadisticas_local WHERE partido_id = ?', (partido_id,))
            gl = c.fetchone()[0] or 0
            c.execute('SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = ?', (partido_id,))
            gv = c.fetchone()[0] or 0
            
            # OG (Filosofía C: suman al rival)
            c.execute('SELECT COALESCE(og_local, 0), COALESCE(og_visitante, 0) FROM partidos WHERE id = ?', (partido_id,))
            og_row = c.fetchone()
            og_local = og_row[0] if og_row else 0
            og_visitante = og_row[1] if og_row else 0
            
            # Aplicar filosofía C
            gl_real = gl + og_visitante
            gv_real = gv + og_local
            
            goles_local = gl_real
            goles_visitante = gv_real
            
            # Córners
            c.execute('SELECT SUM(Crn) FROM estadisticas_local WHERE partido_id = ?', (partido_id,))
            corners_local = c.fetchone()[0] or 0
            c.execute('SELECT SUM(Crn) FROM estadisticas_visitante WHERE partido_id = ?', (partido_id,))
            corners_visit = c.fetchone()[0] or 0
            corners_total = corners_local + corners_visit
            
            mercados['corners_local'] = corners_local
            mercados['corners_visitante'] = corners_visit
            mercados['corners_total'] = corners_total
            mercados['corners_over75'] = 1 if corners_total > 7.5 else 0
            mercados['corners_over85'] = 1 if corners_total > 8.5 else 0
            mercados['corners_over95'] = 1 if corners_total > 9.5 else 0
            mercados['corners_over105'] = 1 if corners_total > 10.5 else 0
            mercados['corners_over115'] = 1 if corners_total > 11.5 else 0
            
            # Tarjetas (TA + TR×2)
            c.execute('''
                SELECT COALESCE(SUM(TA), 0), COALESCE(SUM(TR), 0) 
                FROM estadisticas_local WHERE partido_id = ?
            ''', (partido_id,))
            ta_l, tr_l = c.fetchone()
            c.execute('''
                SELECT COALESCE(SUM(TA), 0), COALESCE(SUM(TR), 0)
                FROM estadisticas_visitante WHERE partido_id = ?
            ''', (partido_id,))
            ta_v, tr_v = c.fetchone()
            
            tarjetas_local = ta_l + (tr_l * 2)
            tarjetas_visit = ta_v + (tr_v * 2)
            tarjetas_total = tarjetas_local + tarjetas_visit
            
            mercados['tarjetas_amarillas_local'] = ta_l
            mercados['tarjetas_amarillas_visitante'] = ta_v
            mercados['tarjetas_total'] = tarjetas_total
            mercados['tarjetas_over15'] = 1 if tarjetas_total > 1.5 else 0
            mercados['tarjetas_over25'] = 1 if tarjetas_total > 2.5 else 0
            mercados['tarjetas_over35'] = 1 if tarjetas_total > 3.5 else 0
            mercados['tarjetas_over45'] = 1 if tarjetas_total > 4.5 else 0
            
            # Goles por jugador
            goles_jug = {'Local': [], 'Visitante': []}
            
            c.execute('''
                SELECT jugador, G FROM estadisticas_local 
                WHERE partido_id = ? AND G > 0
            ''', (partido_id,))
            for nombre, goles in c.fetchall():
                goles_jug['Local'].append({'nombre': nombre, 'goles': goles})
            
            c.execute('''
                SELECT jugador, G FROM estadisticas_visitante 
                WHERE partido_id = ? AND G > 0
            ''', (partido_id,))
            for nombre, goles in c.fetchall():
                goles_jug['Visitante'].append({'nombre': nombre, 'goles': goles})
            
            mercados['goles_jugadores'] = goles_jug
            
        finally:
            conn.close()
    
    # ========== MODO 2: Solo con goles (cierre manual) ==========
    if goles_local is None or goles_visitante is None:
        return mercados
    
    # Goles básicos
    mercados['goles_local'] = goles_local
    mercados['goles_visitante'] = goles_visitante
    
    total_goles = goles_local + goles_visitante
    
    mercados['btts'] = 1 if (goles_local > 0 and goles_visitante > 0) else 0
    mercados['over15'] = 1 if total_goles > 1.5 else 0
    mercados['over25'] = 1 if total_goles > 2.5 else 0
    mercados['over35'] = 1 if total_goles > 3.5 else 0
    mercados['over45'] = 1 if total_goles > 4.5 else 0
    mercados['under15'] = 1 - mercados['over15']
    mercados['under25'] = 1 - mercados['over25']
    mercados['under35'] = 1 - mercados['over35']
    
    mercados['local_over15'] = 1 if goles_local > 1.5 else 0
    mercados['local_over25'] = 1 if goles_local > 2.5 else 0
    mercados['visitante_over15'] = 1 if goles_visitante > 1.5 else 0
    mercados['visitante_over25'] = 1 if goles_visitante > 2.5 else 0
    
    # Doble oportunidad
    if goles_local > goles_visitante:
        mercados['doble_1X'] = 1
        mercados['doble_12'] = 1
        mercados['doble_X2'] = 0
    elif goles_local < goles_visitante:
        mercados['doble_1X'] = 0
        mercados['doble_12'] = 1
        mercados['doble_X2'] = 1
    else:  # empate
        mercados['doble_1X'] = 1
        mercados['doble_12'] = 0
        mercados['doble_X2'] = 1
    
    return mercados

# ============================================================
# GUARDAR PRONÓSTICO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/guardar', methods=['POST'])
def api_guardar_pronostico():
    """Guarda un pronóstico completo en la BD"""
    data = request.json

    local = data.get('local', '')
    visitante = data.get('visitante', '')
    liga = data.get('liga', '')
    fecha_partido = data.get('fecha_partido', '')
    cuota_real = data.get('cuota_real', 0)
    mercado_principal = data.get('mercado_principal', 'Local')
    pronostico_completo = data.get('pronostico', None)

    # ========== Campos Kelly ==========
    def _to_float(v):
        try:
            return float(v) if v is not None else None
        except (ValueError, TypeError):
            return None

    stake_sugerido = _to_float(data.get('stake_sugerido'))
    kelly_fraccion = _to_float(data.get('kelly_fraccion'))
    bankroll_usado = _to_float(data.get('bankroll_usado'))
    stake_minimo_usado = _to_float(data.get('stake_minimo_usado'))
    
    stake_sugerido = data.get('stake_sugerido', None)
    kelly_fraccion = data.get('kelly_fraccion', None)
    bankroll_usado = data.get('bankroll_usado', None)

    if not local or not visitante:
        return jsonify({'error': 'Faltan equipos'})

    if pronostico_completo and pronostico_completo.get('mercados'):
        resultado = pronostico_completo
    else:
        resultado = pronosticar_partido(local, visitante, liga_pronostico=liga)

    if resultado.get('error'):
        return jsonify({'error': resultado['error']})

    mercados = resultado['mercados']

    # Calcular EV del mercado principal
    ev_principal = None
    if cuota_real > 0:
        prob_principal = 0
        if mercado_principal == 'Local':
            prob_principal = mercados['1X2']['local']
        elif mercado_principal == 'Empate':
            prob_principal = mercados['1X2']['empate']
        elif mercado_principal == 'Visitante':
            prob_principal = mercados['1X2']['visitante']
        elif mercado_principal == 'BTTS':
            prob_principal = mercados['BTTS']
        elif mercado_principal == 'Over25':
            prob_principal = mercados['over'].get(2.5, 0)

        if prob_principal > 0:
            ev_principal = ((prob_principal * cuota_real) - 1) * 100

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO pronosticos (
                fecha_pronostico, partido_local, partido_visitante, liga, fecha_partido,
                motor_version, lambda_local, lambda_visitante,
                prob_local, prob_empate, prob_visitante, prob_btts, prob_over25,
                mercado_principal, cuota_real, ev_principal,
                pronostico_json, cerrado,
                stake_sugerido, kelly_fraccion, bankroll_usado, stake_minimo_usado,
                lambda_local_pred, lambda_visitante_pred
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            local, visitante, liga, fecha_partido,
            resultado.get('version_motor', 'v2.0'),
            resultado['lambdas']['local'],
            resultado['lambdas']['visitante'],
            mercados['1X2']['local'],
            mercados['1X2']['empate'],
            mercados['1X2']['visitante'],
            mercados['BTTS'],
            mercados['over'].get(2.5, 0),
            mercado_principal,
            cuota_real,
            ev_principal,
            json.dumps(resultado, ensure_ascii=False),
            stake_sugerido,
            kelly_fraccion,
            bankroll_usado,
            stake_minimo_usado,
            resultado['lambdas']['local'],
            resultado['lambdas']['visitante'],
        ))
        
        pronostico_id = c.lastrowid
        conn.commit()
        return jsonify({'success': True, 'id': pronostico_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# LISTA DE PRONÓSTICOS
# ============================================================
@bp_pronosticos.route('/api/pronosticos/lista')
def api_lista_pronosticos():
    """Lista todos los pronósticos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT id, fecha_pronostico, partido_local, partido_visitante, liga, fecha_partido,
                   motor_version, prob_local, prob_empate, prob_visitante, prob_btts, prob_over25,
                   mercado_principal, cuota_real, ev_principal, cerrado,
                   resultado_local, resultado_visitante, resultado_btts, resultado_over25,
                   partido_id,
                   stake_sugerido, kelly_fraccion, bankroll_usado, stake_minimo_usado,
                   COALESCE(automatico, 0) as automatico
            FROM pronosticos
            ORDER BY fecha_pronostico DESC
            LIMIT 200
        ''')

        pronosticos = []
        for row in c.fetchall():
            pronosticos.append({
                'id': row[0],
                'fecha_pronostico': row[1],
                'local': row[2],
                'visitante': row[3],
                'liga': row[4],
                'fecha_partido': row[5],
                'motor': row[6],
                'prob_local': row[7],
                'prob_empate': row[8],
                'prob_visitante': row[9],
                'prob_btts': row[10],
                'prob_over25': row[11],
                'mercado_principal': row[12],
                'cuota_real': row[13],
                'ev_principal': row[14],
                'cerrado': row[15],
                'resultado_local': row[16],
                'resultado_visitante': row[17],
                'resultado_btts': row[18],
                'resultado_over25': row[19],
                'partido_id': row[20],
                'stake_sugerido': row[21],
                'kelly_fraccion': row[22],
                'bankroll_usado': row[23],
                'stake_minimo_usado': row[24],
                'automatico': row[25],
            })
        return jsonify(pronosticos)
    finally:
        conn.close()


# ============================================================
# OBTENER UN PRONÓSTICO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/<int:pronostico_id>')
def api_obtener_pronostico(pronostico_id):
    """Obtiene un pronóstico completo"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM pronosticos WHERE id = ?', (pronostico_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Pronóstico no encontrado'})

        resultado = dict(row)
        if resultado.get('pronostico_json'):
            try:
                resultado['pronostico_completo'] = json.loads(resultado['pronostico_json'])
            except Exception:
                resultado['pronostico_completo'] = None

        return jsonify(resultado)
    finally:
        conn.close()


# ============================================================
# REGISTRAR RESULTADO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/resultado', methods=['POST'])
def api_registrar_resultado():
    """Registra el resultado real de un pronóstico (solo goles)"""
    data = request.json
    pronostico_id = data.get('id')
    goles_local = data.get('goles_local')
    goles_visitante = data.get('goles_visitante')
    partido_id = data.get('partido_id')

    if pronostico_id is None or goles_local is None or goles_visitante is None:
        return jsonify({'error': 'Faltan datos'})

    btts = 1 if (goles_local > 0 and goles_visitante > 0) else 0
    over25 = 1 if (goles_local + goles_visitante) > 2.5 else 0

    # ========== NUEVO: JSON de mercados ==========
    mercados_json = construir_resultado_mercados(
        partido_id=partido_id if partido_id else None,
        goles_local=goles_local,
        goles_visitante=goles_visitante
    )
    mercados_json_str = json.dumps(mercados_json, ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE pronosticos
            SET resultado_local = ?, resultado_visitante = ?,
                resultado_btts = ?, resultado_over25 = ?,
                cerrado = 1, fecha_cierre = ?,
                partido_id = COALESCE(?, partido_id),
                resultado_mercados_json = ?
            WHERE id = ?
        ''', (goles_local, goles_visitante, btts, over25,
              datetime.now().isoformat(), partido_id, mercados_json_str, pronostico_id))

        conn.commit()
        try:
            from database.aprendizaje import recalcular_aprendizaje_completo
            recalcular_aprendizaje_completo()
        except Exception as e:
            print(f"[APRENDIZAJE] Error recalculando: {e}")
            
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# PRONÓSTICOS PENDIENTES PARA UN PARTIDO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/pendientes-para-partido', methods=['POST'])
def api_pronosticos_pendientes():
    """
    Busca pronósticos abiertos que coincidan con un partido recién guardado.
    """
    data = request.json
    local = data.get('local', '')
    visitante = data.get('visitante', '')
    fecha = data.get('fecha', '')

    if not local or not visitante:
        return jsonify({'error': 'Faltan equipos'})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT id, fecha_pronostico, partido_local, partido_visitante,
                   fecha_partido, prob_local, prob_empate, prob_visitante,
                   prob_btts, prob_over25
            FROM pronosticos
            WHERE cerrado = 0
              AND partido_local = ?
              AND partido_visitante = ?
              AND (
                  fecha_partido = ?
                  OR fecha_partido IS NULL
                  OR fecha_partido = ''
                  OR ABS(julianday(fecha_partido) - julianday(?)) <= 5
              )
            ORDER BY fecha_pronostico DESC
        ''', (local, visitante, fecha, fecha))

        pendientes = []
        for row in c.fetchall():
            pendientes.append({
                'id': row[0],
                'fecha_pronostico': row[1],
                'local': row[2],
                'visitante': row[3],
                'fecha_partido': row[4],
                'prob_local': row[5],
                'prob_empate': row[6],
                'prob_visitante': row[7],
                'prob_btts': row[8],
                'prob_over25': row[9]
            })

        return jsonify(pendientes)
    finally:
        conn.close()


# ============================================================
# VINCULAR PRONÓSTICO A PARTIDO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/vincular-partido', methods=['POST'])
def api_vincular_partido():
    """
    Vincula un pronóstico a un partido y cierra el pronóstico automáticamente.
    Calcula los goles desde las estadísticas del partido.
    Guarda también el JSON completo de mercados reales.
    """
    data = request.json
    pronostico_id = data.get('pronostico_id')
    partido_id = data.get('partido_id')

    if not pronostico_id or not partido_id:
        return jsonify({'error': 'Faltan IDs'})

    # Construir JSON de mercados con todos los datos del partido
    mercados_json = construir_resultado_mercados(partido_id=partido_id)
    mercados_json_str = json.dumps(mercados_json, ensure_ascii=False)

    goles_local = mercados_json['goles_local']
    goles_visitante = mercados_json['goles_visitante']
    btts = mercados_json['btts']
    over25 = mercados_json['over25']

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE pronosticos
            SET resultado_local = ?, resultado_visitante = ?,
                resultado_btts = ?, resultado_over25 = ?,
                cerrado = 1, fecha_cierre = ?,
                partido_id = ?,
                resultado_mercados_json = ?
            WHERE id = ?
        ''', (goles_local, goles_visitante, btts, over25,
              datetime.now().isoformat(), partido_id,
              mercados_json_str, pronostico_id))

        conn.commit()
        
        try:
            from database.aprendizaje import recalcular_aprendizaje_completo
            recalcular_aprendizaje_completo()
        except Exception as e:
            print(f"[APRENDIZAJE] Error recalculando: {e}")
            
        return jsonify({
            'success': True,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()

def cerrar_con_api_logica(limite=10, dias_atras=7):
    """
    Lógica pura de cierre automático con API.
    Llamable desde el endpoint o desde el hilo de fondo.
    """
    from backend.api_football import buscar_partido_por_equipos
    from database.aliases_equipos import normalizar_equipo
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    cerrados = []
    no_encontrados = []
    errores = []
    
    try:
        c.execute('''
            SELECT id, partido_local, partido_visitante, fecha_partido, fecha_pronostico,
                   cuota_real, mercado_principal
            FROM pronosticos
            WHERE cerrado = 0
            ORDER BY fecha_pronostico DESC
            LIMIT ?
        ''', (limite,))
        
        pronosticos_abiertos = c.fetchall()
        
        for row in pronosticos_abiertos:
            pid = row[0]
            local = row[1]
            visitante = row[2]
            fecha_partido = row[3]
            
            local_norm = normalizar_equipo(local)
            visitante_norm = normalizar_equipo(visitante)
            
            try:
                result = buscar_partido_por_equipos(local_norm, visitante_norm, fecha_partido)
            except Exception as e:
                errores.append({'id': pid, 'error': str(e)})
                continue
            
            if not result.get('encontrado'):
                no_encontrados.append({'id': pid, 'razon': 'No encontrado'})
                continue
            
            partido_api = result['partido']
            estado = partido_api.get('estado', '')
            
            ESTADOS_TERMINADOS = {'FINISHED'}
            ESTADOS_EN_JUEGO = {'IN_PLAY', 'PAUSED', 'LIVE'}
            
            if estado not in ESTADOS_TERMINADOS and estado not in ESTADOS_EN_JUEGO:
                no_encontrados.append({'id': pid, 'razon': f'Estado: {estado}'})
                continue
            
            goles_local = partido_api.get('goles_local')
            goles_visitante = partido_api.get('goles_visitante')
            
            if goles_local is None or goles_visitante is None:
                errores.append({'id': pid, 'error': 'Sin marcador'})
                continue
            
            btts = 1 if (goles_local > 0 and goles_visitante > 0) else 0
            over25 = 1 if (goles_local + goles_visitante) > 2.5 else 0
            
            mercados_json = construir_resultado_mercados(
                partido_id=None,
                goles_local=goles_local,
                goles_visitante=goles_visitante,
            )
            mercados_json_str = json.dumps(mercados_json, ensure_ascii=False)
            
            c.execute('''
                UPDATE pronosticos
                SET resultado_local = ?, resultado_visitante = ?,
                    resultado_btts = ?, resultado_over25 = ?,
                    cerrado = 1, fecha_cierre = ?,
                    resultado_mercados_json = ?
                WHERE id = ?
            ''', (goles_local, goles_visitante, btts, over25,
                  datetime.now().isoformat(),
                  mercados_json_str, pid))
            
            cerrados.append({
                'id': pid,
                'local': local,
                'visitante': visitante,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'en_juego': estado in ESTADOS_EN_JUEGO,
            })
        
        conn.commit()
        
        # Recalcular aprendizaje si hay nuevos cierres
        if cerrados:
            try:
                from database.aprendizaje import recalcular_aprendizaje_completo
                recalcular_aprendizaje_completo()
                print(f"[AUTO-CIERRE] Aprendizaje recalculado tras {len(cerrados)} cierres")
            except Exception as e:
                print(f"[AUTO-CIERRE] Error recalculando aprendizaje: {e}")
        
        return {
            'cerrados': cerrados,
            'no_encontrados': no_encontrados,
            'errores': errores,
            'total_procesados': len(pronosticos_abiertos),
            'total_cerrados': len(cerrados),
        }
        
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

# ============================================================
# CIERRE AUTOMÁTICO CON API EXTERNA (FASE 14.1)
# ============================================================
@bp_pronosticos.route('/api/pronosticos/cerrar-con-api', methods=['POST'])
def api_cerrar_con_api():
    """Endpoint wrapper de cerrar_con_api_logica()."""
    data = request.json or {}
    limite = int(data.get('limite', 10))
    dias_atras = int(data.get('dias_atras', 7))
    
    try:
        resultado = cerrar_con_api_logica(limite=limite, dias_atras=dias_atras)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)})
        
# ============================================================
# GENERACIÓN AUTOMÁTICA DE PRONÓSTICOS (FASE 14.3)
# ============================================================
@bp_pronosticos.route('/api/pronosticos/generar-automaticos', methods=['POST'])
def api_generar_automaticos():
    """
    Consulta la API de Football-Data.org y genera pronósticos
    automáticamente para los partidos programados en los próximos N días.
    
    Filtros:
    - Solo ligas con código API y con datos en el histórico.
    - Solo equipos con >= MIN_PARTIDOS partidos en el histórico.
    - No duplica si ya existe un pronóstico abierto para ese partido.
    
    Body:
        {
            "dias": 7,              # días hacia adelante (default 7)
            "ligas": ["PL", "PD"],  # opcional, filtrar ligas
            "min_partidos": 5,      # mínimo de partidos por equipo (default 5)
            "dry_run": false,       # si True, no guarda, solo devuelve candidatos
        }
    
    Returns:
        {
            "generados": [...],
            "saltados": [...],   # razones: sin_datos, duplicado, etc.
            "errores": [...],
            "total_partidos_api": int,
        }
    """
    from backend.api_football import listar_partidos_proximos, codigo_liga_api
    from database.aliases_equipos import normalizar_equipo
    from database.motor_estadistico import obtener_partidos_historicos
    
    data = request.json or {}
    dias = int(data.get('dias', 7))
    min_partidos = int(data.get('min_partidos', 5))
    dry_run = bool(data.get('dry_run', False))
    
    # Si no se especifican ligas, usar todas las que tienen código API
    ligas_codigos = data.get('ligas')
    if not ligas_codigos:
        ligas_codigos = ['PL', 'ELC', 'PD', 'DED', 'BL1', 'BL2', 'SA', 'FL1', 'PPL', 'CL', 'EL', 'UCL']
    
    # ========== 1. Obtener partidos de la API ==========
    result = listar_partidos_proximos(dias_adelante=dias, ligas_codigos=ligas_codigos)
    
    if result.get('error') and not result.get('partidos'):
        return jsonify({'error': result['error']})
    
    partidos_api = result.get('partidos', [])
    
    generados = []
    saltados = []
    errores = []
    
    # ========== 2. Para cada partido, verificar y generar ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        for p in partidos_api:
            local_raw = p.get('local', '')
            visitante_raw = p.get('visitante', '')
            fecha = p.get('fecha', '')
            liga_api = p.get('competicion', '')
            
            # Normalizar equipos
            local_norm = normalizar_equipo(local_raw)
            visitante_norm = normalizar_equipo(visitante_raw)
            
            # ========== Verificar histórico mínimo ==========
            partidos_local = obtener_partidos_historicos(local_norm, como_local=None, limite=30)
            partidos_visit = obtener_partidos_historicos(visitante_norm, como_local=None, limite=30)
            
            if len(partidos_local) < min_partidos:
                saltados.append({
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'razon': f'{local_norm} tiene solo {len(partidos_local)} partidos (min {min_partidos})',
                })
                continue
            
            if len(partidos_visit) < min_partidos:
                saltados.append({
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'razon': f'{visitante_norm} tiene solo {len(partidos_visit)} partidos (min {min_partidos})',
                })
                continue
            
            # ========== Verificar duplicado ==========
            c.execute('''
                SELECT id FROM pronosticos
                WHERE partido_local = ?
                  AND partido_visitante = ?
                  AND cerrado = 0
                  AND (fecha_partido = ? OR fecha_partido = '' OR fecha_partido IS NULL)
            ''', (local_norm, visitante_norm, fecha))
            
            if c.fetchone():
                saltados.append({
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'razon': 'Ya existe pronóstico abierto para este partido',
                })
                continue
            
            # ========== Generar pronóstico ==========
            if dry_run:
                generados.append({
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'liga': liga_api,
                    'dry_run': True,
                    'partidos_local': len(partidos_local),
                    'partidos_visitante': len(partidos_visit),
                })
                continue
            
            try:
                resultado = pronosticar_partido(local_norm, visitante_norm, liga_pronostico=liga_api)
                
                if resultado.get('error'):
                    errores.append({
                        'local': local_norm,
                        'visitante': visitante_norm,
                        'fecha': fecha,
                        'error': resultado['error'],
                    })
                    continue
                
                mercados = resultado['mercados']
                
                # Guardar con automatico=1
                c.execute('''
                    INSERT INTO pronosticos (
                        fecha_pronostico, partido_local, partido_visitante, liga, fecha_partido,
                        motor_version, lambda_local, lambda_visitante,
                        prob_local, prob_empate, prob_visitante, prob_btts, prob_over25,
                        mercado_principal, cuota_real, ev_principal,
                        pronostico_json, cerrado, automatico,
                        lambda_local_pred, lambda_visitante_pred
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    local_norm, visitante_norm, liga_api, fecha,
                    resultado.get('version_motor', 'v2.0'),
                    resultado['lambdas']['local'],
                    resultado['lambdas']['visitante'],
                    mercados['1X2']['local'],
                    mercados['1X2']['empate'],
                    mercados['1X2']['visitante'],
                    mercados['BTTS'],
                    mercados['over'].get(2.5, 0),
                    'Local',  # mercado_principal por defecto
                    0,        # cuota_real (no la tenemos automáticamente)
                    None,     # ev_principal
                    json.dumps(resultado, ensure_ascii=False),
                    resultado['lambdas']['local'],
                    resultado['lambdas']['visitante'],
                ))
                
                pid = c.lastrowid
                
                generados.append({
                    'id': pid,
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'liga': liga_api,
                    'prob_local': round(mercados['1X2']['local'], 3),
                    'prob_empate': round(mercados['1X2']['empate'], 3),
                    'prob_visitante': round(mercados['1X2']['visitante'], 3),
                })
                
            except Exception as e:
                errores.append({
                    'local': local_norm,
                    'visitante': visitante_norm,
                    'fecha': fecha,
                    'error': str(e),
                })
        
        if not dry_run:
            conn.commit()
        
        return jsonify({
            'generados': generados,
            'saltados': saltados,
            'errores': errores,
            'total_partidos_api': len(partidos_api),
            'total_generados': len(generados),
            'total_saltados': len(saltados),
            'total_errores': len(errores),
            'dry_run': dry_run,
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()
        
# ============================================================
# EDITAR CUOTA REAL Y MERCADO PRINCIPAL
# ============================================================
@bp_pronosticos.route('/api/pronosticos/editar/<int:pronostico_id>', methods=['PUT'])
def api_editar_pronostico(pronostico_id):
    """
    Permite editar:
    - partido_local, partido_visitante
    - cuota_real
    - mercado_principal
    - fecha_partido
    
    Si se cambia la cuota o el mercado, recalcula ev_principal.
    """
    data = request.json or {}
    
    cuota_real = data.get('cuota_real')
    mercado_principal = data.get('mercado_principal')
    fecha_partido = data.get('fecha_partido')
    nuevo_local = data.get('partido_local')
    nuevo_visitante = data.get('partido_visitante')
    
    # Validaciones de cuota
    try:
        if cuota_real is not None:
            cuota_real = float(cuota_real)
            if cuota_real < 0:
                cuota_real = 0
    except (ValueError, TypeError):
        cuota_real = 0
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('SELECT * FROM pronosticos WHERE id = ?', (pronostico_id,))
        row = c.fetchone()
        
        if not row:
            return jsonify({'error': 'Pronóstico no encontrado'})
        
        # ========== Normalizar equipos si vienen ==========
        from database.aliases_equipos import normalizar_equipo
        
        if nuevo_local:
            nuevo_local = normalizar_equipo(nuevo_local.strip())
        if nuevo_visitante:
            nuevo_visitante = normalizar_equipo(nuevo_visitante.strip())
        
        # Usar los valores actuales si no se envían nuevos
        local_final = nuevo_local if nuevo_local else row['partido_local']
        visitante_final = nuevo_visitante if nuevo_visitante else row['partido_visitante']
        
        # ========== Recalcular EV ==========
        ev_principal = row['ev_principal']
        
        if cuota_real is not None and cuota_real > 0:
            prob = 0
            mercado = mercado_principal if mercado_principal else row['mercado_principal']
            
            if mercado == 'Local':
                prob = row['prob_local']
            elif mercado == 'Empate':
                prob = row['prob_empate']
            elif mercado == 'Visitante':
                prob = row['prob_visitante']
            elif mercado == 'BTTS':
                prob = row['prob_btts']
            elif mercado == 'Over25':
                prob = row['prob_over25']
            
            if prob and prob > 0:
                ev_principal = ((prob * cuota_real) - 1) * 100
        
        # ========== Actualizar ==========
        c.execute('''
            UPDATE pronosticos
            SET partido_local = ?,
                partido_visitante = ?,
                cuota_real = COALESCE(?, cuota_real),
                mercado_principal = COALESCE(?, mercado_principal),
                fecha_partido = COALESCE(?, fecha_partido),
                ev_principal = ?
            WHERE id = ?
        ''', (
            local_final,
            visitante_final,
            cuota_real,
            mercado_principal,
            fecha_partido,
            ev_principal,
            pronostico_id
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'partido_local': local_final,
            'partido_visitante': visitante_final,
            'cuota_real': cuota_real,
            'mercado_principal': mercado_principal,
            'ev_principal': ev_principal,
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()
        
# ============================================================
# ELIMINAR PRONÓSTICO
# ============================================================
@bp_pronosticos.route('/api/pronosticos/eliminar/<int:pronostico_id>', methods=['DELETE'])
def api_eliminar_pronostico(pronostico_id):
    """Elimina un pronóstico por ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('SELECT id FROM pronosticos WHERE id = ?', (pronostico_id,))
        if not c.fetchone():
            return jsonify({'error': 'Pronóstico no encontrado'})
        
        c.execute('DELETE FROM pronosticos WHERE id = ?', (pronostico_id,))
        conn.commit()
        
        return jsonify({'success': True, 'id': pronostico_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# ELIMINAR TODOS LOS PRONÓSTICOS
# ============================================================
@bp_pronosticos.route('/api/pronosticos/eliminar-todos', methods=['DELETE'])
def api_eliminar_todos_pronosticos():
    """
    Elimina TODOS los pronósticos.
    
    Query params:
        solo_abiertos: si 'true', solo borra los no cerrados
    """
    solo_abiertos = request.args.get('solo_abiertos', 'false').lower() == 'true'
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if solo_abiertos:
            c.execute('DELETE FROM pronosticos WHERE cerrado = 0')
            borrados = c.rowcount
        else:
            c.execute('SELECT COUNT(*) FROM pronosticos')
            borrados = c.fetchone()[0]
            c.execute('DELETE FROM pronosticos')
        
        # Resetear el autoincremento si borramos todo
        if not solo_abiertos:
            try:
                c.execute("DELETE FROM sqlite_sequence WHERE name = 'pronosticos'")
            except Exception:
                pass
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'total_borrados': borrados,
            'solo_abiertos': solo_abiertos,
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()
# ============================================================
# backend/rutas_backtesting.py
# Blueprint: métricas de backtesting del modelo.
# Endpoints:
#   GET /api/backtesting/metricas
#   GET /api/backtesting/calibracion
#   GET /api/backtesting/por-motor
#   GET /api/backtesting/por-liga
#   GET /api/backtesting/por-confianza
# ============================================================

from flask import Blueprint, jsonify
import sqlite3
import json

from backend.db import DB_PATH
from database.motor_estadistico import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_calibracion_avanzada,
    calcular_roi_avanzado,
)


bp_backtesting = Blueprint('backtesting', __name__)


# ============================================================
# MÉTRICAS GENERALES
# ============================================================
@bp_backtesting.route('/api/backtesting/metricas')
def api_backtesting_metricas():
    """Devuelve las métricas generales del modelo (P4 ampliado)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        # ========== Pronósticos totales ==========
        c.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cerrado = 1 THEN 1 ELSE 0 END) as cerrados,
                SUM(CASE WHEN cerrado = 0 THEN 1 ELSE 0 END) as abiertos,
                SUM(CASE WHEN partido_id IS NOT NULL THEN 1 ELSE 0 END) as vinculados
            FROM pronosticos
        ''')
        row = c.fetchone()
        total = row['total'] or 0
        cerrados = row['cerrados'] or 0
        abiertos = row['abiertos'] or 0
        vinculados = row['vinculados'] or 0

        if cerrados == 0:
            return jsonify({
                'total_pronosticos': total,
                'cerrados': 0,
                'abiertos': abiertos,
                'vinculados': vinculados,
                'mensaje': 'No hay pronósticos cerrados aún'
            })

        # ========== Obtener todos los cerrados ==========
        c.execute('''
            SELECT 
                id, prob_local, prob_empate, prob_visitante, prob_btts, prob_over25,
                resultado_local, resultado_visitante, resultado_btts, resultado_over25,
                mercado_principal, cuota_real, ev_principal
            FROM pronosticos
            WHERE cerrado = 1
        ''')
        rows = c.fetchall()

        # ========== Preparar listas para métricas ==========
        pred_1x2_local = []
        pred_1x2_empate = []
        pred_1x2_visitante = []
        pred_btts = []
        pred_over25 = []

        aciertos_1x2 = 0
        aciertos_btts = 0
        aciertos_over25 = 0

        for row in rows:
            r_local = row['resultado_local'] or 0
            r_visit = row['resultado_visitante'] or 0
            r_btts = row['resultado_btts'] or 0
            r_over25 = row['resultado_over25'] or 0

            gano_local = 1 if r_local > r_visit else 0
            gano_empate = 1 if r_local == r_visit else 0
            gano_visit = 1 if r_local < r_visit else 0

            if row['prob_local'] is not None:
                pred_1x2_local.append({'prob': row['prob_local'], 'resultado': gano_local})
            if row['prob_empate'] is not None:
                pred_1x2_empate.append({'prob': row['prob_empate'], 'resultado': gano_empate})
            if row['prob_visitante'] is not None:
                pred_1x2_visitante.append({'prob': row['prob_visitante'], 'resultado': gano_visit})

            if row['prob_btts'] is not None:
                pred_btts.append({'prob': row['prob_btts'], 'resultado': r_btts})
            if row['prob_over25'] is not None:
                pred_over25.append({'prob': row['prob_over25'], 'resultado': r_over25})

            # Aciertos (el que tenga mayor probabilidad)
            max_prob = max(row['prob_local'] or 0, row['prob_empate'] or 0, row['prob_visitante'] or 0)
            if max_prob == row['prob_local'] and gano_local:
                aciertos_1x2 += 1
            elif max_prob == row['prob_empate'] and gano_empate:
                aciertos_1x2 += 1
            elif max_prob == row['prob_visitante'] and gano_visit:
                aciertos_1x2 += 1

            if row['prob_btts'] is not None:
                pred_btts_pred = 1 if row['prob_btts'] > 0.5 else 0
                if pred_btts_pred == r_btts:
                    aciertos_btts += 1

            if row['prob_over25'] is not None:
                pred_over_pred = 1 if row['prob_over25'] > 0.5 else 0
                if pred_over_pred == r_over25:
                    aciertos_over25 += 1

        # ========== Brier Score ==========
        brier_local = calcular_brier_score(pred_1x2_local)
        brier_empate = calcular_brier_score(pred_1x2_empate)
        brier_visit = calcular_brier_score(pred_1x2_visitante)
        brier_btts = calcular_brier_score(pred_btts)
        brier_over25 = calcular_brier_score(pred_over25)

        brier_promedio_1x2 = None
        if all([brier_local, brier_empate, brier_visit]):
            brier_promedio_1x2 = round((brier_local + brier_empate + brier_visit) / 3, 4)

        # ========== Log Loss ==========
        logloss_local = calcular_log_loss(pred_1x2_local)
        logloss_empate = calcular_log_loss(pred_1x2_empate)
        logloss_visit = calcular_log_loss(pred_1x2_visitante)
        logloss_btts = calcular_log_loss(pred_btts)
        logloss_over25 = calcular_log_loss(pred_over25)

        # ========== Calibración ==========
        calibracion_local = calcular_calibracion_avanzada(pred_1x2_local)
        calibracion_btts = calcular_calibracion_avanzada(pred_btts)

        # ========== ROI simulado ==========
        c.execute('''
            SELECT 
                mercado_principal, cuota_real, ev_principal,
                resultado_local, resultado_visitante, resultado_btts, resultado_over25
            FROM pronosticos
            WHERE cerrado = 1 AND cuota_real > 0
        ''')
        apuestas_data = c.fetchall()

        apuestas = []
        for a in apuestas_data:
            if a['mercado_principal'] == 'Local':
                ganada = (a['resultado_local'] or 0) > (a['resultado_visitante'] or 0)
            elif a['mercado_principal'] == 'Visitante':
                ganada = (a['resultado_local'] or 0) < (a['resultado_visitante'] or 0)
            elif a['mercado_principal'] == 'Empate':
                ganada = (a['resultado_local'] or 0) == (a['resultado_visitante'] or 0)
            elif a['mercado_principal'] == 'BTTS':
                ganada = (a['resultado_btts'] or 0) == 1
            elif a['mercado_principal'] == 'Over25':
                ganada = (a['resultado_over25'] or 0) == 1
            else:
                continue

            apuestas.append({
                'stake': 1,
                'cuota': a['cuota_real'],
                'ganada': ganada,
            })

        roi_data = calcular_roi_avanzado(apuestas) if apuestas else None

        tasa_acierto_1x2 = round(aciertos_1x2 / cerrados * 100, 2) if cerrados > 0 else 0
        tasa_acierto_btts = round(aciertos_btts / cerrados * 100, 2) if cerrados > 0 else 0
        tasa_acierto_over25 = round(aciertos_over25 / cerrados * 100, 2) if cerrados > 0 else 0

        return jsonify({
            'total_pronosticos': total,
            'cerrados': cerrados,
            'abiertos': abiertos,
            'vinculados': vinculados,

            'aciertos_1x2': aciertos_1x2,
            'tasa_acierto_1x2': tasa_acierto_1x2,
            'aciertos_btts': aciertos_btts,
            'tasa_acierto_btts': tasa_acierto_btts,
            'aciertos_over25': aciertos_over25,
            'tasa_acierto_over25': tasa_acierto_over25,

            'brier': {
                'local': brier_local,
                'empate': brier_empate,
                'visitante': brier_visit,
                'promedio_1x2': brier_promedio_1x2,
                'btts': brier_btts,
                'over25': brier_over25,
            },

            'log_loss': {
                'local': logloss_local,
                'empate': logloss_empate,
                'visitante': logloss_visit,
                'btts': logloss_btts,
                'over25': logloss_over25,
            },

            'calibracion': {
                'local': calibracion_local,
                'btts': calibracion_btts,
            },

            'roi_avanzado': roi_data,
            'total_apuestas_ev_positivo': len([a for a in apuestas_data if a['ev_principal'] and a['ev_principal'] > 0]),
        })
    finally:
        conn.close()


# ============================================================
# CALIBRACIÓN
# ============================================================
@bp_backtesting.route('/api/backtesting/calibracion')
def api_backtesting_calibracion():
    """Calibración: predicho vs real por rango"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT prob_local, 
                   CASE WHEN resultado_local > resultado_visitante THEN 1 ELSE 0 END as acerto
            FROM pronosticos
            WHERE cerrado = 1 AND prob_local IS NOT NULL
        ''')
        datos = c.fetchall()

        if len(datos) < 3:
            return jsonify({
                'mensaje': f'Insuficientes datos para calibrar ({len(datos)} cerrados, mínimo 3)',
                'rangos': []
            })

        rangos = {
            '0-10': [], '10-20': [], '20-30': [], '30-40': [], '40-50': [],
            '50-60': [], '60-70': [], '70-80': [], '80-90': [], '90-100': []
        }

        for prob, acerto in datos:
            if prob is None:
                continue
            prob_pct = prob * 100
            if prob_pct < 10: rangos['0-10'].append(acerto)
            elif prob_pct < 20: rangos['10-20'].append(acerto)
            elif prob_pct < 30: rangos['20-30'].append(acerto)
            elif prob_pct < 40: rangos['30-40'].append(acerto)
            elif prob_pct < 50: rangos['40-50'].append(acerto)
            elif prob_pct < 60: rangos['50-60'].append(acerto)
            elif prob_pct < 70: rangos['60-70'].append(acerto)
            elif prob_pct < 80: rangos['70-80'].append(acerto)
            elif prob_pct < 90: rangos['80-90'].append(acerto)
            else: rangos['90-100'].append(acerto)

        resultado = []
        for nombre, lista in rangos.items():
            if lista:
                inicio = float(nombre.split('-')[0])
                promedio_predicho = inicio + 5
                frecuencia_real = sum(lista) / len(lista) * 100
                resultado.append({
                    'rango': nombre + '%',
                    'predicho_promedio': round(promedio_predicho, 1),
                    'real': round(frecuencia_real, 1),
                    'diferencia': round(frecuencia_real - promedio_predicho, 1),
                    'muestras': len(lista)
                })

        return jsonify({
            'rangos': resultado,
            'total_muestras': len(datos)
        })
    finally:
        conn.close()


# ============================================================
# POR MOTOR
# ============================================================
@bp_backtesting.route('/api/backtesting/por-motor')
def api_backtesting_por_motor():
    """Compara rendimiento por versión del motor"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT motor_version,
                   COUNT(*) as total,
                   SUM(CASE WHEN cerrado = 1 THEN 1 ELSE 0 END) as cerrados
            FROM pronosticos
            GROUP BY motor_version
        ''')

        resultado = []
        for row in c.fetchall():
            motor, total, cerrados = row

            c.execute('''
                SELECT SUM(CASE 
                    WHEN prob_local > prob_empate AND prob_local > prob_visitante
                         AND resultado_local > resultado_visitante THEN 1
                    WHEN prob_empate > prob_local AND prob_empate > prob_visitante
                         AND resultado_local = resultado_visitante THEN 1
                    WHEN prob_visitante > prob_local AND prob_visitante > prob_empate
                         AND resultado_local < resultado_visitante THEN 1
                    ELSE 0
                END)
                FROM pronosticos
                WHERE cerrado = 1 AND motor_version = ?
            ''', (motor,))
            aciertos = c.fetchone()[0] or 0

            resultado.append({
                'motor': motor or 'desconocido',
                'total': total,
                'cerrados': cerrados,
                'aciertos': aciertos,
                'tasa': round(aciertos / cerrados * 100, 2) if cerrados else 0
            })

        return jsonify(resultado)
    finally:
        conn.close()


# ============================================================
# POR LIGA
# ============================================================
@bp_backtesting.route('/api/backtesting/por-liga')
def api_backtesting_por_liga():
    """Rendimiento por liga"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT liga,
                   COUNT(*) as total,
                   SUM(CASE WHEN cerrado = 1 THEN 1 ELSE 0 END) as cerrados
            FROM pronosticos
            WHERE liga IS NOT NULL AND liga != ''
            GROUP BY liga
            HAVING cerrados > 0
            ORDER BY total DESC
        ''')

        resultado = []
        for row in c.fetchall():
            liga, total, cerrados = row

            c.execute('''
                SELECT SUM(CASE 
                    WHEN prob_local > prob_empate AND prob_local > prob_visitante
                         AND resultado_local > resultado_visitante THEN 1
                    WHEN prob_empate > prob_local AND prob_empate > prob_visitante
                         AND resultado_local = resultado_visitante THEN 1
                    WHEN prob_visitante > prob_local AND prob_visitante > prob_empate
                         AND resultado_local < resultado_visitante THEN 1
                    ELSE 0
                END)
                FROM pronosticos
                WHERE cerrado = 1 AND liga = ?
            ''', (liga,))
            aciertos = c.fetchone()[0] or 0

            resultado.append({
                'liga': liga,
                'total': total,
                'cerrados': cerrados,
                'aciertos': aciertos,
                'tasa': round(aciertos / cerrados * 100, 2) if cerrados else 0
            })

        return jsonify(resultado)
    finally:
        conn.close()


# ============================================================
# POR CONFIANZA
# ============================================================
@bp_backtesting.route('/api/backtesting/por-confianza')
def api_backtesting_por_confianza():
    """Rendimiento por nivel de confianza (alta/media/baja)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                id,
                MAX(prob_local, prob_empate, prob_visitante) as max_prob,
                CASE 
                    WHEN prob_local > prob_empate AND prob_local > prob_visitante
                         AND resultado_local > resultado_visitante THEN 1
                    WHEN prob_empate > prob_local AND prob_empate > prob_visitante
                         AND resultado_local = resultado_visitante THEN 1
                    WHEN prob_visitante > prob_local AND prob_visitante > prob_empate
                         AND resultado_local < resultado_visitante THEN 1
                    ELSE 0
                END as acerto
            FROM pronosticos
            WHERE cerrado = 1
        ''')

        datos = c.fetchall()
        if not datos:
            return jsonify([])

        niveles = {'alta': [], 'media': [], 'baja': []}
        for row in datos:
            max_prob, acerto = row[1], row[2]
            if max_prob is None:
                continue
            if max_prob >= 0.65:
                niveles['alta'].append(acerto)
            elif max_prob >= 0.45:
                niveles['media'].append(acerto)
            else:
                niveles['baja'].append(acerto)

        resultado = []
        for nivel, lista in niveles.items():
            if lista:
                aciertos = sum(lista)
                total = len(lista)
                resultado.append({
                    'nivel': nivel,
                    'total': total,
                    'aciertos': aciertos,
                    'tasa': round(aciertos / total * 100, 2) if total else 0
                })

        return jsonify(resultado)
    finally:
        conn.close()
        
# ============================================================
# BACKTESTING POR MERCADO (FASE 7.3) — v2
# ============================================================
@bp_backtesting.route('/api/backtesting/por-mercado')
def api_backtesting_por_mercado():
    """
    Evalúa cada mercado individualmente usando pronostico_json (probabilidades
    predichas en el momento) y resultado_mercados_json (realidad del partido).
    
    Devuelve, por mercado:
    - total: pronósticos evaluados
    - aciertos: veces que el signo predicho > 0.5 coincide con el real
    - tasa: % de acierto
    - brier: Brier Score (menor = mejor)
    - roi: ROI simulado (apostando 1u cuando EV > 0)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # ========== 1. Obtener pronósticos cerrados con ambos JSON ==========
        c.execute('''
            SELECT id, pronostico_json, resultado_mercados_json,
                   cuota_real, mercado_principal
            FROM pronosticos
            WHERE cerrado = 1
              AND pronostico_json IS NOT NULL AND pronostico_json != ''
              AND resultado_mercados_json IS NOT NULL AND resultado_mercados_json != ''
        ''')
        
        rows = c.fetchall()
        
        if not rows:
            return jsonify({
                'mensaje': 'No hay pronósticos cerrados con JSON de mercados.',
                'mercados': [],
                'total_pronosticos': 0
            })
        
        # ========== 2. Definir mercados a evaluar ==========
        # Cada mercado tiene:
        #   - nombre: para mostrar
        #   - categoria: goles / corners / tarjetas / doble / jugador
        #   - get_prob(pron_json): probabilidad predicha en el momento
        #   - get_real(mj): 0 o 1 (o None si no hay dato)
        
        def _p(path, default=None):
            """Navega por el JSON del pronóstico de forma segura."""
            def getter(pj):
                try:
                    val = pj
                    for key in path:
                        if isinstance(key, int):
                            val = val[key]
                        else:
                            val = val.get(key) if isinstance(val, dict) else None
                        if val is None:
                            return default
                    return val
                except Exception:
                    return default
            return getter
        
        mercados_config = [
            # ========== 1X2 ==========
            {
                'nombre': '1X2 - Local',
                'categoria': 'goles',
                'get_prob': _p(['mercados', '1X2', 'local']),
                'get_real': lambda mj: 1 if mj['goles_local'] > mj['goles_visitante'] else 0,
            },
            {
                'nombre': '1X2 - Empate',
                'categoria': 'goles',
                'get_prob': _p(['mercados', '1X2', 'empate']),
                'get_real': lambda mj: 1 if mj['goles_local'] == mj['goles_visitante'] else 0,
            },
            {
                'nombre': '1X2 - Visitante',
                'categoria': 'goles',
                'get_prob': _p(['mercados', '1X2', 'visitante']),
                'get_real': lambda mj: 1 if mj['goles_local'] < mj['goles_visitante'] else 0,
            },
            # ========== Doble Oportunidad ==========
            {
                'nombre': 'Doble Oportunidad 1X',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'doble_oportunidad', '1X']),
                'get_real': lambda mj: 1 if mj['goles_local'] >= mj['goles_visitante'] else 0,
            },
            {
                'nombre': 'Doble Oportunidad 12',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'doble_oportunidad', '12']),
                'get_real': lambda mj: 1 if mj['goles_local'] != mj['goles_visitante'] else 0,
            },
            {
                'nombre': 'Doble Oportunidad X2',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'doble_oportunidad', 'X2']),
                'get_real': lambda mj: 1 if mj['goles_local'] <= mj['goles_visitante'] else 0,
            },
            # ========== BTTS ==========
            {
                'nombre': 'BTTS',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'BTTS']),
                'get_real': lambda mj: mj.get('btts'),
            },
            # ========== Over / Under goles ==========
            {
                'nombre': 'Over 1.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'over', '1.5']),
                'get_real': lambda mj: mj.get('over15'),
            },
            {
                'nombre': 'Over 2.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'over', '2.5']),
                'get_real': lambda mj: mj.get('over25'),
            },
            {
                'nombre': 'Over 3.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'over', '3.5']),
                'get_real': lambda mj: mj.get('over35'),
            },
            {
                'nombre': 'Over 4.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'over', '4.5']),
                'get_real': lambda mj: mj.get('over45'),
            },
            {
                'nombre': 'Under 1.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'under', '1.5']),
                'get_real': lambda mj: 1 - (mj.get('over15') or 0),
            },
            {
                'nombre': 'Under 2.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'under', '2.5']),
                'get_real': lambda mj: 1 - (mj.get('over25') or 0),
            },
            {
                'nombre': 'Under 3.5',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'under', '3.5']),
                'get_real': lambda mj: 1 - (mj.get('over35') or 0),
            },
            # ========== Goles por equipo ==========
            {
                'nombre': 'Local marca (+1)',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'local_marca']),
                'get_real': lambda mj: 1 if mj['goles_local'] > 0 else 0,
            },
            {
                'nombre': 'Visitante marca (+1)',
                'categoria': 'goles',
                'get_prob': _p(['mercados', 'visitante_marca']),
                'get_real': lambda mj: 1 if mj['goles_visitante'] > 0 else 0,
            },
            # ========== CÓRNERS ==========
            {
                'nombre': 'Over 7.5 córners',
                'categoria': 'corners',
                'get_prob': _p(['mercados_corners', 'over', '7.5']),
                'get_real': lambda mj: mj.get('corners_over75'),
            },
            {
                'nombre': 'Over 8.5 córners',
                'categoria': 'corners',
                'get_prob': _p(['mercados_corners', 'over', '8.5']),
                'get_real': lambda mj: mj.get('corners_over85'),
            },
            {
                'nombre': 'Over 9.5 córners',
                'categoria': 'corners',
                'get_prob': _p(['mercados_corners', 'over', '9.5']),
                'get_real': lambda mj: mj.get('corners_over95'),
            },
            {
                'nombre': 'Over 10.5 córners',
                'categoria': 'corners',
                'get_prob': _p(['mercados_corners', 'over', '10.5']),
                'get_real': lambda mj: mj.get('corners_over105'),
            },
            {
                'nombre': 'Over 11.5 córners',
                'categoria': 'corners',
                'get_prob': _p(['mercados_corners', 'over', '11.5']),
                'get_real': lambda mj: mj.get('corners_over115'),
            },
            # ========== TARJETAS ==========
            {
                'nombre': 'Over 1.5 tarjetas',
                'categoria': 'tarjetas',
                'get_prob': _p(['mercados_tarjetas', 'over', '1.5']),
                'get_real': lambda mj: mj.get('tarjetas_over15'),
            },
            {
                'nombre': 'Over 2.5 tarjetas',
                'categoria': 'tarjetas',
                'get_prob': _p(['mercados_tarjetas', 'over', '2.5']),
                'get_real': lambda mj: mj.get('tarjetas_over25'),
            },
            {
                'nombre': 'Over 3.5 tarjetas',
                'categoria': 'tarjetas',
                'get_prob': _p(['mercados_tarjetas', 'over', '3.5']),
                'get_real': lambda mj: mj.get('tarjetas_over35'),
            },
            {
                'nombre': 'Over 4.5 tarjetas',
                'categoria': 'tarjetas',
                'get_prob': _p(['mercados_tarjetas', 'over', '4.5']),
                'get_real': lambda mj: mj.get('tarjetas_over45'),
            },
        ]
        
        # ========== 3. Evaluar cada mercado ==========
        resultados = []
        
        for cfg in mercados_config:
            total_eval = 0
            aciertos = 0
            predicciones_brier = []
            apuestas = []
            
            for r in rows:
                try:
                    pj = json.loads(r['pronostico_json'])
                    mj = json.loads(r['resultado_mercados_json'])
                except Exception:
                    continue
                
                # Valor real
                try:
                    real = cfg['get_real'](mj)
                except Exception:
                    continue
                if real is None:
                    continue
                
                # Probabilidad predicha
                try:
                    prob_predicha = cfg['get_prob'](pj)
                except Exception:
                    prob_predicha = None
                if prob_predicha is None:
                    continue
                
                total_eval += 1
                
                # Acierto
                predicho_signo = 1 if prob_predicha > 0.5 else 0
                if predicho_signo == real:
                    aciertos += 1
                
                # Brier
                predicciones_brier.append({
                    'prob': prob_predicha,
                    'resultado': real
                })
                
                # ROI: usar cuota_real si aplica (aproximación)
                if r['cuota_real'] and r['cuota_real'] > 0 and r['mercado_principal']:
                    # Solo para el mercado que coincide con el principal
                    # (es la única cuota real que tenemos)
                    if cfg['nombre'].lower().replace(' ', '') in r['mercado_principal'].lower().replace(' ', ''):
                        ev = (prob_predicha * r['cuota_real']) - 1
                        if ev > 0:
                            ganada = (predicho_signo == 1 and real == 1)
                            apuestas.append({
                                'stake': 1,
                                'cuota': r['cuota_real'],
                                'ganada': ganada,
                            })
            
            if total_eval == 0:
                continue
            
            tasa = round(aciertos / total_eval * 100, 2)
            brier = calcular_brier_score(predicciones_brier) if predicciones_brier else None
            roi_data = calcular_roi_avanzado(apuestas) if apuestas else None
            
            resultados.append({
                'mercado': cfg['nombre'],
                'categoria': cfg['categoria'],
                'total': total_eval,
                'aciertos': aciertos,
                'tasa': tasa,
                'brier': brier,
                'roi': roi_data['roi'] if roi_data else None,
                'apuestas': roi_data['total_apuestas'] if roi_data else 0,
                'profit': roi_data['profit_total'] if roi_data else None,
            })
        
        # ========== 4. Ordenar ==========
        orden_categorias = {'goles': 1, 'corners': 2, 'tarjetas': 3}
        resultados.sort(key=lambda x: (orden_categorias.get(x['categoria'], 99), -x['tasa']))
        
        return jsonify({
            'mercados': resultados,
            'total_pronosticos': len(rows),
            'total_mercados_evaluados': len(resultados),
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()
        
# ============================================================
# MAE / RMSE DE GOLES (FASE 10.5)
# ============================================================
@bp_backtesting.route('/api/backtesting/mae-rmse')
def api_backtesting_mae_rmse():
    """
    Calcula el MAE y RMSE de los λ predichos vs los goles reales.
    
    Métricas:
    - MAE local: |λ_local_pred - goles_local_real|
    - MAE visitante: |λ_visit_pred - goles_visitante_real|
    - MAE total: MAE local + MAE visitante (o media)
    - RMSE: raíz del error cuadrático medio
    - Por liga: desglose si hay suficientes partidos
    
    Solo usa pronósticos que tengan:
    - λ predicho (lambda_local_pred, lambda_visitante_pred)
    - Resultado real (resultado_local, resultado_visitante)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT 
                id, liga,
                lambda_local_pred, lambda_visitante_pred,
                resultado_local, resultado_visitante
            FROM pronosticos
            WHERE cerrado = 1
              AND lambda_local_pred IS NOT NULL
              AND lambda_visitante_pred IS NOT NULL
              AND resultado_local IS NOT NULL
              AND resultado_visitante IS NOT NULL
        ''')
        
        rows = c.fetchall()
        
        if not rows:
            return jsonify({
                'mensaje': 'No hay pronósticos cerrados con λ predicho. Genera y cierra algunos pronósticos nuevos.',
                'total': 0,
            })
        
        import math
        
        # ========== Global ==========
        errores_local = []
        errores_visit = []
        errores_total = []
        
        for r in rows:
            e_local = abs(r['lambda_local_pred'] - r['resultado_local'])
            e_visit = abs(r['lambda_visitante_pred'] - r['resultado_visitante'])
            e_total = abs(
                (r['lambda_local_pred'] + r['lambda_visitante_pred'])
                - (r['resultado_local'] + r['resultado_visitante'])
            )
            errores_local.append(e_local)
            errores_visit.append(e_visit)
            errores_total.append(e_total)
        
        n = len(rows)
        
        def _mae(errores):
            return round(sum(errores) / len(errores), 4) if errores else None
        
        def _rmse(errores):
            if not errores:
                return None
            mse = sum(e ** 2 for e in errores) / len(errores)
            return round(math.sqrt(mse), 4)
        
        def _sesgo(pred_col, real_col):
            """Sesgo medio: pred - real. Positivo = sobreestima."""
            diffs = []
            for r in rows:
                diffs.append(r[pred_col] - r[real_col])
            return round(sum(diffs) / len(diffs), 4) if diffs else None
        
        global_data = {
            'total': n,
            'mae_local': _mae(errores_local),
            'mae_visitante': _mae(errores_visit),
            'mae_total': _mae(errores_total),
            'rmse_local': _rmse(errores_local),
            'rmse_visitante': _rmse(errores_visit),
            'rmse_total': _rmse(errores_total),
            'sesgo_local': _sesgo('lambda_local_pred', 'resultado_local'),
            'sesgo_visitante': _sesgo('lambda_visitante_pred', 'resultado_visitante'),
            'interpretacion': _interpretar_mae(_mae(errores_local), _mae(errores_visit)),
        }
        
        # ========== Por liga ==========
        por_liga = {}
        for r in rows:
            liga = r['liga'] or 'Sin liga'
            if liga not in por_liga:
                por_liga[liga] = {
                    'errores_local': [],
                    'errores_visit': [],
                    'errores_total': [],
                    'total': 0,
                }
            e_local = abs(r['lambda_local_pred'] - r['resultado_local'])
            e_visit = abs(r['lambda_visitante_pred'] - r['resultado_visitante'])
            e_total = abs(
                (r['lambda_local_pred'] + r['lambda_visitante_pred'])
                - (r['resultado_local'] + r['resultado_visitante'])
            )
            por_liga[liga]['errores_local'].append(e_local)
            por_liga[liga]['errores_visit'].append(e_visit)
            por_liga[liga]['errores_total'].append(e_total)
            por_liga[liga]['total'] += 1
        
        ligas_data = []
        for liga, d in por_liga.items():
            if d['total'] < 3:
                continue
            ligas_data.append({
                'liga': liga,
                'total': d['total'],
                'mae_local': _mae(d['errores_local']),
                'mae_visitante': _mae(d['errores_visit']),
                'mae_total': _mae(d['errores_total']),
                'rmse_total': _rmse(d['errores_total']),
            })
        
        # Ordenar por MAE total ascendente (mejor primero)
        ligas_data.sort(key=lambda x: x['mae_total'] if x['mae_total'] is not None else 99)
        
        return jsonify({
            'global': global_data,
            'por_liga': ligas_data,
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()


def _interpretar_mae(mae_local, mae_visit):
    """
    Devuelve una interpretación cualitativa del MAE.
    """
    if mae_local is None or mae_visit is None:
        return {'nivel': 'sin_datos', 'color': '#8899aa'}
    
    mae_prom = (mae_local + mae_visit) / 2
    
    if mae_prom < 0.5:
        return {'nivel': 'excelente', 'color': '#00ff88'}
    elif mae_prom < 0.7:
        return {'nivel': 'bueno', 'color': '#00d4ff'}
    elif mae_prom < 0.9:
        return {'nivel': 'aceptable', 'color': '#ffaa00'}
    else:
        return {'nivel': 'mejorable', 'color': '#ff4455'}
    
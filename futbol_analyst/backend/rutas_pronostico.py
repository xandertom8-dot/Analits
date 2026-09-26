# ============================================================
# backend/rutas_pronostico.py
# Blueprint: generación de pronósticos.
# Incluye la lógica completa de pronosticar_partido().
# Endpoints:
#   POST /pronosticar
#   POST /pronosticar-por-id
# ============================================================

from flask import Blueprint, jsonify, request

from database.motor_estadistico import (
    calcular_lambda_poisson,
    calcular_mercados_poisson,
    calcular_lambda_corners,
    calcular_mercados_corners,
    calcular_lambda_tarjetas,
    calcular_mercados_tarjetas,
    obtener_h2h,
    calcular_distribucion_equipo,
    detectar_anomalias_completo,
    calcular_n_efectivo_por_condicion,
    calcular_nivel_confianza,
    calcular_sample_quality_score,
    calcular_intervalo_confianza,
    calcular_edge_ajustado,
    obtener_top_jugadores_probabilidades,
    calcular_kelly_multiples_fracciones,
    VERSION_MOTOR,
)
from database.aliases_equipos import normalizar_equipo


bp_pronostico = Blueprint('pronostico', __name__)


# ============================================================
# PRONÓSTICO COMPLETO
# ============================================================
def pronosticar_partido(local, visitante, liga_pronostico=None):
    """
    Genera un pronóstico usando el motor estadístico v2.0
    - Poisson para goles
    - Ponderación por recencia
    - Tendencias
    - H2H
    - Nivel de confianza
    """
    # ========== 1. Calcular λ para cada equipo ==========
    resultado_local = calcular_lambda_poisson(local, visitante, como_local=True, liga_pronostico=liga_pronostico)
    resultado_visit = calcular_lambda_poisson(visitante, local, como_local=False, liga_pronostico=liga_pronostico)

    errores = []
    if resultado_local.get('error'):
        errores.append(resultado_local['error'])
    if resultado_visit.get('error'):
        errores.append(resultado_visit['error'])

    if errores:
        return {
            'error': ' | '.join(errores),
            'tipo_error': 'datos_insuficientes',
            'local': local,
            'visitante': visitante
        }

    lambda_local = resultado_local['lambda']
    lambda_visit = resultado_visit['lambda']
    
        # ========== 2. Decidir modelo (Poisson vs NegBin) ==========
    from database.motor_estadistico import (
        decidir_modelo, obtener_partidos_historicos,
        estimar_rho_dixon_coles,
    )
    partidos_local_full = obtener_partidos_historicos(local, como_local=None, liga_pronostico=liga_pronostico, limite=15)
    partidos_visit_full = obtener_partidos_historicos(visitante, como_local=None, liga_pronostico=liga_pronostico, limite=15)
    
    decision_modelo = decidir_modelo(partidos_local_full, partidos_visit_full)
    
    # ========== 2b. Estimar rho Dixon-Coles ==========
    rho_info = estimar_rho_dixon_coles(liga=liga_pronostico)
    rho = rho_info['rho']
    
    # ========== 3. Calcular mercados ==========
    mercados = calcular_mercados_poisson(
        lambda_local,
        lambda_visit,
        usar_negbin=(decision_modelo['modelo'] == 'negbin'),
        alpha_local=decision_modelo['alpha_local'],
        alpha_visitante=decision_modelo['alpha_visitante'],
        rho_dixon_coles=rho,
    )
    
    # Añadir info del modelo a la respuesta (sin exponerlo en UI)
    mercados['_decision_modelo'] = decision_modelo
    mercados['_rho_dixon_coles'] = rho_info
    
    # ========== Log en consola (no va al frontend) ==========
    print(f"[MODELO] {local} vs {visitante}: {decision_modelo['modelo'].upper()} + DIXON-COLES")
    print(f"         {decision_modelo['razon']}")
    if decision_modelo['modelo'] == 'negbin':
        print(f"         α_local={decision_modelo['alpha_local']}, α_visit={decision_modelo['alpha_visitante']}")
    print(f"         ρ={rho_info['rho']} ({rho_info['fuente']}, {rho_info['partidos']} part.)")

    # ========== MERCADOS DE CÓRNERS ==========
    corners_local = calcular_lambda_corners(local, visitante, como_local=True, liga_pronostico=liga_pronostico)
    corners_visit = calcular_lambda_corners(visitante, local, como_local=False, liga_pronostico=liga_pronostico)

    mercados_corners = None
    if not corners_local.get('error') and not corners_visit.get('error'):
        mercados_corners = calcular_mercados_corners(
            corners_local['lambda'],
            corners_visit['lambda']
        )
        mercados_corners['meta'] = {
            'local': corners_local,
            'visitante': corners_visit
        }

    # ========== MERCADOS DE TARJETAS ==========
    tarjetas_local = calcular_lambda_tarjetas(local, visitante, como_local=True, liga_pronostico=liga_pronostico)
    tarjetas_visit = calcular_lambda_tarjetas(visitante, local, como_local=False, liga_pronostico=liga_pronostico)

    mercados_tarjetas = None
    if not tarjetas_local.get('error') and not tarjetas_visit.get('error'):
        mercados_tarjetas = calcular_mercados_tarjetas(
            tarjetas_local['lambda'],
            tarjetas_visit['lambda']
        )
        mercados_tarjetas['meta'] = {
            'local': tarjetas_local,
            'visitante': tarjetas_visit
        }

    # ========== DISTRIBUCIONES Y HIT RATES ==========
    dist_local = calcular_distribucion_equipo(
        local, liga_pronostico=liga_pronostico, como_local=True, limite=15
    )
    dist_visit = calcular_distribucion_equipo(
        visitante, liga_pronostico=liga_pronostico, como_local=False, limite=15
    )

    # ========== DETECCIÓN DE ANOMALÍAS ==========
    anomalias = detectar_anomalias_completo(
        mercados,
        mercados_corners,
        mercados_tarjetas,
        dist_local,
        dist_visit
    )

    # ========== 3. H2H ==========
    h2h = obtener_h2h(local, visitante, limite=10)

    # ========== 4. Confianza ==========
    tiene_tendencia = (
        resultado_local['tendencia']['direccion'] != 'sin_datos' and
        resultado_visit['tendencia']['direccion'] != 'sin_datos'
    )

    # ========== 4.1 Sample Quality Score ==========
    sqs_local = calcular_sample_quality_score(local, liga_pronostico, como_local=True)
    sqs_visit = calcular_sample_quality_score(visitante, liga_pronostico, como_local=False)

    sqs_global = round((sqs_local['score'] + sqs_visit['score']) / 2)

    # ========== 4.2 Intervalos de confianza ==========
    n_ef_local = calcular_n_efectivo_por_condicion(local, como_local=True, liga_pronostico=liga_pronostico)
    n_ef_visit = calcular_n_efectivo_por_condicion(visitante, como_local=False, liga_pronostico=liga_pronostico)

    n_efectivo = min(n_ef_local['n_efectivo_total'], n_ef_visit['n_efectivo_total'])

    n_efectivo_detalle = {
        'local': n_ef_local,
        'visitante': n_ef_visit,
        'usado_en_intervalos': round(n_efectivo, 2),
    }

    intervalos = {}
    for clave in ['local', 'empate', 'visitante']:
        prob = mercados['1X2'][clave]
        intervalo = calcular_intervalo_confianza(prob, n_efectivo)
        intervalos[clave] = {
            'prob': prob,
            'min': intervalo[0],
            'max': intervalo[1],
        }

    intervalos['BTTS'] = {
        'prob': mercados['BTTS'],
        'min': calcular_intervalo_confianza(mercados['BTTS'], n_efectivo)[0],
        'max': calcular_intervalo_confianza(mercados['BTTS'], n_efectivo)[1],
    }

    if 2.5 in mercados['over']:
        intervalos['Over_2_5'] = {
            'prob': mercados['over'][2.5],
            'min': calcular_intervalo_confianza(mercados['over'][2.5], n_efectivo)[0],
            'max': calcular_intervalo_confianza(mercados['over'][2.5], n_efectivo)[1],
        }

    confianza = calcular_nivel_confianza(
        partidos_local=resultado_local['partidos'],
        partidos_visitante=resultado_visit['partidos'],
        tiene_h2h=(h2h['total'] > 0),
        tiene_tendencia_clara=tiene_tendencia
    )

    # ========== 5. Jugadores ==========
    goleadores_local = obtener_top_jugadores_probabilidades(local, 'goleadores', 5, liga_pronostico)
    goleadores_visit = obtener_top_jugadores_probabilidades(visitante, 'goleadores', 5, liga_pronostico)
    tiros_local = obtener_top_jugadores_probabilidades(local, 'tiros', 5, liga_pronostico)
    tiros_visit = obtener_top_jugadores_probabilidades(visitante, 'tiros', 5, liga_pronostico)
    faltas_local = obtener_top_jugadores_probabilidades(local, 'faltas', 5, liga_pronostico)
    faltas_visit = obtener_top_jugadores_probabilidades(visitante, 'faltas', 5, liga_pronostico)
    porteros_local = obtener_top_jugadores_probabilidades(local, 'porteros', 3, liga_pronostico)
    porteros_visit = obtener_top_jugadores_probabilidades(visitante, 'porteros', 3, liga_pronostico)

    # ========== 6. Construir respuesta ==========
    stats_local = resultado_local['stats_equipo']
    stats_visit = resultado_visit['stats_equipo']

    return {
        'error': None,
        'version_motor': VERSION_MOTOR,
        'local': local,
        'visitante': visitante,
        'lambdas': {
            'local': lambda_local,
            'visitante': lambda_visit,
            'total_esperado': round(lambda_local + lambda_visit, 2)
        },
        'estadisticas_equipo': {
            'local': {
                'partidos': resultado_local['partidos'],
                'goles_avg': round(stats_local['goles'], 2) if stats_local['goles'] is not None else None,
                'tiros_avg': round(stats_local['tiros'], 2) if stats_local['tiros'] is not None else None,
                'tiros_puerta_avg': round(stats_local['tiros_puerta'], 2) if stats_local['tiros_puerta'] is not None else None,
                'corners_avg': round(stats_local['corners'], 2) if stats_local['corners'] is not None else None,
                'faltas_avg': round(stats_local['faltas'], 2) if stats_local['faltas'] is not None else None,
                'paradas_avg': round(stats_local['paradas'], 2) if stats_local['paradas'] is not None else None,
                'tarjetas_amarillas_avg': round(stats_local['tarjetas_amarillas'], 2) if stats_local['tarjetas_amarillas'] is not None else None,
                'tarjetas_rojas_avg': round(stats_local['tarjetas_rojas'], 2) if stats_local['tarjetas_rojas'] is not None else None,
                'factor_localia': resultado_local.get('factor_localia', 1.0),
                'localia_liga': resultado_local.get('localia_liga'),
                'factor_tendencia': resultado_local.get('factor_tendencia', 1.0),
                'ataque_equipo': resultado_local.get('ataque_equipo'),
                'defensa_rival': resultado_local.get('defensa_rival'),
                'ataque_crudo': resultado_local.get('ataque_crudo'),
                'defensa_cruda': resultado_local.get('defensa_cruda'),
                'ataque_suavizado': resultado_local.get('ataque_suavizado'),
                'defensa_suavizada': resultado_local.get('defensa_suavizada'),
                'factor_suavizado_k': resultado_local.get('factor_suavizado_k', 5.0),
                'promedio_liga': resultado_local.get('promedio_liga'),
                'cobertura_promedio': resultado_local.get('cobertura_promedio', 0),
                'cobertura_campos': stats_local.get('cobertura', {}) if stats_local else {},
                'contexto': resultado_local.get('contexto'),
                'factor_ratio': resultado_local.get('factor_ratio'),
                'ratio_valor': resultado_local.get('ratio_valor'),
                'factor_diferencial': resultado_local.get('factor_diferencial'),
                'diferencial_valor': resultado_local.get('diferencial_valor'),
                'factor_racha_v2': resultado_local.get('factor_racha_v2'),
                'racha_v2_tipo': resultado_local.get('racha_v2_tipo'),
            },
            'visitante': {
                'partidos': resultado_visit['partidos'],
                'goles_avg': round(stats_visit['goles'], 2) if stats_visit['goles'] is not None else None,
                'tiros_avg': round(stats_visit['tiros'], 2) if stats_visit['tiros'] is not None else None,
                'tiros_puerta_avg': round(stats_visit['tiros_puerta'], 2) if stats_visit['tiros_puerta'] is not None else None,
                'corners_avg': round(stats_visit['corners'], 2) if stats_visit['corners'] is not None else None,
                'faltas_avg': round(stats_visit['faltas'], 2) if stats_visit['faltas'] is not None else None,
                'paradas_avg': round(stats_visit['paradas'], 2) if stats_visit['paradas'] is not None else None,
                'tarjetas_amarillas_avg': round(stats_visit['tarjetas_amarillas'], 2) if stats_visit['tarjetas_amarillas'] is not None else None,
                'tarjetas_rojas_avg': round(stats_visit['tarjetas_rojas'], 2) if stats_visit['tarjetas_rojas'] is not None else None,
                'factor_localia': resultado_visit.get('factor_localia', 1.0),
                'factor_tendencia': resultado_visit.get('factor_tendencia', 1.0),
                'ataque_equipo': resultado_visit.get('ataque_equipo'),
                'defensa_rival': resultado_visit.get('defensa_rival'),
                'ataque_crudo': resultado_visit.get('ataque_crudo'),
                'defensa_cruda': resultado_visit.get('defensa_cruda'),
                'ataque_suavizado': resultado_visit.get('ataque_suavizado'),
                'defensa_suavizada': resultado_visit.get('defensa_suavizada'),
                'factor_suavizado_k': resultado_visit.get('factor_suavizado_k', 5.0),
                'promedio_liga': resultado_visit.get('promedio_liga'),
                'cobertura_promedio': resultado_visit.get('cobertura_promedio', 0),
                'cobertura_campos': stats_visit.get('cobertura', {}) if stats_visit else {},
                'contexto': resultado_visit.get('contexto'),
                'factor_ratio': resultado_visit.get('factor_ratio'),
                'ratio_valor': resultado_visit.get('ratio_valor'),
                'factor_diferencial': resultado_visit.get('factor_diferencial'),
                'diferencial_valor': resultado_visit.get('diferencial_valor'),
                'factor_racha_v2': resultado_visit.get('factor_racha_v2'),
                'racha_v2_tipo': resultado_visit.get('racha_v2_tipo'),
            }
        },
        'tendencias': {
            'local': resultado_local['tendencia'],
            'visitante': resultado_visit['tendencia']
        },
        'h2h': h2h,
        'anomalias': anomalias,
        'sample_quality': {
            'local': sqs_local,
            'visitante': sqs_visit,
            'global': sqs_global
        },
        'distribuciones': {
            'local': dist_local,
            'visitante': dist_visit,
        },
        'intervalos_confianza': intervalos,
        'n_efectivo': round(n_efectivo, 2),
        'n_efectivo_detalle': n_efectivo_detalle,
        'confianza': confianza,
        'mercados': mercados,
        'mercados_corners': mercados_corners,
        'mercados_tarjetas': mercados_tarjetas,
        'rachas': {
            'local': resultado_local.get('racha_info'),
            'visitante': resultado_visit.get('racha_info')
        },
        'ventanas': {
            'local': resultado_local.get('ventanas_info'),
            'visitante': resultado_visit.get('ventanas_info')
        },
        'goles_esperados': {
            'local': round(lambda_local, 2),
            'visitante': round(lambda_visit, 2),
            'total': round(lambda_local + lambda_visit, 2)
        },
        'jugadores': {
            'local': {
                'goleadores': goleadores_local,
                'tiros': tiros_local,
                'faltas': faltas_local,
                'porteros': porteros_local
            },
            'visitante': {
                'goleadores': goleadores_visit,
                'tiros': tiros_visit,
                'faltas': faltas_visit,
                'porteros': porteros_visit
            }
        }
    }


# ============================================================
# ENDPOINT /pronosticar
# ============================================================
@bp_pronostico.route('/pronosticar', methods=['POST'])
def pronosticar():
    data = request.json
    local = data.get('local', '')
    visitante = data.get('visitante', '')
    cuota = data.get('cuota', 0)
    liga = data.get('liga', '')

    # ========== NUEVO: bankroll + stake mínimo para Kelly ==========
    try:
        bankroll = float(data.get('bankroll', 10000))
    except (ValueError, TypeError):
        bankroll = 10000.0
    if bankroll <= 0:
        bankroll = 10000.0

    try:
        stake_minimo = float(data.get('stake_minimo', 500))
    except (ValueError, TypeError):
        stake_minimo = 500.0
    if stake_minimo < 0:
        stake_minimo = 0.0

    if not local or not visitante:
        return jsonify({'error': 'Selecciona ambos equipos'})

    local_norm = normalizar_equipo(local)
    visitante_norm = normalizar_equipo(visitante)

    pronostico = pronosticar_partido(local_norm, visitante_norm, liga_pronostico=liga)

    if pronostico.get('error'):
        return jsonify(pronostico)

    # ===== Extraer probabilidades =====
    mercados = pronostico.get('mercados', {})
    
    from database.aprendizaje import aplicar_calibracion
    probs = {
        'local': mercados.get('1X2', {}).get('local', 0),
        'empate': mercados.get('1X2', {}).get('empate', 0),
        'visitante': mercados.get('1X2', {}).get('visitante', 0),
        'BTTS': mercados.get('BTTS', 0),
        'Over_2_5': mercados.get('over', {}).get(2.5, 0),
        'Over_3_5': mercados.get('over', {}).get(3.5, 0),
        'Local_ML': mercados.get('1X2', {}).get('local', 0),
        'Visitante_ML': mercados.get('1X2', {}).get('visitante', 0),
        'Double_Chance_1X': mercados.get('doble_oportunidad', {}).get('1X', 0),
        'Double_Chance_X2': mercados.get('doble_oportunidad', {}).get('X2', 0),
        'Local_Over_1_5': (mercados.get('goles_local', {}).get('2', 0) +
                          mercados.get('goles_local', {}).get('3+', 0)),
        'Visitante_Over_1_5': (mercados.get('goles_visitante', {}).get('2', 0) +
                              mercados.get('goles_visitante', {}).get('3+', 0))
    }

    # ===== Calcular valor esperado =====
    valor_resultados = []

    nombres_mercado = {
        'local': '1X2 - Local',
        'empate': '1X2 - Empate',
        'visitante': '1X2 - Visitante',
        'BTTS': 'BTTS Sí',
        'Over_2_5': 'Over 2.5',
        'Over_3_5': 'Over 3.5',
        'Local_ML': 'Local Gana',
        'Visitante_ML': 'Visitante Gana',
        'Double_Chance_1X': 'Doble Oportunidad 1X',
        'Double_Chance_X2': 'Doble Oportunidad X2',
        'Local_Over_1_5': 'Local +1.5',
        'Visitante_Over_1_5': 'Visitante +1.5'
    }

    # ===== GOLES =====
    for clave, nombre in nombres_mercado.items():
        if clave in probs:
            prob = probs[clave]
            if prob <= 0:
                continue

            if cuota > 0:
                ev = (prob * cuota) - 1
                cuota_justa = 1 / prob
                valor_resultados.append({
                    'mercado': nombre,
                    'categoria': 'goles',
                    'probabilidad': prob,
                    'cuota': cuota,
                    'cuota_justa': round(cuota_justa, 2),
                    'EV': round(ev * 100, 2),
                    'tiene_cuota': True
                })
            else:
                valor_resultados.append({
                    'mercado': nombre,
                    'categoria': 'goles',
                    'probabilidad': prob,
                    'cuota': None,
                    'cuota_justa': round(1 / prob, 2) if prob > 0 else 0,
                    'EV': None,
                    'tiene_cuota': False
                })

    # ===== CÓRNERS =====
    mercados_corners = pronostico.get('mercados_corners')
    if mercados_corners and mercados_corners.get('over'):
        for linea, prob in mercados_corners['over'].items():
            if prob <= 0:
                continue
            nombre = f'Over {linea} córners'
            if cuota > 0:
                ev = (prob * cuota) - 1
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'corners',
                    'probabilidad': prob, 'cuota': cuota,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': round(ev * 100, 2), 'tiene_cuota': True
                })
            else:
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'corners',
                    'probabilidad': prob, 'cuota': None,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': None, 'tiene_cuota': False
                })

        for linea, prob in mercados_corners['under'].items():
            if prob <= 0:
                continue
            nombre = f'Under {linea} córners'
            if cuota > 0:
                ev = (prob * cuota) - 1
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'corners',
                    'probabilidad': prob, 'cuota': cuota,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': round(ev * 100, 2), 'tiene_cuota': True
                })
            else:
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'corners',
                    'probabilidad': prob, 'cuota': None,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': None, 'tiene_cuota': False
                })

    # ===== TARJETAS =====
    mercados_tarjetas = pronostico.get('mercados_tarjetas')
    if mercados_tarjetas and mercados_tarjetas.get('over'):
        for linea, prob in mercados_tarjetas['over'].items():
            if prob <= 0:
                continue
            nombre = f'Over {linea} tarjetas'
            if cuota > 0:
                ev = (prob * cuota) - 1
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'tarjetas',
                    'probabilidad': prob, 'cuota': cuota,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': round(ev * 100, 2), 'tiene_cuota': True
                })
            else:
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'tarjetas',
                    'probabilidad': prob, 'cuota': None,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': None, 'tiene_cuota': False
                })

        for linea, prob in mercados_tarjetas['under'].items():
            if prob <= 0:
                continue
            nombre = f'Under {linea} tarjetas'
            if cuota > 0:
                ev = (prob * cuota) - 1
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'tarjetas',
                    'probabilidad': prob, 'cuota': cuota,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': round(ev * 100, 2), 'tiene_cuota': True
                })
            else:
                valor_resultados.append({
                    'mercado': nombre, 'categoria': 'tarjetas',
                    'probabilidad': prob, 'cuota': None,
                    'cuota_justa': round(1 / prob, 2),
                    'EV': None, 'tiene_cuota': False
                })

    valor_resultados.sort(key=lambda x: (x['EV'] is None, -(x['EV'] or 0)))
    pronostico['valor'] = valor_resultados
    pronostico['probabilidades'] = probs
    pronostico['local'] = local_norm
    pronostico['visitante'] = visitante_norm

    # ===== EDGE AJUSTADO =====
    if cuota > 0:
        n_efectivo = pronostico.get('n_efectivo', 5)
        intervalos = pronostico.get('intervalos_confianza', {})

        for v in valor_resultados:
            if not v.get('tiene_cuota'):
                continue

            mercado_key = None
            if '1X2 - Local' in v['mercado']:
                mercado_key = 'local'
            elif '1X2 - Empate' in v['mercado']:
                mercado_key = 'empate'
            elif '1X2 - Visitante' in v['mercado']:
                mercado_key = 'visitante'
            elif 'BTTS' in v['mercado']:
                mercado_key = 'BTTS'
            elif 'Over 2.5' in v['mercado']:
                mercado_key = 'Over_2_5'

            if mercado_key and mercado_key in intervalos:
                intervalo = intervalos[mercado_key]
                edge = calcular_edge_ajustado(
                    v['probabilidad'],
                    intervalo['min'],
                    intervalo['max'],
                    v['cuota'],
                    n_efectivo
                )
                if edge:
                    v['edge_ajustado'] = edge['edge_ajustado']
                    v['ev_min'] = edge['ev_min']
                    v['ev_max'] = edge['ev_max']
                    v['decision'] = edge['decision']
                    v['razon'] = edge['razon']

    # ===== KELLY (11.3) =====
    # Para cada value bet con cuota, calcular stake sugerido con las 4 fracciones
    if cuota > 0:
        for v in valor_resultados:
            if not v.get('tiene_cuota') or not v.get('cuota'):
                continue

            prob_para_kelly = v.get('probabilidad', 0)

            try:
                kelly_data = calcular_kelly_multiples_fracciones(
                    prob=prob_para_kelly,
                    cuota=v['cuota'],
                    bankroll=bankroll
                )

                # ========== Aplicar stake mínimo ==========
                if kelly_data:
                    for key in ['completo', 'medio', 'cuarto', 'octavo']:
                        k = kelly_data.get(key)
                        if not k:
                            continue
                        # Solo ajustar si Kelly > 0 (hay value) y stake < mínimo
                        if k['stake_dinero'] > 0 and k['stake_dinero'] < stake_minimo:
                            k['stake_dinero'] = stake_minimo
                            k['stake_minimo_aplicado'] = True
                            if k['stake_pct'] > 0:
                                k['stake_pct'] = stake_minimo / bankroll
                        else:
                            k['stake_minimo_aplicado'] = False

                v['kelly'] = kelly_data
            except Exception as e:
                v['kelly'] = None

    # Añadir bankroll usado a la respuesta (para que el frontend lo sepa)
    pronostico['bankroll_usado'] = bankroll
    pronostico['stake_minimo_usado'] = stake_minimo

    return jsonify(pronostico)


# ============================================================
# ENDPOINT /pronosticar-por-id
# ============================================================
def pronosticar_partido_por_id(local_id, visitante_id, liga_pronostico=None):
    """
    Versión por ID de pronosticar_partido().
    Internamente convierte IDs a nombres y usa la función existente.
    """
    from database.motor_estadistico import obtener_nombre_equipo

    local = obtener_nombre_equipo(local_id)
    visitante = obtener_nombre_equipo(visitante_id)

    if not local:
        return {'error': f'Equipo con ID {local_id} no encontrado'}
    if not visitante:
        return {'error': f'Equipo con ID {visitante_id} no encontrado'}

    return pronosticar_partido(local, visitante, liga_pronostico=liga_pronostico)


@bp_pronostico.route('/pronosticar-por-id', methods=['POST'])
def pronosticar_por_id():
    """Versión del endpoint /pronosticar que acepta IDs."""
    data = request.json
    local_id = data.get('local_id')
    visitante_id = data.get('visitante_id')
    cuota = data.get('cuota', 0)
    liga = data.get('liga', '')

    if not local_id or not visitante_id:
        return jsonify({'error': 'Selecciona ambos equipos'})

    pronostico = pronosticar_partido_por_id(local_id, visitante_id, liga_pronostico=liga)

    if pronostico.get('error'):
        return jsonify(pronostico)

    return jsonify(pronostico)
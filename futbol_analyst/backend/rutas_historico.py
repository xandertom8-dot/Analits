# ============================================================
# backend/rutas_historico.py
# Blueprint: gestión de partidos del histórico.
# Endpoints:
#   POST   /preview
#   POST   /guardar
#   GET    /historico
#   DELETE /eliminar/<id>
#   DELETE /eliminar-todo
#   GET    /partido/<id>
#   PUT    /editar/<id>
# ============================================================

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime

from backend.db import DB_PATH
from backend.parser import parsear_estadisticas, parsear_texto_unificado
from database.aliases_equipos import normalizar_equipo


bp_historico = Blueprint('historico', __name__)


# ============================================================
# PREVIEW
# ============================================================
@bp_historico.route('/preview', methods=['POST'])
def preview():
    """
    Genera una vista previa SIN guardar. Solo para validación.
    
    Detecta automáticamente si el texto es:
    - Unificado (===== ESTADÍSTICAS... + ===== TIMELINE...)
    - Antiguo (solo tabla de jugadores en cada textarea)
    """
    data = request.json
    estadisticasLocal = data.get('estadisticasLocal', '')
    estadisticasVisitante = data.get('estadisticasVisitante', '')
    textoUnificado = data.get('textoUnificado', '')  # NUEVO: campo opcional
    local = data.get('local', 'Local')
    visitante = data.get('visitante', 'Visitante')

    # ========== MODO UNIFICADO ==========
    if textoUnificado and textoUnificado.strip():
        unificado = parsear_texto_unificado(textoUnificado)
        
        parsed_local = unificado.get('equipo_local') or {}
        parsed_visitante = unificado.get('equipo_visitante') or {}
        timeline = unificado.get('timeline') or {}
        resumen = unificado.get('resumen_unificado', {})
        
        # Combinar advertencias
        adv_local = parsed_local.get('advertencias', [])
        adv_visitante = parsed_visitante.get('advertencias', [])
        
        # Aviso del timeline si hay discrepancias
        if resumen.get('discrepancia'):
            adv_local.append(f'📊 {resumen.get("mensaje", "Discrepancia en goles")}')
        
        return jsonify({
            'modo': 'unificado',
            'local': {
                'nombre': local,
                'error': parsed_local.get('error'),
                'valido': parsed_local.get('valido', False),
                'jugadores': len(parsed_local.get('jugadores', [])),
                'advertencias': adv_local,
                'campos_faltantes_total': sum(len(j.get('campos_faltantes', [])) for j in parsed_local.get('jugadores', []))
            },
            'visitante': {
                'nombre': visitante,
                'error': parsed_visitante.get('error'),
                'valido': parsed_visitante.get('valido', False),
                'jugadores': len(parsed_visitante.get('jugadores', [])),
                'advertencias': adv_visitante,
                'campos_faltantes_total': sum(len(j.get('campos_faltantes', [])) for j in parsed_visitante.get('jugadores', []))
            },
            'timeline': {
                'eventos_local': len(timeline.get('local', [])),
                'eventos_visitante': len(timeline.get('visitante', [])),
                'resumen': timeline.get('resumen', {}),
            },
            'resumen_unificado': resumen,
        })
    
    # ========== MODO ANTIGUO ==========
    parsed_local = parsear_estadisticas(estadisticasLocal)
    parsed_visitante = parsear_estadisticas(estadisticasVisitante)

    return jsonify({
        'modo': 'antiguo',
        'local': {
            'nombre': local,
            'error': parsed_local.get('error'),
            'valido': parsed_local.get('valido', False),
            'jugadores': len(parsed_local.get('jugadores', [])),
            'advertencias': parsed_local.get('advertencias', []),
            'campos_faltantes_total': sum(len(j.get('campos_faltantes', [])) for j in parsed_local.get('jugadores', []))
        },
        'visitante': {
            'nombre': visitante,
            'error': parsed_visitante.get('error'),
            'valido': parsed_visitante.get('valido', False),
            'jugadores': len(parsed_visitante.get('jugadores', [])),
            'advertencias': parsed_visitante.get('advertencias', []),
            'campos_faltantes_total': sum(len(j.get('campos_faltantes', [])) for j in parsed_visitante.get('jugadores', []))
        }
    })


# ============================================================
# GUARDAR
# ============================================================
@bp_historico.route('/guardar', methods=['POST'])
def guardar():
    """
    Guarda un partido en el histórico.
    
    Detecta automáticamente si el pegado es unificado o antiguo:
    - Unificado: contiene "===== ESTADÍSTICAS..." y "===== TIMELINE..."
      → Extrae local/visitante/timeline/OG automáticamente.
    - Antiguo: solo textareas separados de cada equipo.
      → Comportamiento actual con OG manual.
    """
    data = request.json
    local = data.get('local', '')
    visitante = data.get('visitante', '')
    local = normalizar_equipo(local)
    visitante = normalizar_equipo(visitante)
    fecha = data.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    pais = data.get('pais', '')
    liga = data.get('liga', '')
    temporada = data.get('temporada', '')
    forzar_guardado = data.get('forzar_guardado', False)
    
    # ========== Detectar modo ==========
    texto_unificado = data.get('textoUnificado', '')
    estadisticasLocal = data.get('estadisticasLocal', '')
    estadisticasVisitante = data.get('estadisticasVisitante', '')
    
    timeline_data = None
    resumen_timeline = None
    og_local = 0
    og_visitante = 0
    
    # ========== MODO UNIFICADO ==========
    if texto_unificado and texto_unificado.strip():
        unificado = parsear_texto_unificado(texto_unificado)
        
        parsed_local = unificado.get('equipo_local') or {}
        parsed_visitante = unificado.get('equipo_visitante') or {}
        timeline_data = unificado.get('timeline')
        resumen_unificado = unificado.get('resumen_unificado', {})
        
        # Guardar el texto original crudo (el texto_unificado completo)
        estadisticasLocal = parsed_local.get('texto_original', '') or ''
        estadisticasVisitante = parsed_visitante.get('texto_original', '') or ''
        
        # Extraer OG automáticamente del timeline
        og_local = resumen_unificado.get('og_local', 0)
        og_visitante = resumen_unificado.get('og_visitante', 0)
        
        # Resumen reducido del timeline (para consultas rápidas)
        resumen_timeline = {
            'goles_local': resumen_unificado.get('goles_local_timeline', 0),
            'goles_visitante': resumen_unificado.get('goles_visitante_timeline', 0),
            'og_local': og_local,
            'og_visitante': og_visitante,
            'penaltis_fallados_local': timeline_data['resumen']['penaltis_fallados']['local'] if timeline_data else 0,
            'penaltis_fallados_visitante': timeline_data['resumen']['penaltis_fallados']['visitante'] if timeline_data else 0,
            'tarjetas_local': timeline_data['resumen']['tarjetas_local'] if timeline_data else 0,
            'tarjetas_visitante': timeline_data['resumen']['tarjetas_visitante'] if timeline_data else 0,
            'sustituciones_local': timeline_data['resumen']['sustituciones_local'] if timeline_data else 0,
            'sustituciones_visitante': timeline_data['resumen']['sustituciones_visitante'] if timeline_data else 0,
        }
    
    # ========== MODO ANTIGUO ==========
    else:
        parsed_local = parsear_estadisticas(estadisticasLocal)
        parsed_visitante = parsear_estadisticas(estadisticasVisitante)
        
        # OG manuales (del formulario antiguo)
        try:
            og_local = int(data.get('og_local', 0)) or 0
            og_visitante = int(data.get('og_visitante', 0)) or 0
        except (ValueError, TypeError):
            og_local = 0
            og_visitante = 0
        
        og_local = max(0, og_local)
        og_visitante = max(0, og_visitante)
    
    # ========== Validaciones comunes ==========
    if not local or not visitante:
        return jsonify({'error': 'Faltan datos obligatorios'})
    
    if parsed_local.get('error'):
        return jsonify({'error': f'Local: {parsed_local["error"]}'})
    if parsed_visitante.get('error'):
        return jsonify({'error': f'Visitante: {parsed_visitante["error"]}'})
    
    todas_advertencias = parsed_local.get('advertencias', []) + parsed_visitante.get('advertencias', [])
    
    if todas_advertencias and not forzar_guardado:
        return jsonify({
            'requiere_confirmacion': True,
            'advertencias': todas_advertencias,
            'local_jugadores': len(parsed_local.get('jugadores', [])),
            'visitante_jugadores': len(parsed_visitante.get('jugadores', []))
        })
    
    # ========== Guardar en BD ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Verificar duplicados
        c.execute('''
            SELECT id, estadisticas_local_raw, estadisticas_visitante_raw 
            FROM partidos 
            WHERE local = ? AND visitante = ?
        ''', (local, visitante))
        
        existing = c.fetchall()
        for row in existing:
            if row[1] == estadisticasLocal and row[2] == estadisticasVisitante:
                conn.close()
                return jsonify({
                    'error': f'⚠️ Ya existe un partido IDÉNTICO entre {local} y {visitante} (ID: {row[0]}).'
                })
        
        # Preparar JSON del timeline
        timeline_json_str = json.dumps(timeline_data, ensure_ascii=False) if timeline_data else None
        resumen_timeline_str = json.dumps(resumen_timeline, ensure_ascii=False) if resumen_timeline else None
        
        # Insertar partido
        tiene_advertencias = 1 if todas_advertencias else 0
        advertencias_json = json.dumps(todas_advertencias, ensure_ascii=False) if todas_advertencias else None
        
        c.execute('''
            INSERT INTO partidos 
            (fecha, pais, liga, temporada, local, visitante, 
             estadisticas_local_raw, estadisticas_visitante_raw,
             jugadores_local, jugadores_visitante, fecha_creacion,
             tiene_advertencias, advertencias,
             og_local, og_visitante,
             timeline_json, resumen_timeline_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fecha, pais, liga, temporada, local, visitante,
            estadisticasLocal, estadisticasVisitante,
            len(parsed_local.get('jugadores', [])),
            len(parsed_visitante.get('jugadores', [])),
            datetime.now().isoformat(),
            tiene_advertencias, advertencias_json,
            og_local, og_visitante,
            timeline_json_str, resumen_timeline_str
        ))
        
        partido_id = c.lastrowid
        
        # Insertar estadísticas del local (código sin cambios)
        for jugador in parsed_local.get('jugadores', []):
            stats = jugador['stats']
            campos_faltantes_str = ','.join(jugador.get('campos_faltantes', [])) if jugador.get('campos_faltantes') else None
            c.execute('''
                INSERT INTO estadisticas_local 
                (partido_id, jugador, G, A, TR, TA, Crn, S, SOnT, BS, P, C, E, O, FC, FR, SAV, campos_faltantes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                partido_id, jugador['nombre'],
                stats.get('G'), stats.get('A'), stats.get('TR'), stats.get('TA'),
                stats.get('Crn'), stats.get('S'), stats.get('SOnT'), stats.get('BS'),
                stats.get('P'), stats.get('C'), stats.get('E'), stats.get('O'),
                stats.get('FC'), stats.get('FR'), stats.get('SAV'),
                campos_faltantes_str
            ))
        
        # Insertar estadísticas del visitante (código sin cambios)
        for jugador in parsed_visitante.get('jugadores', []):
            stats = jugador['stats']
            campos_faltantes_str = ','.join(jugador.get('campos_faltantes', [])) if jugador.get('campos_faltantes') else None
            c.execute('''
                INSERT INTO estadisticas_visitante 
                (partido_id, jugador, G, A, TR, TA, Crn, S, SOnT, BS, P, C, E, O, FC, FR, SAV, campos_faltantes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                partido_id, jugador['nombre'],
                stats.get('G'), stats.get('A'), stats.get('TR'), stats.get('TA'),
                stats.get('Crn'), stats.get('S'), stats.get('SOnT'), stats.get('BS'),
                stats.get('P'), stats.get('C'), stats.get('E'), stats.get('O'),
                stats.get('FC'), stats.get('FR'), stats.get('SAV'),
                campos_faltantes_str
            ))
        
        # Verificar pronósticos pendientes (código sin cambios)
        pronosticos_pendientes = []
        if local and visitante:
            c.execute('''
                SELECT id, fecha_pronostico, prob_local, prob_empate, prob_visitante,
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
            
            for row in c.fetchall():
                pronosticos_pendientes.append({
                    'id': row[0],
                    'fecha_pronostico': row[1],
                    'prob_local': row[2],
                    'prob_empate': row[3],
                    'prob_visitante': row[4],
                    'prob_btts': row[5],
                    'prob_over25': row[6]
                })
        
        # Actualizar pronósticos cerrados con estos equipos (código sin cambios)
        pronosticos_actualizados = []
        if local and visitante:
            c.execute('''
                SELECT id FROM pronosticos
                WHERE cerrado = 1
                  AND (partido_id IS NULL OR partido_id = 0)
                  AND partido_local = ?
                  AND partido_visitante = ?
            ''', (local, visitante))
            
            ids_a_actualizar = [row[0] for row in c.fetchall()]
            
            for pid in ids_a_actualizar:
                try:
                    from backend.rutas_pronosticos import construir_resultado_mercados
                    mercados_json = construir_resultado_mercados(partido_id=partido_id)
                    mercados_json_str = json.dumps(mercados_json, ensure_ascii=False)
                    
                    c.execute('''
                        UPDATE pronosticos
                        SET resultado_mercados_json = ?,
                            partido_id = ?
                        WHERE id = ?
                    ''', (mercados_json_str, partido_id, pid))
                    
                    pronosticos_actualizados.append(pid)
                except Exception as e:
                    print(f"Error actualizando pronóstico {pid}: {e}")
        
        conn.commit()
        return jsonify({
            'success': True,
            'partido_id': partido_id,
            'advertencias_guardadas': len(todas_advertencias),
            'pronosticos_pendientes': pronosticos_pendientes,
            'pronosticos_actualizados': pronosticos_actualizados,
            'og_local': og_local,
            'og_visitante': og_visitante,
            'modo': 'unificado' if texto_unificado else 'antiguo',
            'tiene_timeline': timeline_data is not None,
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# HISTÓRICO (LISTADO CON FILTROS)
# ============================================================
@bp_historico.route('/historico')
def historico():
    """
    Lista partidos del histórico con:
    - Filtro por texto (local, visitante, liga)
    - Filtro por fecha (desde/hasta)
    - Paginación
    - Resultado y ganador
    """
    q = request.args.get('q', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()

    try:
        pagina = int(request.args.get('pagina', 1))
    except (ValueError, TypeError):
        pagina = 1
    try:
        por_pagina = int(request.args.get('por_pagina', 20))
    except (ValueError, TypeError):
        por_pagina = 20

    if pagina < 1:
        pagina = 1
    if por_pagina < 10 or por_pagina > 200:
        por_pagina = 20

    offset = (pagina - 1) * por_pagina

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        where = []
        params = []

        if q:
            where.append("""(
                LOWER(local) LIKE ? OR
                LOWER(visitante) LIKE ? OR
                LOWER(liga) LIKE ?
            )""")
            q_like = f'%{q.lower()}%'
            params.extend([q_like, q_like, q_like])

        if fecha_desde:
            where.append("fecha >= ?")
            params.append(fecha_desde)

        if fecha_hasta:
            where.append("fecha <= ?")
            params.append(fecha_hasta)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        c.execute(f"SELECT COUNT(*) FROM partidos {where_sql}", params)
        total = c.fetchone()[0]

        c.execute(f"""
            SELECT 
                id, fecha, local, visitante, liga, temporada,
                jugadores_local, jugadores_visitante, tiene_advertencias,
                (SELECT SUM(G) FROM estadisticas_local WHERE partido_id = partidos.id) as goles_local_jugadores,
                (SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = partidos.id) as goles_visitante_jugadores,
                COALESCE(og_local, 0) as og_local,
                COALESCE(og_visitante, 0) as og_visitante
            FROM partidos
            {where_sql}
            ORDER BY fecha DESC, id DESC
            LIMIT ? OFFSET ?
        """, params + [por_pagina, offset])

        rows = c.fetchall()
        resultados = []
        for row in rows:
            goles_local_jugadores = row[9] or 0
            goles_visitante_jugadores = row[10] or 0
            og_local = row[11] or 0
            og_visitante = row[12] or 0
            goles_local = goles_local_jugadores + og_visitante
            goles_visitante = goles_visitante_jugadores + og_local

            if goles_local > goles_visitante:
                ganador = 'local'
                ganador_label = '🏠 Local'
            elif goles_local < goles_visitante:
                ganador = 'visitante'
                ganador_label = '✈️ Visitante'
            else:
                ganador = 'empate'
                ganador_label = '🤝 Empate'

            resultados.append({
                'id': row[0],
                'fecha': row[1],
                'local': row[2],
                'visitante': row[3],
                'liga': row[4],
                'temporada': row[5],
                'jugadores_local': row[6],
                'jugadores_visitante': row[7],
                'jugadores': (row[6] or 0) + (row[7] or 0),
                'tiene_advertencias': row[8] or 0,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'resultado': f'{goles_local} - {goles_visitante}',
                'ganador': ganador,
                'ganador_label': ganador_label,
                'og_local': og_local,
                'og_visitante': og_visitante,
            })

        total_paginas = (total + por_pagina - 1) // por_pagina if total > 0 else 1

        return jsonify({
            'partidos': resultados,
            'paginacion': {
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total': total,
                'total_paginas': total_paginas,
                'tiene_anterior': pagina > 1,
                'tiene_siguiente': pagina < total_paginas,
            },
            'filtros': {
                'q': q,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# ELIMINAR
# ============================================================
@bp_historico.route('/eliminar/<int:partido_id>', methods=['DELETE'])
def eliminar_partido(partido_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('SELECT id FROM partidos WHERE id = ?', (partido_id,))
        if not c.fetchone():
            return jsonify({'error': 'Partido no encontrado'})

        c.execute('DELETE FROM estadisticas_local WHERE partido_id = ?', (partido_id,))
        c.execute('DELETE FROM estadisticas_visitante WHERE partido_id = ?', (partido_id,))
        c.execute('DELETE FROM analisis WHERE partido_id = ?', (partido_id,))
        c.execute('DELETE FROM partidos WHERE id = ?', (partido_id,))

        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


@bp_historico.route('/eliminar-todo', methods=['DELETE'])
def eliminar_todo():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('DELETE FROM analisis')
        c.execute('DELETE FROM estadisticas_local')
        c.execute('DELETE FROM estadisticas_visitante')
        c.execute('DELETE FROM partidos')
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('partidos', 'estadisticas_local', 'estadisticas_visitante', 'analisis')")
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()


# ============================================================
# EDITAR
# ============================================================
@bp_historico.route('/partido/<int:partido_id>', methods=['GET'])
def obtener_partido(partido_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute('''
            SELECT id, fecha, local, visitante, liga, temporada,
                   COALESCE(og_local, 0) as og_local, 
                   COALESCE(og_visitante, 0) as og_visitante,
                   timeline_json, resumen_timeline_json
            FROM partidos WHERE id = ?
        ''', (partido_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Partido no encontrado'})

        # Parsear timeline si existe
        timeline = None
        resumen_timeline = None
        
        if row['timeline_json']:
            try:
                timeline = json.loads(row['timeline_json'])
            except Exception:
                timeline = None
        
        if row['resumen_timeline_json']:
            try:
                resumen_timeline = json.loads(row['resumen_timeline_json'])
            except Exception:
                resumen_timeline = None

        return jsonify({
            'id': row['id'],
            'fecha': row['fecha'],
            'local': row['local'],
            'visitante': row['visitante'],
            'liga': row['liga'],
            'temporada': row['temporada'],
            'og_local': row['og_local'],
            'og_visitante': row['og_visitante'],
            'timeline': timeline,
            'resumen_timeline': resumen_timeline,
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()


@bp_historico.route('/editar/<int:partido_id>', methods=['PUT'])
def editar_partido(partido_id):
    data = request.json
    fecha = data.get('fecha')
    local = data.get('local')
    visitante = data.get('visitante')
    liga = data.get('liga')

    # ========== NUEVO: Leer OG ==========
    try:
        og_local = int(data.get('og_local', 0)) or 0
        og_visitante = int(data.get('og_visitante', 0)) or 0
    except (ValueError, TypeError):
        og_local = 0
        og_visitante = 0
    og_local = max(0, og_local)
    og_visitante = max(0, og_visitante)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE partidos 
            SET fecha = ?, local = ?, visitante = ?, liga = ?,
                og_local = ?, og_visitante = ?
            WHERE id = ?
        ''', (fecha, local, visitante, liga, og_local, og_visitante, partido_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()
        
# ============================================================
# ACTUALIZAR PARTIDO CON TEXTO UNIFICADO (FASE I)
# ============================================================
@bp_historico.route('/partido/<int:partido_id>/actualizar-unificado', methods=['POST'])
def actualizar_partido_unificado(partido_id):
    """
    Actualiza un partido existente con un nuevo texto unificado.
    
    Qué hace:
    1. Parsea el texto unificado (stats + timeline).
    2. BORRA las filas de estadisticas_local y estadisticas_visitante del partido.
    3. REINSERTA las nuevas filas parseadas.
    4. Actualiza timeline_json, resumen_timeline_json, og_local, og_visitante.
    5. Actualiza el texto crudo (estadisticas_local_raw, estadisticas_visitante_raw).
    6. Mantiene el id del partido (pronósticos vinculados siguen vinculados).
    7. Recalcula resultado_mercados_json de pronósticos cerrados vinculados.
    
    Body:
        {
            "textoUnificado": "...",
            "forzar_guardado": false
        }
    """
    data = request.json or {}
    texto_unificado = data.get('textoUnificado', '')
    forzar_guardado = data.get('forzar_guardado', False)
    
    if not texto_unificado or not texto_unificado.strip():
        return jsonify({'error': 'Falta el texto unificado'})
    
    # ========== 1. Verificar que el partido existe ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('SELECT id, local, visitante FROM partidos WHERE id = ?', (partido_id,))
        partido = c.fetchone()
        
        if not partido:
            return jsonify({'error': f'Partido {partido_id} no encontrado'})
        
        # ========== 2. Parsear texto unificado ==========
        unificado = parsear_texto_unificado(texto_unificado)
        
        if unificado['modo'] != 'unificado':
            return jsonify({
                'error': 'El texto no está en formato unificado. Debe contener "===== ESTADÍSTICAS DE JUGADORES =====" y "===== TIMELINE ====="'
            })
        
        parsed_local = unificado.get('equipo_local') or {}
        parsed_visitante = unificado.get('equipo_visitante') or {}
        timeline_data = unificado.get('timeline')
        resumen_unificado = unificado.get('resumen_unificado', {})
        
        if parsed_local.get('error'):
            return jsonify({'error': f'Local: {parsed_local["error"]}'})
        if parsed_visitante.get('error'):
            return jsonify({'error': f'Visitante: {parsed_visitante["error"]}'})
        
        todas_advertencias = parsed_local.get('advertencias', []) + parsed_visitante.get('advertencias', [])
        
        if todas_advertencias and not forzar_guardado:
            return jsonify({
                'requiere_confirmacion': True,
                'advertencias': todas_advertencias,
                'local_jugadores': len(parsed_local.get('jugadores', [])),
                'visitante_jugadores': len(parsed_visitante.get('jugadores', []))
            })
        
        # ========== 3. Extraer OG del timeline ==========
        og_local = resumen_unificado.get('og_local', 0)
        og_visitante = resumen_unificado.get('og_visitante', 0)
        
        # ========== 4. Preparar timeline y resumen ==========
        timeline_json_str = json.dumps(timeline_data, ensure_ascii=False) if timeline_data else None
        
        resumen_timeline = None
        if timeline_data:
            resumen_timeline = {
                'goles_local': resumen_unificado.get('goles_local_timeline', 0),
                'goles_visitante': resumen_unificado.get('goles_visitante_timeline', 0),
                'og_local': og_local,
                'og_visitante': og_visitante,
                'penaltis_fallados_local': timeline_data['resumen']['penaltis_fallados']['local'],
                'penaltis_fallados_visitante': timeline_data['resumen']['penaltis_fallados']['visitante'],
                'tarjetas_local': timeline_data['resumen']['tarjetas_local'],
                'tarjetas_visitante': timeline_data['resumen']['tarjetas_visitante'],
                'sustituciones_local': timeline_data['resumen']['sustituciones_local'],
                'sustituciones_visitante': timeline_data['resumen']['sustituciones_visitante'],
            }
        resumen_timeline_str = json.dumps(resumen_timeline, ensure_ascii=False) if resumen_timeline else None
        
        # ========== 5. BORRAR estadísticas antiguas ==========
        c.execute('DELETE FROM estadisticas_local WHERE partido_id = ?', (partido_id,))
        c.execute('DELETE FROM estadisticas_visitante WHERE partido_id = ?', (partido_id,))
        
        # ========== 6. INSERTAR nuevas estadísticas (local) ==========
        for jugador in parsed_local.get('jugadores', []):
            stats = jugador['stats']
            campos_faltantes_str = ','.join(jugador.get('campos_faltantes', [])) if jugador.get('campos_faltantes') else None
            c.execute('''
                INSERT INTO estadisticas_local 
                (partido_id, jugador, G, A, TR, TA, Crn, S, SOnT, BS, P, C, E, O, FC, FR, SAV, campos_faltantes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                partido_id, jugador['nombre'],
                stats.get('G'), stats.get('A'), stats.get('TR'), stats.get('TA'),
                stats.get('Crn'), stats.get('S'), stats.get('SOnT'), stats.get('BS'),
                stats.get('P'), stats.get('C'), stats.get('E'), stats.get('O'),
                stats.get('FC'), stats.get('FR'), stats.get('SAV'),
                campos_faltantes_str
            ))
        
        # ========== 7. INSERTAR nuevas estadísticas (visitante) ==========
        for jugador in parsed_visitante.get('jugadores', []):
            stats = jugador['stats']
            campos_faltantes_str = ','.join(jugador.get('campos_faltantes', [])) if jugador.get('campos_faltantes') else None
            c.execute('''
                INSERT INTO estadisticas_visitante 
                (partido_id, jugador, G, A, TR, TA, Crn, S, SOnT, BS, P, C, E, O, FC, FR, SAV, campos_faltantes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                partido_id, jugador['nombre'],
                stats.get('G'), stats.get('A'), stats.get('TR'), stats.get('TA'),
                stats.get('Crn'), stats.get('S'), stats.get('SOnT'), stats.get('BS'),
                stats.get('P'), stats.get('C'), stats.get('E'), stats.get('O'),
                stats.get('FC'), stats.get('FR'), stats.get('SAV'),
                campos_faltantes_str
            ))
        
        # ========== 8. ACTUALIZAR el partido ==========
        tiene_advertencias = 1 if todas_advertencias else 0
        advertencias_json = json.dumps(todas_advertencias, ensure_ascii=False) if todas_advertencias else None
        
        # Guardar los textos crudos originales (los del equipo 1 y equipo 2)
        estadisticasLocal_raw = parsed_local.get('texto_original', '') or ''
        estadisticasVisitante_raw = parsed_visitante.get('texto_original', '') or ''
        
        c.execute('''
            UPDATE partidos
            SET estadisticas_local_raw = ?,
                estadisticas_visitante_raw = ?,
                jugadores_local = ?,
                jugadores_visitante = ?,
                tiene_advertencias = ?,
                advertencias = ?,
                og_local = ?,
                og_visitante = ?,
                timeline_json = ?,
                resumen_timeline_json = ?
            WHERE id = ?
        ''', (
            estadisticasLocal_raw,
            estadisticasVisitante_raw,
            len(parsed_local.get('jugadores', [])),
            len(parsed_visitante.get('jugadores', [])),
            tiene_advertencias,
            advertencias_json,
            og_local,
            og_visitante,
            timeline_json_str,
            resumen_timeline_str,
            partido_id
        ))
        
        # ========== 9. Actualizar pronósticos vinculados ==========
        pronosticos_actualizados = []
        c.execute('''
            SELECT id FROM pronosticos
            WHERE partido_id = ?
        ''', (partido_id,))
        
        ids_pronosticos = [row[0] for row in c.fetchall()]
        
        for pid in ids_pronosticos:
            try:
                from backend.rutas_pronosticos import construir_resultado_mercados
                mercados_json = construir_resultado_mercados(partido_id=partido_id)
                mercados_json_str = json.dumps(mercados_json, ensure_ascii=False)
                
                # Actualizar el JSON de mercados
                c.execute('''
                    UPDATE pronosticos
                    SET resultado_mercados_json = ?,
                        resultado_local = ?,
                        resultado_visitante = ?
                    WHERE id = ?
                ''', (
                    mercados_json_str,
                    mercados_json['goles_local'],
                    mercados_json['goles_visitante'],
                    pid
                ))
                pronosticos_actualizados.append(pid)
            except Exception as e:
                print(f"Error actualizando pronóstico {pid}: {e}")
        
        conn.commit()
        
        # ========== 10. Recalcular aprendizaje ==========
        try:
            from database.aprendizaje import recalcular_aprendizaje_completo
            recalcular_aprendizaje_completo()
            print(f"[ACTUALIZAR-UNIFICADO] Aprendizaje recalculado tras actualizar partido {partido_id}")
        except Exception as e:
            print(f"[ACTUALIZAR-UNIFICADO] Error recalculando aprendizaje: {e}")
        
        return jsonify({
            'success': True,
            'partido_id': partido_id,
            'jugadores_local': len(parsed_local.get('jugadores', [])),
            'jugadores_visitante': len(parsed_visitante.get('jugadores', [])),
            'og_local': og_local,
            'og_visitante': og_visitante,
            'tiene_timeline': timeline_data is not None,
            'eventos_timeline_local': len(timeline_data['local']) if timeline_data else 0,
            'eventos_timeline_visitante': len(timeline_data['visitante']) if timeline_data else 0,
            'goles_local_reales': resumen_unificado.get('goles_local_reales', 0),
            'goles_visitante_reales': resumen_unificado.get('goles_visitante_reales', 0),
            'pronosticos_actualizados': pronosticos_actualizados,
            'advertencias': todas_advertencias,
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)})
    finally:
        conn.close()
# ============================================================
# backend/rutas_externo.py
# Blueprint: endpoints que exponen el cliente de Football-Data.org
# Endpoints:
#   GET  /api/externo/test
#   GET  /api/externo/competiciones
#   GET  /api/externo/partidos-dia?fecha=YYYY-MM-DD
#   POST /api/externo/buscar-partido
# ============================================================

from flask import Blueprint, jsonify, request

from backend.api_football import (
    probar_conexion,
    listar_competiciones,
    buscar_partidos_por_fecha,
    buscar_partido_por_equipos,
)
from database.aliases_equipos import normalizar_equipo


bp_externo = Blueprint('externo', __name__)


# ============================================================
# TEST DE CONEXIÓN
# ============================================================
@bp_externo.route('/api/externo/test')
def api_externo_test():
    """Prueba la conexión con Football-Data.org."""
    result = probar_conexion()
    return jsonify(result)


# ============================================================
# LISTAR COMPETICIONES
# ============================================================
@bp_externo.route('/api/externo/competiciones')
def api_externo_competiciones():
    """Lista las competiciones disponibles en el plan free."""
    result = listar_competiciones()
    return jsonify(result)


# ============================================================
# PARTIDOS DE UN DÍA
# ============================================================
@bp_externo.route('/api/externo/partidos-dia')
def api_externo_partidos_dia():
    """Lista partidos jugados en una fecha específica."""
    fecha = request.args.get('fecha', '').strip()
    
    if not fecha:
        return jsonify({'error': 'Falta parámetro "fecha" (YYYY-MM-DD)'}), 400
    
    result = buscar_partidos_por_fecha(fecha)
    return jsonify(result)


# ============================================================
# BUSCAR PARTIDO POR EQUIPOS
# ============================================================
@bp_externo.route('/api/externo/buscar-partido', methods=['POST'])
def api_externo_buscar_partido():
    """
    Busca un partido específico por equipos y fecha.
    
    Body:
        {
            "local": "Barcelona",
            "visitante": "Real Madrid",
            "fecha": "2026-09-15"  (opcional)
        }
    """
    data = request.json or {}
    local = data.get('local', '').strip()
    visitante = data.get('visitante', '').strip()
    fecha = data.get('fecha', '').strip() or None
    
    if not local or not visitante:
        return jsonify({'error': 'Faltan equipos'}), 400
    
    # Normalizar nombres a canónicos (para hacer match con aliases)
    local_norm = normalizar_equipo(local)
    visitante_norm = normalizar_equipo(visitante)
    
    result = buscar_partido_por_equipos(local_norm, visitante_norm, fecha)
    
    return jsonify({
        'encontrado': result.get('encontrado', False),
        'partido': result.get('partido'),
        'error': result.get('error'),
        'local_buscado': local_norm,
        'visitante_buscado': visitante_norm,
    })
    
@bp_externo.route('/api/externo/partidos-proximos')
def api_externo_partidos_proximos():
    """
    Lista partidos programados para los próximos N días.
    
    Query params:
        dias: cuántos días hacia adelante (default 7)
        ligas: códigos separados por coma (ej: "PL,PD,SA")
    """
    from backend.api_football import listar_partidos_proximos
    
    try:
        dias = int(request.args.get('dias', 7))
    except (ValueError, TypeError):
        dias = 7
    
    if dias < 1:
        dias = 1
    if dias > 14:
        dias = 14
    
    ligas_str = request.args.get('ligas', '').strip()
    ligas_codigos = [l.strip() for l in ligas_str.split(',') if l.strip()] if ligas_str else None
    
    result = listar_partidos_proximos(dias_adelante=dias, ligas_codigos=ligas_codigos)
    return jsonify(result)
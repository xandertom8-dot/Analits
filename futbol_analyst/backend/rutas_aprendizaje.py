# ============================================================
# backend/rutas_aprendizaje.py
# Blueprint: estado y control manual de la capa de aprendizaje.
# Endpoints:
#   GET  /api/aprendizaje/estado       -> ver qué ha aprendido el modelo
#   POST /api/aprendizaje/recalcular   -> forzar recálculo manual
# ============================================================

from flask import Blueprint, jsonify

from database.aprendizaje import (
    recalcular_aprendizaje_completo,
    estado_aprendizaje,
    init_tabla_aprendizaje,
)

bp_aprendizaje = Blueprint('aprendizaje', __name__)


@bp_aprendizaje.route('/api/aprendizaje/estado')
def api_aprendizaje_estado():
    init_tabla_aprendizaje()
    return jsonify(estado_aprendizaje())


@bp_aprendizaje.route('/api/aprendizaje/recalcular', methods=['POST'])
def api_aprendizaje_recalcular():
    from flask import request
    init_tabla_aprendizaje()
    
    data = request.json or {}
    fecha_corte = data.get('fecha_corte', None)
    
    try:
        resultado = recalcular_aprendizaje_completo(fecha_corte=fecha_corte)
        return jsonify({'success': True, **resultado})
    except Exception as e:
        return jsonify({'error': str(e)})

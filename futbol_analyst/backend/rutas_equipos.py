# ============================================================
# backend/rutas_equipos.py
# Blueprint: catálogos de equipos y ligas.
# Endpoints:
#   /api/continentes
#   /api/paises
#   /api/ligas
#   /api/temporadas
#   /api/equipos
#   /api/equipos-con-id
#   /api/team/<id>
#   /api/player/<id>
#   /api/buscar-equipo
# ============================================================

from flask import Blueprint, jsonify, request
import sqlite3
import json

from backend.db import DB_PATH


bp_equipos = Blueprint('equipos', __name__)


# ============================================================
# CATÁLOGOS EN CASCADA
# ============================================================

@bp_equipos.route('/api/continentes')
def api_continentes():
    try:
        from database.equipos import obtener_continentes
        return jsonify(obtener_continentes())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/paises')
def api_paises():
    try:
        from database.equipos import obtener_paises
        continente = request.args.get('continente')
        return jsonify(obtener_paises(continente))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/ligas')
def api_ligas():
    try:
        from database.equipos import obtener_ligas
        continente = request.args.get('continente')
        pais = request.args.get('pais')
        if not continente or not pais:
            return jsonify({'error': 'Faltan parámetros'}), 400
        return jsonify(obtener_ligas(continente, pais))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/temporadas')
def api_temporadas():
    try:
        from database.equipos import obtener_temporadas
        continente = request.args.get('continente')
        pais = request.args.get('pais')
        liga = request.args.get('liga')
        if not continente or not pais or not liga:
            return jsonify({'error': 'Faltan parámetros'}), 400
        return jsonify(obtener_temporadas(continente, pais, liga))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/equipos')
def api_equipos():
    try:
        from database.equipos import obtener_equipos
        continente = request.args.get('continente')
        pais = request.args.get('pais')
        liga = request.args.get('liga')
        temporada = request.args.get('temporada')
        if not continente or not pais or not liga or not temporada:
            return jsonify({'error': 'Faltan parámetros'}), 400
        return jsonify(obtener_equipos(continente, pais, liga, temporada))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/equipos-con-id')
def api_equipos_con_id():
    """Devuelve equipos de una liga con su ID"""
    try:
        from database.equipos import obtener_equipos
        from database.motor_estadistico import obtener_id_equipo
        from database.aliases_equipos import normalizar_equipo

        continente = request.args.get('continente')
        pais = request.args.get('pais')
        liga = request.args.get('liga')
        temporada = request.args.get('temporada')

        if not continente or not pais or not liga or not temporada:
            return jsonify({'error': 'Faltan parámetros'}), 400

        equipos_nombres = obtener_equipos(continente, pais, liga, temporada)

        equipos_con_id = []
        for nombre in equipos_nombres:
            nombre_norm = normalizar_equipo(nombre)
            team_id = obtener_id_equipo(nombre_norm)
            if team_id:
                equipos_con_id.append({
                    'id': team_id,
                    'name': nombre_norm
                })

        return jsonify(equipos_con_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# CONSULTAS POR ID
# ============================================================

@bp_equipos.route('/api/team/<int:team_id>')
def api_team(team_id):
    """Obtiene información de un equipo por ID"""
    try:
        from database.motor_estadistico import obtener_nombre_equipo
        nombre = obtener_nombre_equipo(team_id)
        if not nombre:
            return jsonify({'error': 'Equipo no encontrado'}), 404

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = c.fetchone()
        conn.close()

        return jsonify({
            'id': row['id'],
            'name': row['name'],
            'country': row['country'],
            'aliases': json.loads(row['aliases']) if row['aliases'] else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/player/<int:player_id>')
def api_player(player_id):
    """Obtiene información de un jugador por ID"""
    try:
        from database.motor_estadistico import obtener_nombre_jugador
        nombre = obtener_nombre_jugador(player_id)
        if not nombre:
            return jsonify({'error': 'Jugador no encontrado'}), 404

        return jsonify({
            'id': player_id,
            'name': nombre
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_equipos.route('/api/buscar-equipo')
def api_buscar_equipo():
    """Busca un equipo por nombre (incluyendo aliases)"""
    try:
        q = request.args.get('q', '').strip().lower()
        if not q:
            return jsonify([])

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT id, name, country, aliases
            FROM teams
            WHERE LOWER(name) LIKE ?
               OR LOWER(aliases) LIKE ?
            ORDER BY name
            LIMIT 20
        """, (f'%{q}%', f'%{q}%'))

        resultados = []
        for row in c.fetchall():
            resultados.append({
                'id': row['id'],
                'name': row['name'],
                'country': row['country']
            })

        conn.close()
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
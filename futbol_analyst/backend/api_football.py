# ============================================================
# backend/api_football.py
# Cliente para Football-Data.org (plan gratuito).
# 
# Docs: https://www.football-data.org/documentation/quickstart
# Cuota: 10 requests/minuto.
# ============================================================

import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error


# ============================================================
# CONFIGURACIÓN
# ============================================================
API_BASE_URL = 'https://api.football-data.org/v4'

# ============================================================
# MAPEO: nombre de liga interno → código Football-Data.org
# ============================================================
MAPEO_LIGAS = {
    # Inglaterra
    'premier league': 'PL',
    'championship': 'ELC',
    
    # España
    'laliga': 'PD',
    'laliga2': None,  # ❌ No disponible en plan free
    'laliga 2': None,
    'segunda division': None,
    
    # Países Bajos
    'eredivisie': 'DED',
    
    # Alemania
    'bundesliga': 'BL1',
    'bundesliga 2': 'BL2',
    
    # Italia
    'serie a': 'SA',
    'serie b': None,  # ❌ No disponible en plan free
    
    # Francia
    'ligue 1': 'FL1',
    'ligue 2': None,  # ❌ No disponible en plan free
    
    # Portugal
    'primeira liga': 'PPL',
    
    # UEFA
    'champions league': 'CL',
    'uefa champions league': 'CL',
    'europa league': 'EL',
    'uefa europa league': 'EL',
    'conference league': 'UCL',
    'uefa conference league': 'UCL',
}


def codigo_liga_api(nombre_liga):
    """Devuelve el código de Football-Data.org para una liga, o None si no está."""
    if not nombre_liga:
        return None
    return MAPEO_LIGAS.get(nombre_liga.lower().strip())

# La API key se lee de la variable de entorno FOOTBALL_DATA_API_KEY
# o del archivo backend/api_key.txt (si existe).
def _obtener_api_key():
    # 1. Variable de entorno (recomendado)
    key = os.environ.get('FOOTBALL_DATA_API_KEY')
    if key:
        return key.strip()
    
    # 2. Archivo local
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(backend_dir, 'api_key.txt')
    if os.path.exists(key_file):
        with open(key_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    return None


# ============================================================
# RATE LIMIT (10 req/min = 1 req cada 6s)
# ============================================================
_ULTIMA_LLAMADA = [0.0]  # lista para mutabilidad
_INTERVALO_MINIMO = 6.5  # segundos (con margen)


def _respetar_rate_limit():
    """Espera si es necesario para no superar 10 req/min."""
    ahora = time.time()
    delta = ahora - _ULTIMA_LLAMADA[0]
    if delta < _INTERVALO_MINIMO:
        time.sleep(_INTERVALO_MINIMO - delta)
    _ULTIMA_LLAMADA[0] = time.time()

# ============================================================
# NORMALIZACIÓN PARA MATCHING (quitar tildes, artículos, sufijos)
# ============================================================
import unicodedata

def _normalizar_para_match(nombre):
    """
    Normaliza un nombre de equipo para hacer matching robusto con la API.
    
    Ejemplos:
        'Mónaco' → 'monaco'
        'AS Monaco FC' → 'monaco'
        'Racing Club de Lens' → 'lens'
        'FC Bayern München' → 'bayern munchen'
        '1. FC Union Berlin' → 'union berlin'
    
    Estrategia:
    1. Quitar tildes/acentos.
    2. Minúsculas.
    3. Quitar puntuación.
    4. Eliminar palabras genéricas (as, fc, cf, sc, rc, club, de, 1., etc.).
    """
    if not nombre:
        return ''
    
    # 1. Quitar acentos
    nombre = unicodedata.normalize('NFD', nombre)
    nombre = ''.join(c for c in nombre if unicodedata.category(c) != 'Mn')
    
    # 2. Minúsculas
    nombre = nombre.lower()
    
    # 3. Quitar puntuación (excepto espacios)
    import re
    nombre = re.sub(r'[^\w\s]', ' ', nombre)
    
    # 4. Quitar palabras genéricas
    PALABRAS_IGNORAR = {
        'as', 'fc', 'cf', 'sc', 'rc', 'cd', 'ca', 'ac', 'afc',
        'club', 'de', 'del', 'la', 'el', 'los', 'las',
        'calcio', 'futbol', 'football', 'sport', 'sports',
        'racing', 'real', 'atletico', 'athletic',  # ojo: algunos son distintivos
        'cd', 'sd', 'ud', 'sv', 'vfl', 'vfb', 'tsg', 'bsc',
        '1', '2', '1899', '1900', '1907', '1911', '1913', '1846',
        'sg', 'fk', 'sk', 'nk', 'hk', 'if', 'bk',
        'united', 'city', 'town', 'rovers', 'wanderers', 'albion',
    }
    
    palabras = nombre.split()
    palabras_filtradas = [p for p in palabras if p not in PALABRAS_IGNORAR and len(p) > 1]
    
    # Si todo se filtró, devolvemos el nombre completo sin puntuación
    if not palabras_filtradas:
        palabras_filtradas = palabras
    
    return ' '.join(palabras_filtradas)

# ============================================================
# LLAMADA BASE A LA API
# ============================================================
def _api_get(path, params=None):
    """
    Hace una llamada GET a la API con manejo de errores.
    
    Args:
        path: ruta relativa (ej: '/matches')
        params: dict de query params
    
    Returns:
        {
            'ok': bool,
            'data': dict or None,
            'error': str or None,
            'status': int,
        }
    """
    api_key = _obtener_api_key()
    if not api_key:
        return {
            'ok': False,
            'data': None,
            'error': 'No se encontró API key. Configura FOOTBALL_DATA_API_KEY o backend/api_key.txt',
            'status': 0,
        }
    
    _respetar_rate_limit()
    
    url = API_BASE_URL + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(url)
    req.add_header('X-Auth-Token', api_key)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                'ok': True,
                'data': data,
                'error': None,
                'status': response.status,
            }
    except urllib.error.HTTPError as e:
        error_body = ''
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
        return {
            'ok': False,
            'data': None,
            'error': f'HTTP {e.code}: {error_body[:200]}',
            'status': e.code,
        }
    except urllib.error.URLError as e:
        return {
            'ok': False,
            'data': None,
            'error': f'URLError: {str(e)}',
            'status': 0,
        }
    except Exception as e:
        return {
            'ok': False,
            'data': None,
            'error': f'Error inesperado: {str(e)}',
            'status': 0,
        }


# ============================================================
# ENDPOINTS DE LA API
# ============================================================

def buscar_partidos_por_fecha(fecha):
    """
    Busca todos los partidos jugados en una fecha concreta.
    
    Args:
        fecha: string 'YYYY-MM-DD'
    
    Returns:
        Lista de partidos normalizados:
        [
            {
                'id': int,
                'fecha': 'YYYY-MM-DD',
                'local': str,
                'visitante': str,
                'goles_local': int,
                'goles_visitante': int,
                'estado': str,  # 'FINISHED', 'SCHEDULED', etc.
                'competicion': str,
            },
            ...
        ]
    """
    result = _api_get('/matches', {'date': fecha})
    
    if not result['ok']:
        return {'error': result['error'], 'partidos': []}
    
    data = result['data']
    partidos = []
    
    for m in data.get('matches', []):
        try:
            partido = {
                'id': m.get('id'),
                'fecha': (m.get('utcDate') or '')[:10],
                'local': m.get('homeTeam', {}).get('name', ''),
                'visitante': m.get('awayTeam', {}).get('name', ''),
                'goles_local': m.get('score', {}).get('fullTime', {}).get('home'),
                'goles_visitante': m.get('score', {}).get('fullTime', {}).get('away'),
                'estado': m.get('status', ''),
                'competicion': m.get('competition', {}).get('name', ''),
            }
            partidos.append(partido)
        except Exception:
            continue
    
    return {'error': None, 'partidos': partidos}


def buscar_partido_por_equipos(local, visitante, fecha=None):
    """
    Busca un partido específico entre dos equipos.
    
    Estrategia:
    - Normaliza nombres con _normalizar_para_match (quita tildes, artículos).
    - Busca primero en la fecha indicada (o hoy).
    - Si no encuentra, expande a un rango de ±3 días.
    - Compara por substring de tokens distintivos.
    
    Args:
        local: nombre del equipo local (o alias)
        visitante: nombre del equipo visitante
        fecha: opcional, 'YYYY-MM-DD'
    
    Returns:
        {
            'encontrado': bool,
            'partido': dict or None,
            'error': str or None,
            'fechas_buscadas': list,
        }
    """
    from datetime import datetime, timedelta
    
    local_n = _normalizar_para_match(local)
    visitante_n = _normalizar_para_match(visitante)
    
    if not local_n or not visitante_n:
        return {'encontrado': False, 'partido': None, 'error': 'Nombres vacíos'}
    
    # ========== Determinar fechas a buscar ==========
    fechas = []
    
    if fecha:
        # Rango ±3 días alrededor de la fecha indicada
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            for delta in [0, -1, 1, -2, 2, -3, 3]:
                f = (fecha_dt + timedelta(days=delta)).strftime('%Y-%m-%d')
                if f not in fechas:
                    fechas.append(f)
        except Exception:
            fechas = [fecha]
    else:
        # Últimos 7 días + hoy
        hoy = datetime.now().date()
        for i in range(0, -7, -1):
            fechas.append((hoy + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    fechas_buscadas = []
    
    for f in fechas:
        fechas_buscadas.append(f)
        result = buscar_partidos_por_fecha(f)
        
        if result.get('error'):
            continue
        
        for p in result['partidos']:
            p_local = _normalizar_para_match(p['local'])
            p_visit = _normalizar_para_match(p['visitante'])
            
            # Matching por intersección de tokens
            # Cualquier token de "local_n" que aparezca en "p_local" vale
            tokens_local_n = set(local_n.split())
            tokens_p_local = set(p_local.split())
            
            tokens_visit_n = set(visitante_n.split())
            tokens_p_visit = set(p_visit.split())
            
            # Match si hay intersección de al menos 1 token distintivo
            match_local = bool(tokens_local_n & tokens_p_local) or local_n in p_local or p_local in local_n
            match_visit = bool(tokens_visit_n & tokens_p_visit) or visitante_n in p_visit or p_visit in visitante_n
            
            if match_local and match_visit:
                return {
                    'encontrado': True,
                    'partido': p,
                    'error': None,
                    'fechas_buscadas': fechas_buscadas,
                }
    
    return {
        'encontrado': False,
        'partido': None,
        'error': None,
        'fechas_buscadas': fechas_buscadas,
    }


def listar_competiciones():
    """Lista las competiciones disponibles en el plan free."""
    result = _api_get('/competitions')
    
    if not result['ok']:
        return {'error': result['error'], 'competiciones': []}
    
    comps = []
    for c in result['data'].get('competitions', []):
        comps.append({
            'id': c.get('id'),
            'nombre': c.get('name'),
            'pais': c.get('area', {}).get('name'),
            'codigo': c.get('code'),
        })
    
    return {'error': None, 'competiciones': comps}


def probar_conexion():
    """
    Prueba rápida de conexión a la API.
    Útil para verificar que la API key funciona.
    """
    result = _api_get('/competitions')
    
    if result['ok']:
        num_comps = len(result['data'].get('competitions', []))
        return {
            'ok': True,
            'mensaje': f'✅ Conexión OK. {num_comps} competiciones disponibles.',
            'status': result['status'],
        }
    else:
        return {
            'ok': False,
            'mensaje': f'❌ Error: {result["error"]}',
            'status': result['status'],
        }
        
def listar_partidos_proximos(dias_adelante=7, ligas_codigos=None):
    """
    Lista partidos programados para los próximos N días.
    
    Args:
        dias_adelante: cuántos días hacia adelante mirar (default 7)
        ligas_codigos: lista de códigos de liga a filtrar (ej: ['PL', 'PD'])
                       Si None, devuelve todas las competiciones del plan free.
    
    Returns:
        {
            'partidos': [
                {
                    'id': int,
                    'fecha': 'YYYY-MM-DD',
                    'hora': 'HH:MM',
                    'local': str,
                    'visitante': str,
                    'estado': str,  # 'SCHEDULED', 'TIMED', 'IN_PLAY'
                    'competicion': str,
                    'codigo_competicion': str,
                    'jornada': int or None,
                },
                ...
            ],
            'error': str or None,
            'fechas_consultadas': list,
        }
    """
    from datetime import datetime, timedelta
    
    hoy = datetime.now().date()
    fechas = [(hoy + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(dias_adelante + 1)]
    
    partidos = []
    errores = []
    
    for fecha in fechas:
        result = _api_get('/matches', {'date': fecha})
        
        if not result['ok']:
            errores.append(f'{fecha}: {result["error"]}')
            continue
        
        for m in result['data'].get('matches', []):
            estado = m.get('status', '')
            
            # Solo partidos programados o en juego
            if estado not in ('SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED'):
                continue
            
            codigo_comp = m.get('competition', {}).get('code', '')
            
            # Filtrar por ligas si se especifica
            if ligas_codigos and codigo_comp not in ligas_codigos:
                continue
            
            utc_date = m.get('utcDate', '')
            
            partidos.append({
                'id': m.get('id'),
                'fecha': utc_date[:10],
                'hora': utc_date[11:16] if len(utc_date) > 11 else '',
                'local': m.get('homeTeam', {}).get('name', ''),
                'visitante': m.get('awayTeam', {}).get('name', ''),
                'estado': estado,
                'competicion': m.get('competition', {}).get('name', ''),
                'codigo_competicion': codigo_comp,
                'jornada': m.get('matchday'),
            })
    
    return {
        'partidos': partidos,
        'error': ' | '.join(errores) if errores else None,
        'fechas_consultadas': fechas,
    }
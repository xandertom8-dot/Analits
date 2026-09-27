# ============================================================
# backend/parser.py
# Parser estricto de estadísticas pegadas desde texto.
# - Valida estructura (15 columnas)
# - Diferencia 0 (real) de None (faltante)
# - Detecta fila "Total"
# - Guarda el texto original
# ============================================================

import re


# ============================================================
# CONSTANTES
# ============================================================
COLUMNAS_ESPERADAS = ['G', 'A', 'TR', 'TA', 'Crn', 'S', 'SOnT', 'BS', 'P', 'C', 'E', 'O', 'FC', 'FR', 'SAV']
NUM_COLUMNAS = len(COLUMNAS_ESPERADAS)


# ============================================================
# PARSER
# ============================================================
def parsear_estadisticas(texto):
    """
    Parser estricto con validación:
    - Encabezado debe tener exactamente las 15 columnas esperadas
    - Cada jugador debe tener exactamente 15 valores
    - Detecta valores no numéricos
    - Diferencia 0 (real) de None (faltante)
    - Detecta fila Total
    - Guarda el texto original

    Retorna:
        {
            'error': str or None,
            'valido': bool,
            'advertencias': [str],
            'jugadores': [{'nombre': str, 'stats': {col: int|None}, 'campos_faltantes': [str]}],
            'total': {col: int} or None,
            'columnas_detectadas': [str],
            'texto_original': str
        }
    """
    resultado = {
        'error': None,
        'valido': False,
        'advertencias': [],
        'jugadores': [],
        'total': None,
        'columnas_detectadas': [],
        'texto_original': texto
    }

    if not texto or not texto.strip():
        resultado['error'] = 'No se proporcionó texto'
        return resultado

    lineas = [l for l in texto.strip().split('\n') if l.strip()]

    if len(lineas) < 2:
        resultado['error'] = 'El texto debe tener al menos 2 líneas (encabezado + datos)'
        return resultado

    # ============ 1. VALIDAR ENCABEZADO ============
    encabezado_linea = lineas[0].strip()
    encabezado_partes = re.split(r'\t+|\s{2,}', encabezado_linea)
    encabezado_partes = [p.strip() for p in encabezado_partes if p.strip()]

    if len(encabezado_partes) != NUM_COLUMNAS:
        resultado['error'] = (
            f'❌ Error de estructura en el encabezado: '
            f'se esperaban {NUM_COLUMNAS} columnas, se detectaron {len(encabezado_partes)}. '
            f'Detectadas: {encabezado_partes}'
        )
        return resultado

    # Validar que sean exactamente las esperadas
    columnas_encontradas = []
    for i, col in enumerate(encabezado_partes):
        col_limpia = col.strip().upper()
        if i < len(COLUMNAS_ESPERADAS):
            esperada = COLUMNAS_ESPERADAS[i].upper()
            if col_limpia == esperada:
                columnas_encontradas.append(COLUMNAS_ESPERADAS[i])
            else:
                resultado['advertencias'].append(
                    f'⚠️ Columna {i+1}: se esperaba "{COLUMNAS_ESPERADAS[i]}", se encontró "{col}"'
                )
                columnas_encontradas.append(col)

    resultado['columnas_detectadas'] = columnas_encontradas

    # ============ 2. PROCESAR JUGADORES ============
    for idx, linea in enumerate(lineas[1:], start=2):
        linea = linea.strip()
        if not linea:
            continue

        partes = re.split(r'\t+|\s{2,}', linea)
        partes = [p.strip() for p in partes if p.strip()]

        if len(partes) < 2:
            # ========== NUEVO: ignorar silenciosamente separadores decorativos ==========
            # Si la línea entera es solo símbolos decorativos (=, -, *, _, ., etc.),
            # se ignora sin advertir porque es un separador visual.
            linea_sin_espacios = linea.replace(' ', '').replace('\t', '')
            if linea_sin_espacios and not any(ch.isalnum() for ch in linea_sin_espacios):
                # Solo símbolos, no advertir
                continue
            
            # Si la línea es muy corta y no tiene números, probablemente es basura
            # (pero avisamos por si acaso)
            resultado['advertencias'].append(
                f'⚠️ Línea {idx}: se ignoró. Partes={len(partes)}. Contenido: "{linea[:80]}"'
            )
            continue

        nombre = partes[0].strip()
        valores_raw = partes[1:]

        # ¿Es la fila Total?
        es_total = nombre.lower() in ['total', 'totales', 'total equipo']

        # ===== Validar cantidad de valores =====
        if len(valores_raw) != NUM_COLUMNAS:
            if es_total:
                # La fila Total se ignora silenciosamente si tiene menos valores
                # (no es crítica, es solo informativa)
                if len(valores_raw) < NUM_COLUMNAS - 5:
                    # Muy pocos valores: probablemente es basura, avisar
                    resultado['advertencias'].append(
                        f'⚠️ Fila "Total": formato incorrecto ({len(valores_raw)} valores)'
                    )
                # Si está cerca del formato esperado, no avisar
            else:
                resultado['advertencias'].append(
                    f'⚠️ Jugador "{nombre}": se esperaban {NUM_COLUMNAS} valores, se detectaron {len(valores_raw)}'
                )

        # ===== Procesar cada valor =====
        stats = {}
        campos_faltantes = []

        for i, col in enumerate(COLUMNAS_ESPERADAS):
            if i < len(valores_raw):
                valor_str = valores_raw[i].strip()

                try:
                    if '.' in valor_str:
                        valor = int(float(valor_str))
                    else:
                        valor = int(valor_str)
                    stats[col] = valor
                except (ValueError, TypeError):
                    stats[col] = None
                    campos_faltantes.append(col)
                    if not es_total:
                        resultado['advertencias'].append(
                            f'⚠️ Jugador "{nombre}": valor no numérico en columna "{col}": "{valor_str}"'
                        )
            else:
                stats[col] = None
                campos_faltantes.append(col)

        if es_total:
            resultado['total'] = stats
        else:
            jugador = {
                'nombre': nombre,
                'stats': stats,
                'campos_faltantes': campos_faltantes
            }
            resultado['jugadores'].append(jugador)

    # ============ 3. VALIDAR RESULTADO ============
    if len(resultado['jugadores']) == 0:
        resultado['error'] = '❌ No se detectaron jugadores válidos'
        return resultado

    resultado['valido'] = True
    return resultado


def validar_estructura(texto):
    """
    Valida si el texto tiene estructura válida SIN guardar nada.
    Útil para preview.
    """
    return parsear_estadisticas(texto)


# ============================================================
# CALCULAR ESTADÍSTICAS AGREGADAS
# ============================================================
def calcular_estadisticas_equipo(jugadores):
    """
    Calcula estadísticas agregadas de un equipo IGNORANDO NULL.

    - Para cada estadística, cuenta solo los jugadores que tienen el dato.
    - Devuelve el TOTAL y también la cantidad de observaciones válidas.
    - Diferencia claramente 0 (observado) de None (faltante).
    """
    if not jugadores:
        return {
            'goles': 0, 'asistencias': 0, 'tiros': 0, 'tiros_puerta': 0,
            'corners': 0, 'faltas': 0, 'paradas': 0,
            'tarjetas_amarillas': 0, 'tarjetas_rojas': 0,
            'pases': 0, 'centros': 0, 'entradas': 0,
            'fueras_juego': 0, 'faltas_recibidas': 0,
            'tiros_bloqueados': 0,
            'observaciones': {},
        }

    mapeo = {
        'goles': 'G',
        'asistencias': 'A',
        'tiros': 'S',
        'tiros_puerta': 'SOnT',
        'tiros_bloqueados': 'BS',
        'corners': 'Crn',
        'faltas': 'FC',
        'faltas_recibidas': 'FR',
        'paradas': 'SAV',
        'tarjetas_amarillas': 'TA',
        'tarjetas_rojas': 'TR',
        'pases': 'P',
        'centros': 'C',
        'entradas': 'E',
        'fueras_juego': 'O',
    }

    resultado = {}
    observaciones = {}

    for campo_salida, campo_bd in mapeo.items():
        valores_validos = [
            j['stats'].get(campo_bd)
            for j in jugadores
            if j['stats'].get(campo_bd) is not None
        ]

        if valores_validos:
            resultado[campo_salida] = sum(valores_validos)
        else:
            resultado[campo_salida] = None  # ← Sin datos ≠ 0

        observaciones[campo_salida] = {
            'validos': len(valores_validos),
            'total_jugadores': len(jugadores),
        }

    resultado['observaciones'] = observaciones
    return resultado

# ============================================================
# FASE I — INGESTA UNIFICADA
# ============================================================

import re


# ============================================================
# PARSER DE TIMELINE
# ============================================================
def parsear_timeline(texto_timeline):
    """
    Parsea el bloque TIMELINE del texto unificado.
    
    Formato esperado:
        --- LOCAL ---
        8' | Gol | João Cancelo (asist: Lamine Yamal)
        25' | Gol de penalti | Raphinha
        36' | Gol en propia puerta | Asier Villalibre
        45+5' | Tarjeta amarilla | Lamine Yamal
        46' | Sustitución | Sale: Joan García → Entra: W. Szczęsny
        
        --- VISITANTE ---
        22' | Tarjeta amarilla | Pedro Felipe
        ...
    
    Args:
        texto_timeline: string con el bloque completo (sin el header "===== TIMELINE =====")
    
    Returns:
        {
            'local': [{'minuto', 'minuto_str', 'tipo', 'jugador', 'asistencia'?, 'sale'?, 'entra'?, 'raw'}],
            'visitante': [...],
            'errores': [str],
            'resumen': {
                'goles_local': int,
                'goles_visitante': int,
                'og_local': int,       # OG que metió el local (suman al visitante)
                'og_visitante': int,   # OG que metió el visitante (suman al local)
                'penaltis_fallados': {'local': int, 'visitante': int},
                'tarjetas_local': int,
                'tarjetas_visitante': int,
                'sustituciones_local': int,
                'sustituciones_visitante': int,
            }
        }
    """
    resultado = {
        'local': [],
        'visitante': [],
        'errores': [],
        'resumen': {
            'goles_local': 0,
            'goles_visitante': 0,
            'og_local': 0,
            'og_visitante': 0,
            'penaltis_fallados': {'local': 0, 'visitante': 0},
            'tarjetas_local': 0,
            'tarjetas_visitante': 0,
            'sustituciones_local': 0,
            'sustituciones_visitante': 0,
        }
    }
    
    if not texto_timeline or not texto_timeline.strip():
        return resultado
    
    # ========== Dividir por LOCAL / VISITANTE ==========
    bloque_local = ''
    bloque_visitante = ''
    
    # Detectar secciones
    match_local = re.search(
        r'---\s*LOCAL\s*---(.*?)(?=---\s*VISITANTE\s*---|$)',
        texto_timeline,
        re.DOTALL | re.IGNORECASE
    )
    match_visitante = re.search(
        r'---\s*VISITANTE\s*---(.*?)$',
        texto_timeline,
        re.DOTALL | re.IGNORECASE
    )
    
    if match_local:
        bloque_local = match_local.group(1)
    if match_visitante:
        bloque_visitante = match_visitante.group(1)
    
    if not match_local and not match_visitante:
        resultado['errores'].append('No se encontraron secciones LOCAL/VISITANTE en el timeline')
        return resultado
    
    # ========== Parsear cada bloque ==========
    resultado['local'] = _parsear_lineas_timeline(bloque_local, 'local', resultado)
    resultado['visitante'] = _parsear_lineas_timeline(bloque_visitante, 'visitante', resultado)
    
    return resultado


def _parsear_lineas_timeline(bloque, lado, resultado):
    """
    Parsea las líneas de un bloque LOCAL o VISITANTE.
    
    Args:
        bloque: texto con las líneas
        lado: 'local' o 'visitante'
        resultado: dict con la estructura completa (para acumular resumen)
    
    Returns:
        Lista de eventos parseados.
    """
    eventos = []
    
    for linea in bloque.strip().split('\n'):
        linea = linea.strip()
        if not linea:
            continue
        
        # Formato: "8' | Gol | João Cancelo (asist: Lamine Yamal)"
        partes = [p.strip() for p in linea.split('|')]
        
        if len(partes) < 3:
            continue
        
        minuto_str = partes[0]
        tipo_str = partes[1].strip()
        detalle = ' | '.join(partes[2:]).strip()  # por si el detalle lleva "|" dentro
        
        # ========== Extraer minuto numérico ==========
        minuto_num = _extraer_minuto(minuto_str)
        
        # ========== Identificar tipo de evento ==========
        tipo = _identificar_tipo_evento(tipo_str)
        
        # ========== Parsear detalle según tipo ==========
        evento = {
            'minuto': minuto_num,
            'minuto_str': minuto_str,
            'tipo': tipo,
            'raw': linea,
        }
        
        if tipo == 'gol':
            # "João Cancelo (asist: Lamine Yamal)"
            jugador, asistencia = _parsear_jugador_asistencia(detalle)
            evento['jugador'] = jugador
            evento['asistencia'] = asistencia
            
            if lado == 'local':
                resultado['resumen']['goles_local'] += 1
            else:
                resultado['resumen']['goles_visitante'] += 1
        
        elif tipo == 'gol_penalti':
            # "Raphinha"
            evento['jugador'] = detalle.strip()
            
            if lado == 'local':
                resultado['resumen']['goles_local'] += 1
            else:
                resultado['resumen']['goles_visitante'] += 1
        
        elif tipo == 'og_rival':
            # "Asier Villalibre" — jugador del RIVAL
            evento['jugador'] = detalle.strip()
            evento['es_og'] = True
            
            # El gol suma al EQUIPO DEL TIMELINE (el beneficiado)
            if lado == 'local':
                resultado['resumen']['goles_local'] += 1
                # El jugador que metió el OG es del visitante
                resultado['resumen']['og_visitante'] += 1
            else:
                resultado['resumen']['goles_visitante'] += 1
                # El jugador que metió el OG es del local
                resultado['resumen']['og_local'] += 1
        
        elif tipo == 'penalti_fallado':
            evento['jugador'] = detalle.strip()
            
            if lado == 'local':
                resultado['resumen']['penaltis_fallados']['local'] += 1
            else:
                resultado['resumen']['penaltis_fallados']['visitante'] += 1
        
        elif tipo == 'tarjeta':
            evento['jugador'] = detalle.strip()
            
            if lado == 'local':
                resultado['resumen']['tarjetas_local'] += 1
            else:
                resultado['resumen']['tarjetas_visitante'] += 1
        
        elif tipo == 'sustitucion':
            # "Sale: Joan García → Entra: W. Szczęsny"
            sale, entra = _parsear_sustitucion(detalle)
            evento['sale'] = sale
            evento['entra'] = entra
            
            if lado == 'local':
                resultado['resumen']['sustituciones_local'] += 1
            else:
                resultado['resumen']['sustituciones_visitante'] += 1
        
        eventos.append(evento)
    
    return eventos


def _extraer_minuto(minuto_str):
    """
    Convierte "45+5'" → 45, "8'" → 8, "90+2'" → 90.
    """
    try:
        # Buscar el primer número
        m = re.match(r'(\d+)', minuto_str.strip())
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 0


def _identificar_tipo_evento(tipo_str):
    """
    Mapea el tipo textual a un tipo interno estandarizado.
    """
    tipo_lower = tipo_str.lower().strip()
    
    if 'propia puerta' in tipo_lower or 'autogol' in tipo_lower:
        return 'og_rival'
    if 'penalti fallado' in tipo_lower or 'penal fallado' in tipo_lower:
        return 'penalti_fallado'
    if 'penalti' in tipo_lower or 'penal' in tipo_lower:
        return 'gol_penalti'
    if tipo_lower == 'gol':
        return 'gol'
    if 'sustituci' in tipo_lower or 'cambio' in tipo_lower:
        return 'sustitucion'
    if 'tarjeta' in tipo_lower or 'amarilla' in tipo_lower or 'roja' in tipo_lower:
        return 'tarjeta'
    # Desconocido
    return 'otro'


def _parsear_jugador_asistencia(detalle):
    """
    Parsea "João Cancelo (asist: Lamine Yamal)" → ("João Cancelo", "Lamine Yamal")
    Si no hay asistencia, devuelve ("João Cancelo", None).
    """
    match = re.match(r'^(.+?)\s*\(asist:\s*(.+?)\)\s*$', detalle.strip(), re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return detalle.strip(), None


def _parsear_sustitucion(detalle):
    """
    Parsea "Sale: Joan García → Entra: W. Szczęsny" → ("Joan García", "W. Szczęsny")
    Soporta → (flecha unicode), -> (ascii), => (ascii).
    """
    # Normalizar flechas
    detalle_norm = detalle.replace('→', '->').replace('=>', '->')
    
    match = re.match(
        r'^Sale:\s*(.+?)\s*->\s*Entra:\s*(.+?)\s*$',
        detalle_norm.strip(),
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    return None, None

def parsear_texto_unificado(texto):
    """
    Parsea un texto unificado que contiene:
    - Bloque "===== ESTADÍSTICAS DE JUGADORES =====" con EQUIPO 1 y EQUIPO 2
    - Bloque "===== TIMELINE =====" con LOCAL y VISITANTE
    
    Args:
        texto: string completo pegado por el usuario
    
    Returns:
        {
            'modo': 'unificado' | 'antiguo' | 'mixto',
            'equipo_local': {  # parseo de las stats del EQUIPO 1
                'error': None,
                'valido': bool,
                'advertencias': [],
                'jugadores': [...],
                'total': {...},
                'columnas_detectadas': [...],
                'texto_original': str,
            },
            'equipo_visitante': {  # parseo de las stats del EQUIPO 2
                ...
            },
            'timeline': {
                'local': [...],
                'visitante': [...],
                'errores': [...],
                'resumen': {...},
            },
            'resumen_unificado': {
                'goles_local_stats': int,
                'goles_visitante_stats': int,
                'goles_local_timeline': int,
                'goles_visitante_timeline': int,
                'og_local': int,
                'og_visitante': int,
                'discrepancia': bool,
                'mensaje': str,
            }
        }
    """
    resultado = {
        'modo': 'antiguo',
        'equipo_local': None,
        'equipo_visitante': None,
        'timeline': None,
        'resumen_unificado': {
            'goles_local_stats': 0,
            'goles_visitante_stats': 0,
            'goles_local_timeline': 0,
            'goles_visitante_timeline': 0,
            'og_local': 0,
            'og_visitante': 0,
            'discrepancia': False,
            'mensaje': '',
        }
    }
    
    if not texto or not texto.strip():
        return resultado
    
    # ========== 1. Detectar si es unificado ==========
    es_unificado = bool(re.search(
        r'=====\s*ESTAD[IÍ]STICAS DE JUGADORES\s*=====',
        texto,
        re.IGNORECASE
    ))
    
    if not es_unificado:
        # Modo antiguo (solo stats de un equipo)
        resultado['modo'] = 'antiguo'
        return resultado
    
    resultado['modo'] = 'unificado'
    
    # ========== 2. Separar bloques ==========
    # Bloque stats
    match_stats = re.search(
        r'=====\s*ESTAD[IÍ]STICAS DE JUGADORES\s*=====(.*?)(?=====\s*TIMELINE\s*=====|$)',
        texto,
        re.DOTALL | re.IGNORECASE
    )
    bloque_stats = match_stats.group(1) if match_stats else ''
    
    # Bloque timeline
    match_timeline = re.search(
        r'=====\s*TIMELINE\s*=====(.*?)$',
        texto,
        re.DOTALL | re.IGNORECASE
    )
    bloque_timeline = match_timeline.group(1) if match_timeline else ''
    
    # ========== 3. Separar EQUIPO 1 y EQUIPO 2 ==========
    match_eq1 = re.search(
        r'---\s*EQUIPO\s*1\s*---(.*?)(?=---\s*EQUIPO\s*2\s*---|$)',
        bloque_stats,
        re.DOTALL | re.IGNORECASE
    )
    match_eq2 = re.search(
        r'---\s*EQUIPO\s*2\s*---(.*?)$',
        bloque_stats,
        re.DOTALL | re.IGNORECASE
    )
    
    texto_eq1 = match_eq1.group(1).strip() if match_eq1 else ''
    texto_eq2 = match_eq2.group(1).strip() if match_eq2 else ''
    
    # ========== 4. Parsear cada equipo con el parser existente ==========
    if texto_eq1:
        resultado['equipo_local'] = parsear_estadisticas(texto_eq1)
    else:
        resultado['equipo_local'] = {
            'error': 'No se detectó el EQUIPO 1',
            'valido': False,
            'advertencias': [],
            'jugadores': [],
            'total': None,
            'columnas_detectadas': [],
            'texto_original': '',
        }
    
    if texto_eq2:
        resultado['equipo_visitante'] = parsear_estadisticas(texto_eq2)
    else:
        resultado['equipo_visitante'] = {
            'error': 'No se detectó el EQUIPO 2',
            'valido': False,
            'advertencias': [],
            'jugadores': [],
            'total': None,
            'columnas_detectadas': [],
            'texto_original': '',
        }
    
    # ========== 5. Parsear timeline ==========
    if bloque_timeline:
        resultado['timeline'] = parsear_timeline(bloque_timeline)
    else:
        resultado['timeline'] = {
            'local': [],
            'visitante': [],
            'errores': ['No se encontró bloque TIMELINE'],
            'resumen': {
                'goles_local': 0,
                'goles_visitante': 0,
                'og_local': 0,
                'og_visitante': 0,
                'penaltis_fallados': {'local': 0, 'visitante': 0},
                'tarjetas_local': 0,
                'tarjetas_visitante': 0,
                'sustituciones_local': 0,
                'sustituciones_visitante': 0,
            }
        }
    
    # ========== 6. Calcular resumen y detectar discrepancias ==========
    goles_local_stats = _sumar_goles_jugadores(resultado['equipo_local'])
    goles_visitante_stats = _sumar_goles_jugadores(resultado['equipo_visitante'])
    
    goles_local_timeline = resultado['timeline']['resumen']['goles_local']
    goles_visitante_timeline = resultado['timeline']['resumen']['goles_visitante']
    
    og_local = resultado['timeline']['resumen']['og_local']
    og_visitante = resultado['timeline']['resumen']['og_visitante']
    
    # Goles reales según timeline (con OG aplicados según filosofía C)
    goles_local_reales = goles_local_stats + og_visitante
    goles_visitante_reales = goles_visitante_stats + og_local
    
    discrepancia = False
    mensaje = ''
    
    # Comparar goles stats vs timeline
    if goles_local_timeline != goles_local_stats + og_visitante:
        discrepancia = True
        mensaje = (f'⚠️ Goles del LOCAL: stats={goles_local_stats}, timeline={goles_local_timeline}, '
                   f'OG_visitante={og_visitante}. Revisa el timeline.')
    
    if goles_visitante_timeline != goles_visitante_stats + og_local:
        discrepancia = True
        msg = (f'⚠️ Goles del VISITANTE: stats={goles_visitante_stats}, timeline={goles_visitante_timeline}, '
               f'OG_local={og_local}. Revisa el timeline.')
        mensaje = f'{mensaje} {msg}'.strip() if mensaje else msg
    
    resultado['resumen_unificado'] = {
        'goles_local_stats': goles_local_stats,
        'goles_visitante_stats': goles_visitante_stats,
        'goles_local_timeline': goles_local_timeline,
        'goles_visitante_timeline': goles_visitante_timeline,
        'goles_local_reales': goles_local_reales,
        'goles_visitante_reales': goles_visitante_reales,
        'og_local': og_local,
        'og_visitante': og_visitante,
        'discrepancia': discrepancia,
        'mensaje': mensaje.strip(),
    }
    
    return resultado


def _sumar_goles_jugadores(equipo_parseado):
    """Suma los goles de todos los jugadores de un equipo parseado."""
    if not equipo_parseado or not equipo_parseado.get('jugadores'):
        return 0
    total = 0
    for j in equipo_parseado['jugadores']:
        g = j['stats'].get('G')
        if g is not None:
            total += g
    return total
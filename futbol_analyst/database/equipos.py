# ============================================================
# BASE DE DATOS DE EQUIPOS Y LIGAS - ÚNICA FUENTE DE VERDAD
# ============================================================
# Este archivo es la ÚNICA fuente de verdad para ligas y equipos.
# NO duplicar esta información en index.html ni en ningún otro sitio.
# ============================================================

# Estructura jerárquica completa:
# Continente > País > Competición > Temporada > Equipos

ESTRUCTURA = {
    # ========== EUROPA ==========
    "Europa": {
        "España": {
            "LaLiga": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Deportivo Alavés","Athletic Club","Atlético de Madrid","FC Barcelona","Celta de Vigo","Deportivo de La Coruña","Elche","Espanyol","Getafe","Levante","Málaga","Osasuna","Racing de Santander","Rayo Vallecano","Real Betis","Real Madrid","Real Sociedad","Sevilla","Valencia","Villarreal"
                    ]
                }
            },
            "LaLiga2": {
                "tipo": "liga",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "Castellón","Eibar","Burgos","CD Sabadell","Leganés","Girona","RC Celta Fortuna","Mallorca","Tenerife","Granada","Las Palmas","Sporting Gijón","Almería","Real Sociedad II","Real Oviedo","Real Valladolid","FC Andorra","Cádiz","Córdoba","Eldense","Albacete","Ceuta"


                    ]
                }
            }
        },
        "Inglaterra": {
            "Premier League": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Manchester City","Arsenal","Hull City","Chelsea","Brentford","Liverpool","Newcastle United","Everton","Leeds United","Brighton & Hove Albion","Manchester United","Sunderland","Crystal Palace","Ipswich Town","AFC Bournemouth","Nottingham Forest","Aston Villa","Tottenham Hotspur","Fulham","Coventry City"
                    ]
                }
            },
            "Championship": {
                "tipo": "liga",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "West Ham United","West Bromwich Albion","Swansea City","Queens Park Rangers","Charlton Athletic","Middlesbrough","Bristol City","Millwall","Norwich City","Sheffield United","Wolverhampton Wanderers","Watford","Southampton","Birmingham City","Stoke City","Wrexham","Portsmouth","Blackburn Rovers","Lincoln City","Cardiff City","Bolton Wanderers","Derby County","Burnley","Preston North End"


                    ]
                }
            }
        },
        "Italia": {
            "Serie A": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "AS Roma","Internazionale","Lazio","Como","AC Milan","Juventus","Frosinone","Atalanta","Cagliari","Sassuolo","Udinese","Napoli","Torino","Lecce","Fiorentina","Bolonia","Parma","Monza","Génova","Venezia"
                    ]
                }
            },
            "Serie B": {
                "tipo": "liga",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "Palermo","Mantova","Sudtirol","Ascoli","Modena","US Avellino","Pisa","Empoli","Arezzo","Cesena","Padova","Vicenza","Hellas Verona","Virtus Entella","Benevento","Cremonese","Carrarese","Sampdoria","Juve Stabia","Catanzaro"


                    ]
                }
            }
        },
        "Alemania": {
            "Bundesliga": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "F. C. Augsburgo","SC Freiburg","Borussia Dortmund","SV Elversberg","Mainz","Bayern Munich","Schalke 04","Bayer Leverkusen","RB Leipzig","VfB Stuttgart","Werder Bremen","FC Cologne","SC Paderborn 07","Eintracht Frankfurt","FC Union Berlin","TSG Hoffenheim","Borussia Monchengladbach","Hamburg SV"


                    ]
                }
            },
            "Bundesliga 2": {
                "tipo": "liga",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "FC Nürnberg","Hertha Berlin","1. FC Heidenheim 1846","VfL Wolfsburg","Kaiserslautern","VfL Bochum","FC Magdeburg","VfL Osnabruck","Karlsruher SC","Energie Cottbus","Arminia Bielefeld","SpVgg Greuther Fürth","Hannover 96","SV Darmstadt 98","TSV Eintracht Braunschweig","St Pauli","Holstein Kiel","Dynamo Dresden"


                    ]
                }
            }
        },
        "Francia": {
            "Ligue 1": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Stade Rennais","AS Mónaco","Paris FC","Lyon","Lille","Strasbourg","Brest","Lorient","Troyes","Lens","Marseille","Angers","Paris Saint-Germain","Le Mans","Nice","Le Havre AC","Toulouse","AJ Auxerre"


                    ]
                }
            },
            "Ligue 2": {
                "tipo": "liga",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "Ajaccio", "Amiens", "Annecy", "Bastia", "Caen", "Clermont", "Dunkerque",
                        "Grenoble", "Guingamp", "Laval", "Lorient", "Martigues", "Metz",
                        "Paris FC", "Pau", "Red Star", "Rodez", "Troyes"
                    ]
                }
            }
        },
        "Países Bajos": {
            "Eredivisie": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "AZ Alkmaar","PSV Eindhoven","Feyenoord Rotterdam","Excelsior","FC Twente","Fortuna Sittard","Go Ahead Eagles","Ajax Amsterdam","NEC Nijmegen","FC Groningen","Sparta Rotterdam","Heerenveen","PEC Zwolle","Telstar","FC Utrecht","Willem II","ADO Den Haag","SC Cambuur"


                    ]
                }
            }
        },
        "Portugal": {
            "Primeira Liga": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "FC Porto","Benfica","Sporting CP","Santa Clara","Arouca","Estrela","Gil Vicente","Braga","Maritimo","Académico de Viseu","Vitória de Guimaraes","C.D. Nacional","Moreirense","FC Famalicao","Rio Ave","Alverca","Estoril","Casa Pia"


                    ]
                }
            }
        },
        "Bélgica": {
            "Pro League": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "KAA Gent","Union St.-Gilloise","Club Brujas","Royal Charleroi SC","Zulte-Waregem","Standard Liege","Anderlecht","Sint-Truidense","Racing Genk","Lommel SK","Antwerp","Waasland-Beveren","KVC Westerlo","Cercle Brugge KSV","KV Mechelen","RAAL La Louvière","Oud-Heverlee Leuven","KV Kortrijk"


                    ]
                }
            }
        },
        "Turquía": {
            "Süper Lig": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Besiktas","Galatasaray","Kocaelispor","Trabzonspor","Amed SFK","Gaziantep FK","Alanyaspor","Genclerbirligi","Fenerbahçe","Kasimpasa","Caykur Rizespor","Istanbul Basaksehir","Samsunspor","Çorum FK","Erzurum BB","Eyupspor","Goztepe","Konyaspor"


                    ]
                }
            }
        },
        "Escocia": {
            "Scottish Premiership": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Celtic","Rangers","Heart of Midlothian","St Mirren","Motherwell","Dundee","St Johnstone","Hibernian","Dundee United","Aberdeen","Falkirk","Kilmarnock"


                    ]
                }
            }
        },
        "Ucrania": {
            "Ukrainian Premier League": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Bukovyna","Cherkasy","Chernomorets O.","Dinamo Kiev","Epitsentr","Karpaty Lvov","Kolos Kovalivka","Kryvbas KR","Kudrivka","Livyi Bereh","Metalist 1925 Kharkiv","Obolon Kyiv","Polessya Zhitomir","Shakhtar","Veres Livne","Zorya"


                    ]
                }
            }
        },
        "Grecia": {
            "Super League": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Panathinaikos","Panetolikos","AEK Athens","Olympiacos","PAOK","OFI Crete","Aris","Iraklis","Volos NFC","Atromitos","Kalamata","Kifisia","Asteras Tripoli","Levadiakos"


                    ]
                }
            }
        },
        "Suiza": {
            "Super League": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Basel","FC Lugano","FC Vaduz","Grasshopper","Lausanne Sports","Luzern","Servette","Sion","St. Gallen","Thun","Young Boys","Zurich"


                    ]
                }
            }
        },
        "Austria": {
            "Bundesliga de Austria": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "LASK Linz","RB Salzburg","Rapid Vienna","SK Sturm Graz","WSG Swarovski Tirol","TSV Hartberg","Austria Lustenau","SV Josko Ried","Wolfsberger","Grazer AK","SC Rheindorf Altach","Austria Vienna"


                    ]
                }
            }
        },
        "Dinamarca": {
            "Superliga": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "F.C. København","FC Midtjylland","FC Nordsjælland","Viborg FF","Brøndby IF","Randers FC","AC Horsens","Lyngby Boldklub","Silkeborg IF","Odense Boldklub","Aarhus GF","Sonderjyske"


                    ]
                }
            }
        },
        "Noruega": {
            "Eliteserien": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Bodo/Glimt","Viking FK","Tromso","Molde","Lillestrom","Rosenborg","SK Brann","Fredrikstad","Sarpsborg FK","Hamarkameratene","Vålerenga","Sandefjord","Kristiansund BK","KFUM Oslo","Aalesund","IK Start"


                    ]
                }
            }
        },
        "Suecia": {
            "Allsvenskan": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "IK Sirius","Djurgården","Hammarby IF","BK Häcken","AIK","IF Elfsborg","Malmö FF","Västerås SK","GAIS","IF Brommapojkarna","IFK Göteborg","Mjällby AIF","Kalmar FF","Degerfors IF","Örgryte IS","Halmstads BK"


                    ]
                }
            }
        }
    },
    
    # ========== AMÉRICA ==========
    "América": {
        "México": {
            "Liga MX": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "Apertura 2026.2027": [
                        "América","Guadalajara","Toluca","Tijuana","Atlas","Cruz Azul","Pumas UNAM","Querétaro","Puebla","León","Monterrey","Pachuca","Necaxa","Atlante","Tigres UANL","Atlético de San Luis","Santos","FC Juarez"


                    ]
                }
            }
        },
        "Estados Unidos": {
            "MLS": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Nashville SC","Inter Miami CF","New England Revolution","Chicago Fire FC","Charlotte FC","Orlando City SC","FC Cincinnati","Philadelphia Union","New York City FC","Toronto FC","D.C. United","Red Bull New York","Columbus Crew","Atlanta United FC","CF Montréal","Vancouver Whitecaps","Houston Dynamo FC","LAFC","FC Dallas","San Jose Earthquakes","St. Louis CITY SC","Colorado Rapids","Portland Timbers","San Diego FC","Real Salt Lake","Minnesota United FC","LA Galaxy","Seattle Sounders FC","Austin FC","Sporting Kansas City"


                    ]
                }
            }
        },
        "Colombia": {
            "Liga BetPlay I": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "América de Cali","Deportes Tolima","Independiente Medellín","Millonarios","Atlético Nacional","Llaneros FC","Independiente Santa Fe","Águilas Doradas","Atlético Bucaramanga","Once Caldas","Deportivo Cali","Cúcuta Deportivo","Internacional de Bogotá","Fortaleza CEIF","Deportivo Pereira","Jaguares de Córdoba","Boyacá Chicó FC","Atlético Junior","Deportivo Pasto","Alianza FC"


                    ]
                }
            },
            "Liga BetPlay II": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Alianza FC", "América de Cali", "Atlético Bucaramanga",
                        "Atlético Nacional", "Boyacá Chicó", "Cúcuta Deportivo",
                        "Deportes Tolima", "Deportivo Cali", "Deportivo Pasto",
                        "Deportivo Pereira", "Fortaleza", "Independiente Medellín",
                        "Internacional de Bogotá", "Jaguares", "Junior", "Llaneros",
                        "Millonarios", "Once Caldas", "Santa Fe", "Águilas Doradas"
                    ]
                }
            }
        },
        "Argentina": {
            "Liga Profesional": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Vélez Sarsfield","Gimnasia (Mendoza)","Instituto (Córdoba)","Defensa y Justicia","Unión (Santa Fe)","Newell's Old Boys","Independiente","Boca Juniors","Lanús","San Lorenzo","Deportivo Riestra","Platense","Estudiantes de La Plata","Central Córdoba (Santiago del Estero)","Talleres (Córdoba)","Argentinos Juniors","Sarmiento (Junín)","Gimnasia La Plata","Atlético Tucumán","Belgrano (Córdoba)","Tigre","Rosario Central","Independiente Rivadavia","Barracas Central","River Plate","Huracán","Banfield","Estudiantes de Río Cuarto","Aldosivi","Racing Club"


                    ]
                }
            }
        },
        "Brasil": {
            "Brasileirão": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Flamengo","Palmeiras","Athletico Paranaense","Fluminense","Bahia","Cruzeiro","Coritiba","Atlético-MG","Red Bull Bragantino","São Paulo","Vitória","Corinthians","Santos","Botafogo","Grêmio","Mirassol","Vasco da Gama","Internacional","Remo","Chapecoense"


                    ]
                }
            }
        },
        "Uruguay": {
            "Primera División": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Liverpool","Montevideo City Torque","Cerro","Juventud","Deportivo Maldonado","Racing (Montevideo)","Boston River","Peñarol","Nacional","Montevideo Wanderers","Progreso","Cerro Largo","Central Español Fútbol Club","Danubio","Defensor Sporting","Albion FC"


                    ]
                }
            }
        },
        "Chile": {
            "Primera División": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Colo Colo","Universidad Católica","Universidad de Chile","Palestino","Everton CD","Deportes Limache","Ñublense","Deportes Concepcion","La Serena","Coquimbo Unido","O'Higgins","Audax Italiano","Huachipato","Universidad de Concepción","Cobresal","Unión La Calera"


                    ]
                }
            }
        },
        "Ecuador": {
            "Serie A": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Independiente del Valle","Aucas","Universidad Católica (Quito)","Macará","Liga de Quito","Barcelona SC","Libertad (Ecuador)","Leones","Emelec","Mushuc Runa","Guayaquil City FC","Deportivo Cuenca","Orense","Técnico Universitario","Delfín","Manta F.C."


                    ]
                }
            }
        },
        "Paraguay": {
            "Primera División": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Libertad","2 de Mayo","Club Olimpia","Sportivo Ameliano","Nacional Asunción","Sportivo Trinidense","Cerro Porteño","Guaraní","Sportivo Luqueño","Rubio Ñú","Deportivo Recoleta","Sportivo San Lorenzo"


                    ]
                }
            }
        },
        "Perú": {
            "Liga 1": {
                "tipo": "liga",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Deportivo Garcilaso","Universitario","Alianza Atlético","Cusco FC","Juan Pablo II","Melgar","Sport Boys","Sporting Cristal","Alianza Lima","Sport Huancayo","Atlético Grau","Comerciantes Unidos","Cienciano del Cusco","Deportivo Moquegua","FC Cajamarca","Los Chankas","ADT","UTC"


                    ]
                }
            }
        }
    },
    
    # ========== INTERNACIONAL ==========
    "Internacional": {
        "UEFA": {
            "UEFA Champions League": {
                "tipo": "copa_internacional",
                "nivel": 1,
                "temporadas": {
                    "2026-2027": [
                        "Paris Saint-Germain","Bayern Munich","Barcelona","Manchester United","Como","Sporting CP","VfB Stuttgart","Manchester City","Aston Villa","Lens","Real Betis","Borussia Dortmund","Liverpool","Real Madrid","Arsenal","AEK Athens","AS Roma","Shakhtar Donetsk","Fenerbahçe","PSV Eindhoven","Villarreal","Club Brujas","Lille","Slavia Prague","Atlético de Madrid","Internazionale","LASK Linz","Napoli","Galatasaray","Viking FK","FC Porto","RB Leipzig","Feyenoord Rotterdam","Sabah FK","Slovan Bratislava","Bodo/Glimt"


                    ]
                }
            },
            "UEFA Europa League": {
                "tipo": "copa_internacional",
                "nivel": 2,
                "temporadas": {
                    "2026-2027": [
                        "AC Milan","AZ Alkmaar","Anderlecht","Ararat-Armenia","Bayer Leverkusen","Benfica","Besiktas","AFC Bournemouth","NK Celje","Celta Vigo","Celtic","Crystal Palace","Dinamo Zagreb","Ferencvaros","Hapoel Be'er","TSG Hoffenheim","Jagiellonia Bialystok","Juventus","Lech Poznan","Levski Sofia","Lillestrom","Lyon","Marseille","NEC Nijmegen","OFI Crete","Olympiacos","Omonia Nicosia","Real Sociedad","Stade Rennais","RB Salzburg","Sparta Prague","SK Sturm Graz","Sunderland","Torreense","Union St.-Gilloise","Viktoria Plzen"


                    ]
                }
            },
            "UEFA Conference League": {
                "tipo": "copa_internacional",
                "nivel": 3,
                "temporadas": {
                    "2026-2027": [
                        "Aarhus GF","Ajax Amsterdam","Atalanta","Borac Banja Luka","SK Brann","Brighton & Hove Albion","CSKA Sofia","Egnatia","F.C. København","SC Freiburg","KAA Gent","Getafe","Hajduk Split","Heart of Midlothian","Iberia 1999","Inter D'Escaldes","Jablonec","Kairat Almaty","Kauno Zalgiris","KuPS Kuopio","Lincoln Red Imps","FC Lugano","FC Midtjylland","Mjällby AIF","AS Mónaco","FC Nordsjælland","Pafos","Panathinaikos","Red Star Belgrade","Riga FC","Sint-Truidense","Braga","FC Thun","Trabzonspor","FC Twente","CSU Craiova"


                    ]
                }
            }
        },
        "CONMEBOL": {
            "Copa Libertadores": {
                "tipo": "copa_internacional",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Flamengo","Estudiantes de La Plata","Independiente Medellín","Cusco FC","Coquimbo Unido","Deportes Tolima","Nacional","Universitario","Independiente Rivadavia","Fluminense","Bolívar","Deportivo La Guaira","Universidad Católica","Cruzeiro","Boca Juniors","Barcelona SC","Corinthians","Platense","Independiente Santa Fe","Peñarol","Cerro Porteño","Palmeiras","Sporting Cristal","Atlético Junior","Liga de Quito","Mirassol","Lanús","Always Ready","Independiente del Valle","Rosario Central","UCV FC","Libertad"


                    ]
                }
            },
            "Copa Sudamericana": {
                "tipo": "copa_internacional",
                "nivel": 2,
                "temporadas": {
                    "2026": [
                        "Alianza Lima", "Argentinos Juniors", "Atlético Bucaramanga",
                        "Audax Italiano", "Barcelona SC", "Ceará", "Cerro Porteño",
                        "Cienciano", "Coquimbo Unido", "Deportes Tolima", "Deportivo Cali",
                        "Deportivo Pereira", "Godoy Cruz", "Guaraní", "Huachipato",
                        "Independiente", "Independiente Medellín", "Lanús", "Melgar",
                        "Montevideo Wanderers", "Nublense", "Once Caldas", "Palestino",
                        "Santa Fe", "Sporting Cristal", "Unión Española", "Universidad Católica",
                        "Vasco da Gama", "Vitória"
                    ]
                }
            }
        },
        "CONCACAF": {
            "MLS Playoffs": {
                "tipo": "copa_internacional",
                "nivel": 1,
                "temporadas": {
                    "2026": [
                        "Inter Miami", "LA Galaxy", "Los Angeles FC", "New York Red Bulls",
                        "Philadelphia Union", "Seattle Sounders", "Atlanta United", "Columbus Crew",
                        "Cincinnati FC", "Orlando City", "New England Revolution", "Portland Timbers"
                    ]
                }
            }
        }
    }
}


# ============================================================
# FUNCIONES DE CONSULTA
# ============================================================

def obtener_continentes():
    """Obtiene la lista de continentes disponibles"""
    return list(ESTRUCTURA.keys())

def obtener_paises(continente=None):
    """Obtiene la lista de países. Si se especifica continente, filtra."""
    if continente:
        return list(ESTRUCTURA.get(continente, {}).keys())
    paises = []
    for cont in ESTRUCTURA.values():
        paises.extend(cont.keys())
    return paises

def obtener_ligas(continente, pais):
    """Obtiene las ligas de un país"""
    try:
        return list(ESTRUCTURA[continente][pais].keys())
    except KeyError:
        return []

def obtener_temporadas(continente, pais, liga):
    """Obtiene las temporadas de una liga"""
    try:
        return list(ESTRUCTURA[continente][pais][liga]["temporadas"].keys())
    except KeyError:
        return []

def obtener_equipos(continente, pais, liga, temporada):
    """Obtiene los equipos de una temporada específica"""
    try:
        return ESTRUCTURA[continente][pais][liga]["temporadas"][temporada]
    except KeyError:
        return []

def obtener_info_liga(continente, pais, liga):
    """Obtiene información de una liga (tipo, nivel)"""
    try:
        info = ESTRUCTURA[continente][pais][liga]
        return {
            'tipo': info.get('tipo', 'liga'),
            'nivel': info.get('nivel', 1),
            'temporadas': list(info.get('temporadas', {}).keys())
        }
    except KeyError:
        return None

def buscar_equipo(nombre):
    """Busca un equipo en TODAS las ligas y devuelve todas las coincidencias"""
    resultados = []
    for continente, paises in ESTRUCTURA.items():
        for pais, ligas in paises.items():
            for liga, info in ligas.items():
                for temporada, equipos in info.get("temporadas", {}).items():
                    for equipo in equipos:
                        if nombre.lower() in equipo.lower():
                            resultados.append({
                                'continente': continente,
                                'pais': pais,
                                'liga': liga,
                                'temporada': temporada,
                                'equipo': equipo
                            })
    return resultados

def obtener_todas_las_ligas():
    """Devuelve TODAS las ligas en formato plano para compatibilidad"""
    resultado = {}
    for continente, paises in ESTRUCTURA.items():
        for pais, ligas in paises.items():
            for liga, info in ligas.items():
                for temporada in info.get("temporadas", {}):
                    clave = f"{pais}|{liga}|{temporada}"
                    resultado[clave] = info["temporadas"][temporada]
    return resultado


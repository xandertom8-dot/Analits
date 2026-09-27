"""
Diccionario de aliases de equipos — VERSIÓN LIMPIA
- Sin duplicados (un canónico por equipo)
- Nombres cortos (Opción A)
- Tildes correctas
- Ordenado por país/región
"""

ALIASES_EQUIPOS = {
    # =====================================================================
    # PORTUGAL — Primeira Liga
    # =====================================================================
    "Benfica": ["SL Benfica", "S.L. Benfica", "Sport Lisboa e Benfica"],
    "Porto": ["FC Porto", "F.C. Porto", "Futebol Clube do Porto"],
    "Sporting CP": ["Sporting Lisboa", "Sporting", "Sporting de Lisboa", "Sporting Portugal", "Sporting Clube de Portugal"],
    "Braga": ["SC Braga", "S.C. Braga", "Sporting Clube de Braga"],
    "Vitória Guimarães": ["Guimarães", "Vitória SC", "Vitoria Guimaraes", "Vitória de Guimarães", "Vitória de Guimaraes"],
    "Famalicão": ["FC Famalicão", "Famalicao", "F.C. Famalicão", "FC Famalicao"],
    "Marítimo": ["Maritimo", "CS Marítimo", "Club Sport Marítimo"],
    "Estoril Praia": ["Estoril", "Estoril-Praia", "GD Estoril Praia"],
    "Casa Pia": ["Casa Pia AC", "Casa Pia A.C."],
    "Estrela Amadora": ["Estrela", "Estrela da Amadora", "CF Estrela Amadora"],
    "Moreirense": ["Moreirense FC", "Moreirense F.C."],
    "Rio Ave": ["Rio Ave FC", "Rio Ave F.C."],
    "Santa Clara": ["CD Santa Clara", "Santa Clara Açores"],
    "Arouca": ["FC Arouca", "F.C. Arouca"],
    "Gil Vicente": ["Gil Vicente FC", "Gil Vicente F.C."],
    "Nacional": ["CD Nacional", "Nacional Madeira", "Nacional da Madeira", "C.D. Nacional"],
    "Farense": ["SC Farense", "Farense SC"],
    "AVS": ["AVS Futebol SAD", "AVS SAD", "Aves SAD", "AVS Futebol"],
    "Alverca": ["Futebol Clube de Alverca", "FC Alverca", "Alverca FC"],
    "Académico Viseu": ["Académico de Viseu", "Academico Viseu", "Académico de Viseu Futebol Clube", "Ac. Viseu"],
    "Portimonense": ["Portimonense SC", "Portimonense S.C."],

    # =====================================================================
    # ESPAÑA — LaLiga
    # =====================================================================
    "Barcelona": ["FC Barcelona", "Barça", "Barca", "F.C. Barcelona", "FCB"],
    "Real Madrid": ["Real Madrid CF", "R. Madrid", "Madrid", "Real Madrid Club de Fútbol"],
"Atlético de Madrid": [
    "Atlético Madrid", "Atletico de Madrid", "Atleti", "Atlético","Atletico Madrid", "Atlético de Madrid CF","Club Atlético de Madrid"],
    "Sevilla": ["Sevilla FC", "Sevilla F.C.", "Sevilla Club de Fútbol"],
    "Rayo Vallecano": ["Rayo", "Rayo Vallecano de Madrid", "Rayo Vallecano CF"],
    "Athletic Club": ["Athletic Bilbao", "Athletic de Bilbao", "Athletic", "Athletic Club Bilbao"],
    "Real Sociedad": ["Real Sociedad de Fútbol", "La Real", "Real Sociedad de Futbol", "Erreala"],
    "Real Betis": ["Betis", "Real Betis Balompié", "Betis Balompié", "Real Betis Balompie"],
    "Villarreal": ["Villarreal CF", "Villarreal C.F.", "Villarreal Club de Fútbol"],
    "Valencia": ["Valencia CF", "Valencia C.F.", "Valencia Club de Fútbol"],
    "Celta de Vigo": ["Celta", "RC Celta", "R.C. Celta de Vigo", "Real Club Celta de Vigo"],
    "Girona": ["Girona FC", "Girona F.C.", "Girona Futbol Club"],
    "Osasuna": ["CA Osasuna", "Club Atlético Osasuna", "Atlético Osasuna"],
    "Getafe": ["Getafe CF", "Getafe C.F.", "Getafe Club de Fútbol"],
    "Espanyol": ["RCD Espanyol", "Espanyol de Barcelona", "RCD Espanyol de Barcelona", "Real Club Deportivo Espanyol"],
    "Alavés": ["Deportivo Alavés", "Alaves", "Deportivo Alaves", "CD Alavés"],
    "Mallorca": ["RCD Mallorca", "Real Club Deportivo Mallorca", "Mallorca FC"],
    "Las Palmas": ["UD Las Palmas", "Unión Deportiva Las Palmas", "Las Palmas UD"],
    "Leganés": ["CD Leganés", "Leganes", "Club Deportivo Leganés"],
    "Elche": ["Elche CF", "Elche C.F.", "Elche Club de Fútbol"],
    "Levante": ["Levante UD", "Levante Unión Deportiva", "Levante U.D."],
    "Deportivo La Coruña": ["Deportivo de La Coruña", "Deportivo de A Coruña", "Deportivo", "Depor", "RC Deportivo", "Deportivo de la Coruna"],
    "Racing Santander": ["Racing de Santander", "Real Racing Club", "Racing Club de Santander"],
    "Málaga": ["Málaga CF", "Malaga", "Málaga Club de Fútbol"],

    # =====================================================================
    # INGLATERRA — Premier League
    # =====================================================================
    "Manchester City": ["Man City", "MCFC", "City", "Manchester City FC"],
    "Arsenal": ["Arsenal FC", "The Gunners", "Arsenal Football Club"],
    "Hull City": ["Hull", "Hull City AFC", "The Tigers"],
    "Chelsea": ["Chelsea FC", "The Blues", "Chelsea Football Club"],
    "Brentford": ["Brentford FC", "The Bees", "Brentford Football Club"],
    "Liverpool": ["Liverpool FC", "The Reds", "Liverpool Football Club"],
    "Newcastle United": ["Newcastle", "The Magpies", "Newcastle United FC"],
    "Everton": ["Everton FC", "The Toffees", "Everton Football Club"],
    "Leeds United": ["Leeds", "The Whites", "Leeds United FC"],
    "Brighton & Hove Albion": ["Brighton", "The Seagulls", "Brighton and Hove Albion", "Brighton & Hove Albion FC"],
    "Manchester United": ["Man United", "Man Utd", "MUFC", "United", "Manchester United FC"],
    "Sunderland": ["Sunderland AFC", "The Black Cats", "Sunderland Association Football Club"],
    "Crystal Palace": ["Palace", "The Eagles", "Crystal Palace FC"],
    "Ipswich Town": ["Ipswich", "The Tractor Boys", "Ipswich Town FC"],
    "Bournemouth": ["AFC Bournemouth", "The Cherries", "Bournemouth FC"],
    "Nottingham Forest": ["Forest", "The Reds", "Nottingham Forest FC"],
    "Aston Villa": ["Villa", "The Villans", "Aston Villa FC"],
    "Tottenham Hotspur": ["Tottenham", "Spurs", "Tottenham Hotspur FC"],
    "Fulham": ["Fulham FC", "The Cottagers", "Fulham Football Club"],
    "Coventry City": ["Coventry", "The Sky Blues", "Coventry City FC"],
    "Wolverhampton": ["Wolves", "Wolverhampton Wanderers", "Wolverhampton Wanderers FC"],
    "West Ham United": ["West Ham", "The Hammers", "West Ham United FC"],
    "West Bromwich Albion": ["West Brom", "WBA", "The Baggies", "West Bromwich Albion FC"],
    "Swansea City": ["Swansea", "The Swans", "Swansea City AFC"],
    "Queens Park Rangers": ["QPR", "The Hoops", "Queens Park Rangers FC"],
    "Charlton Athletic": ["Charlton", "The Addicks", "Charlton Athletic FC"],
    "Middlesbrough": ["Boro", "The Smoggies", "Middlesbrough FC"],
    "Bristol City": ["Bristol", "The Robins", "Bristol City FC"],
    "Millwall": ["The Lions", "Millwall FC", "Millwall Football Club"],
    "Norwich City": ["Norwich", "The Canaries", "Norwich City FC"],
    "Sheffield United": ["Sheffield Utd", "The Blades", "Sheffield United FC"],
    "Watford": ["The Hornets", "Watford FC", "Watford Football Club"],
    "Southampton": ["Saints", "The Saints", "Southampton FC"],
    "Birmingham City": ["Birmingham", "The Blues", "Birmingham City FC"],
    "Stoke City": ["Stoke", "The Potters", "Stoke City FC"],
    "Wrexham": ["Wrexham AFC", "The Red Dragons", "Wrexham Association Football Club"],
    "Portsmouth": ["Pompey", "The Blues", "Portsmouth FC"],
    "Blackburn": ["Blackburn Rovers", "Rovers", "Blackburn Rovers FC"],
    "Lincoln City": ["Lincoln", "The Imps", "Lincoln City FC"],
    "Cardiff City": ["Cardiff", "The Bluebirds", "Cardiff City FC"],
    "Bolton Wanderers": ["Bolton", "The Trotters", "Bolton Wanderers FC"],
    "Derby County": ["Derby", "The Rams", "Derby County FC"],
    "Burnley": ["The Clarets", "Burnley FC", "Burnley Football Club"],
    "Preston North End": ["Preston", "The Lilywhites", "Preston North End FC"],

    # =====================================================================
    # ITALIA — Serie A / Serie B
    # =====================================================================
    "Roma": ["AS Roma", "A.S. Roma", "Associazione Sportiva Roma"],
    "Inter Milan": ["Inter", "Inter de Milán", "Internazionale", "FC Internazionale Milano"],
    "Lazio": ["SS Lazio", "S.S. Lazio", "Società Sportiva Lazio"],
    "Como": ["Como 1907", "Calcio Como", "Como Calcio"],
    "Milan": ["AC Milan", "A.C. Milan", "Associazione Calcio Milan"],
    "Juventus": ["Juve", "Juventus FC", "Juventus Football Club"],
    "Frosinone": ["Frosinone Calcio", "Calcio Frosinone"],
    "Atalanta": ["Atalanta BC", "Atalanta Bergamasca Calcio", "La Dea"],
    "Cagliari": ["Cagliari Calcio", "Cagliari FC"],
    "Sassuolo": ["US Sassuolo", "Unione Sportiva Sassuolo Calcio", "Sassuolo Calcio"],
    "Udinese": ["Udinese Calcio", "Udinese FC"],
    "Napoli": ["SSC Napoli", "S.S.C. Napoli", "Società Sportiva Calcio Napoli"],
    "Torino": ["Torino FC", "Toro", "Torino Football Club"],
    "Lecce": ["US Lecce", "Unione Sportiva Lecce", "Lecce Calcio"],
    "Fiorentina": ["ACF Fiorentina", "La Viola", "Fiorentina FC"],
    "Bologna": ["Bolonia", "Bologna FC", "Bologna Football Club 1909"],
    "Parma": ["Parma Calcio", "Parma FC", "Parma Calcio 1913"],
    "Monza": ["AC Monza", "Monza Calcio", "Associazione Calcio Monza"],
    "Genoa": ["Génova", "Genoa CFC", "Genoa Cricket and Football Club"],
    "Venezia": ["Venezia FC", "Venezia Calcio", "Venezia Football Club"],
    "Palermo": ["Palermo FC", "Palermo Calcio", "US Città di Palermo"],
    "Mantova": ["Mantova 1911", "Mantova Calcio", "AC Mantova"],
    "Südtirol": ["FC Südtirol", "Sudtirol", "Sudtirol Alto Adige"],
    "Ascoli": ["Ascoli Calcio", "Ascoli Picchio", "Ascoli Calcio 1898"],
    "Modena": ["Modena FC", "Modena Calcio", "Modena Football Club"],
    "Avellino": ["US Avellino", "US Avellino 1912", "Avellino Calcio"],
    "Pisa": ["Pisa SC", "Pisa Calcio", "Sporting Club Pisa"],
    "Empoli": ["Empoli FC", "Empoli Calcio", "Empoli Football Club"],
    "Arezzo": ["Arezzo Calcio", "AC Arezzo", "US Arezzo"],
    "Cesena": ["Cesena FC", "Cesena Calcio", "AC Cesena"],
    "Padova": ["Padova Calcio", "Calcio Padova", "AC Padova"],
    "Vicenza": ["Vicenza Calcio", "LR Vicenza", "Vicenza Virtus"],
    "Hellas Verona": ["Verona", "Hellas", "Hellas Verona FC"],
    "Virtus Entella": ["Entella", "AC Virtus Entella"],
    "Benevento": ["Benevento Calcio", "Benevento FC"],
    "Cremonese": ["Cremonese Calcio", "US Cremonese", "Cremonese FC"],
    "Carrarese": ["Carrarese Calcio", "Carrarese 1908"],
    "Sampdoria": ["UC Sampdoria", "Samp", "Sampdoria FC"],
    "Juve Stabia": ["SS Juve Stabia", "Juve Stabia Calcio", "Stabia"],
    "Catanzaro": ["US Catanzaro", "Catanzaro Calcio", "Catanzaro FC"],

    # =====================================================================
    # ALEMANIA — Bundesliga / Bundesliga 2
    # =====================================================================
    "Augsburgo": ["F. C. Augsburgo", "Augsburg", "FC Augsburg"],
    "Freiburg": ["SC Freiburg", "Sport-Club Freiburg"],
    "Borussia Dortmund": ["Dortmund", "BVB"],
    "Elversberg": ["SV Elversberg", "SV 07 Elversberg"],
    "Mainz 05": ["Mainz", "1. FSV Mainz 05"],
    "Bayern de Múnich": ["Bayern Munich", "Bayern Múnich", "FC Bayern", "Bayern München", "Bayern"],
    "Schalke 04": ["Schalke", "FC Schalke 04", "S04"],
    "Bayer Leverkusen": ["Leverkusen", "Bayer 04 Leverkusen", "Bayer"],
    "RB Leipzig": ["Leipzig", "RasenBallsport Leipzig"],
    "Stuttgart": ["VfB Stuttgart", "VfB"],
    "Werder Bremen": ["Werder", "Bremen", "SV Werder Bremen"],
    "Colonia": ["FC Cologne", "Köln", "FC Köln", "1. FC Köln"],
    "Paderborn 07": ["SC Paderborn 07", "Paderborn", "SC Paderborn"],
    "Eintracht Frankfurt": ["Frankfurt", "Eintracht"],
    "Union Berlin": ["FC Union Berlin", "Union", "1. FC Union Berlin"],
    "Hoffenheim": ["TSG Hoffenheim", "TSG 1899 Hoffenheim"],
    "Borussia Mönchengladbach": ["Mönchengladbach", "Gladbach", "Borussia M'gladbach", "BMG", "Borussia Monchengladbach"],
    "Hamburgo": ["Hamburg SV", "Hamburger SV", "HSV", "Hamburg"],
    "Núremberg": ["FC Nürnberg", "Nurnberg", "1. FC Nürnberg", "Nürnberg"],
    "Hertha Berlin": ["Hertha", "Hertha BSC", "Hertha Berlín"],
    "Heidenheim": ["1. FC Heidenheim 1846", "1. FC Heidenheim", "Heidenheim 1846"],
    "Wolfsburgo": ["VfL Wolfsburg", "Wolfsburg"],
    "Kaiserslautern": ["1. FC Kaiserslautern", "FCK"],
    "Bochum": ["VfL Bochum", "VfL Bochum 1848"],
    "Magdeburgo": ["FC Magdeburg", "Magdeburg", "1. FC Magdeburg"],
    "Osnabrück": ["VfL Osnabruck", "Osnabruck", "VfL Osnabrück"],
    "Karlsruhe": ["Karlsruher SC", "KSC"],
    "Cottbus": ["Energie Cottbus", "FC Energie Cottbus"],
    "Bielefeld": ["Arminia Bielefeld", "DSC Arminia Bielefeld", "Arminia"],
    "Greuther Fürth": ["SpVgg Greuther Fürth", "Fürth", "SpVgg Fürth"],
    "Hannover": ["Hannover 96", "H96"],
    "Darmstadt": ["SV Darmstadt 98", "SV Darmstadt", "Darmstadt 98"],
    "Eintracht Braunschweig": ["Braunschweig", "TSV Eintracht Braunschweig", "TSV Braunschweig"],
    "St. Pauli": ["St Pauli", "FC St. Pauli", "San Pauli"],
    "Holstein Kiel": ["Kiel", "KSV Holstein"],
    "Dynamo Dresden": ["Dresde", "Dresden", "SG Dynamo Dresden"],

    # =====================================================================
    # FRANCIA — Ligue 1 / Ligue 2
    # =====================================================================
    "Rennes": ["Stade Rennais", "Stade Rennais FC", "SRFC"],
    "Mónaco": ["AS Mónaco", "Monaco", "AS Monaco", "ASM"],
    "Paris FC": ["Paris Football Club", "PFC"],
    "Lyon": ["Olympique de Lyon", "Olympique Lyonnais", "OL"],
    "Lille": ["LOSC Lille", "Lille OSC", "LOSC"],
    "Strasbourg": ["RC Strasbourg", "Strasbourg Alsace", "RCSA"],
    "Brest": ["Stade Brestois", "Stade Brestois 29", "SB29"],
    "Lorient": ["FC Lorient", "FCL"],
    "Troyes": ["ES Troyes AC", "Troyes AC", "ESTAC"],
    "Lens": ["RC Lens", "Racing Club de Lens", "RCL"],
    "Marseille": ["Olympique de Marseille", "OM"],
    "Angers": ["Angers SCO", "SCO Angers"],
    "Paris Saint-Germain": ["PSG", "Paris SG", "París Saint-Germain", "Paris Saint Germain","Paris Saint-Germain FC"],
    "Le Mans": ["Le Mans FC", "Le Mans UC 72", "LMFC"],
    "Nice": ["OGC Nice", "Olympique Gymnaste Club Nice", "OGCN"],
    "Le Havre": ["Le Havre AC", "HAC", "Le Havre Athletic Club"],
    "Toulouse": ["Toulouse FC", "TFC"],
    "Auxerre": ["AJ Auxerre", "AJA"],
    "Ajaccio": ["AC Ajaccio", "ACA"],
    "Amiens": ["Amiens SC", "ASC"],
    "Annecy": ["FC Annecy", "FCA"],
    "Bastia": ["SC Bastia", "SCB"],
    "Caen": ["SM Caen", "Stade Malherbe Caen"],
    "Clermont": ["Clermont Foot", "Clermont Foot 63", "CF63"],
    "Dunkerque": ["USL Dunkerque", "USLD"],
    "Grenoble": ["Grenoble Foot 38", "GF38"],
    "Guingamp": ["EA Guingamp", "EAG"],
    "Laval": ["Stade Lavallois", "Stade Lavallois Mayenne FC"],
    "Martigues": ["FC Martigues", "FCM"],
    "Metz": ["FC Metz", "FCMetz"],
    "Pau": ["Pau FC", "Pau Football Club"],
    "Red Star": ["Red Star FC", "Red Star 93"],
    "Rodez": ["Rodez AF", "RAF"],

    # =====================================================================
    # PAÍSES BAJOS — Eredivisie
    # =====================================================================
    "Ajax": ["Ajax Amsterdam", "Amsterdam", "AFC Ajax"],
    "AZ Alkmaar": ["AZ", "Alkmaar"],
    "PSV Eindhoven": ["PSV", "Eindhoven", "Philips Sport Vereniging"],
    "Feyenoord": ["Feyenoord Rotterdam", "Rotterdam"],
    "Excelsior": ["SBV Excelsior", "Excelsior Rotterdam"],
    "FC Twente": ["Twente", "Twente Enschede"],
    "Fortuna Sittard": ["Fortuna", "Sittard"],
    "Go Ahead Eagles": ["Go Ahead", "Eagles"],
    "NEC Nijmegen": ["NEC", "Nijmegen"],
    "FC Groningen": ["Groningen", "FCG"],
    "Sparta Rotterdam": ["Sparta"],
    "Heerenveen": ["SC Heerenveen", "sc Heerenveen"],
    "PEC Zwolle": ["Zwolle", "PEC"],
    "Telstar": ["SC Telstar", "Telstar Velsen"],
    "FC Utrecht": ["Utrecht", "FCU"],
    "Willem II": ["Willem II Tilburg", "WII"],
    "ADO Den Haag": ["ADO", "Den Haag"],
    "SC Cambuur": ["Cambuur", "Cambuur Leeuwarden"],

    # =====================================================================
    # BÉLGICA — Pro League
    # =====================================================================
    "Gent": ["KAA Gent", "La Gantoise"],
    "Union Saint-Gilloise": ["Union SG", "Union St.-Gilloise", "Royale Union Saint-Gilloise"],
    "Club Brugge": ["Club Brujas", "Brujas", "Club Brugge KV"],
    "Charleroi": ["Royal Charleroi SC", "Sporting Charleroi", "RCSC"],
    "Zulte Waregem": ["Zulte-Waregem", "SV Zulte Waregem", "Essevee"],
    "Standard Liège": ["Standard Liege", "Standard de Lieja", "Standard"],
    "Anderlecht": ["RSC Anderlecht", "Sporting Anderlecht"],
    "Sint-Truiden": ["Sint-Truidense", "STVV", "Sint-Truidense VV"],
    "Genk": ["Racing Genk", "KRC Genk"],
    "Lommel": ["Lommel SK", "Lommel United"],
    "Antwerp": ["Royal Antwerp", "Antwerp FC", "Royal Antwerp FC"],
    "Waasland-Beveren": ["Waasland Beveren", "SK Beveren"],
    "Westerlo": ["KVC Westerlo"],
    "Cercle Brugge": ["Cercle Brugge KSV", "Cercle"],
    "Mechelen": ["KV Mechelen", "Yellow Red KV Mechelen"],
    "La Louvière": ["RAAL La Louvière", "RAAL", "RAAL La Louviere"],
    "Oud-Heverlee Leuven": ["OH Leuven", "OHL"],
    "Kortrijk": ["KV Kortrijk"],

    # =====================================================================
    # TURQUÍA — Süper Lig
    # =====================================================================
    "Beşiktaş": ["Besiktas", "Besiktas JK", "Beşiktaş Jimnastik Kulübü"],
    "Galatasaray": ["Galatasaray SK", "Gala", "Galatasaray Spor Kulübü"],
    "Kocaelispor": ["Kocaeli", "Kocaeli Spor"],
    "Trabzonspor": ["Trabzon", "Trabzonspor Kulübü"],
    "Amed SFK": ["Amed Sportif", "Amed"],
    "Gaziantep FK": ["Gaziantep", "Gaziantep Futbol Kulübü", "GFK"],
    "Alanyaspor": ["Alanya", "Alanya Spor Kulübü"],
    "Gençlerbirliği": ["Genclerbirligi", "Gençlerbirliği SK"],
    "Fenerbahçe": ["Fenerbahce", "Fener", "Fenerbahçe SK"],
    "Kasımpaşa": ["Kasimpasa", "Kasımpaşa SK"],
    "Rizespor": ["Caykur Rizespor", "Çaykur Rizespor"],
    "Başakşehir": ["Istanbul Basaksehir", "İstanbul Başakşehir FK"],
    "Samsunspor": ["Samsun", "Samsunspor Kulübü"],
    "Çorum FK": ["Corum FK", "Çorum"],
    "Erzurum BB": ["Erzurumspor", "Erzurum Büyükşehir Belediyespor"],
    "Eyüpspor": ["Eyupspor", "Eyüp Spor Kulübü"],
    "Göztepe": ["Goztepe", "Göztepe SK"],
    "Konyaspor": ["Konya", "Konyaspor Kulübü"],

    # =====================================================================
    # ESCOCIA — Scottish Premiership
    # =====================================================================
    "Celtic": ["Celtic FC", "The Bhoys", "Celtic Football Club"],
    "Rangers": ["Rangers FC", "The Gers", "Rangers Football Club"],
    "Heart of Midlothian": ["Hearts", "Heart of Midlothian FC", "Hearts of Midlothian"],
    "St. Mirren": ["St Mirren", "St Mirren FC", "The Buddies"],
    "Motherwell": ["Motherwell FC", "The Well", "Motherwell Football Club"],
    "Dundee": ["Dundee FC", "The Dark Blues", "Dundee Football Club"],
    "St. Johnstone": ["St Johnstone", "St Johnstone FC", "The Saints"],
    "Hibernian": ["Hibs", "Hibernian FC", "Hibernian Football Club"],
    "Dundee United": ["Dundee Utd", "The Terrors", "Dundee United FC"],
    "Aberdeen": ["Aberdeen FC", "The Dons", "Aberdeen Football Club"],
    "Falkirk": ["Falkirk FC", "The Bairns", "Falkirk Football Club"],
    "Kilmarnock": ["Kilmarnock FC", "Killie", "Kilmarnock Football Club"],

    # =====================================================================
    # UCRANIA — Ukrainian Premier League
    # =====================================================================
    "Bukovyna": ["Bukovyna Chernivtsi", "FC Bukovyna"],
    "Cherkasy": ["FC Cherkasy", "Cherkashchyna"],
    "Chornomorets Odesa": ["Chernomorets O.", "Chernomorets Odessa", "Chernomorets", "Chornomorets"],
    "Dynamo Kyiv": ["Dinamo Kiev", "Dynamo Kiev"],
    "Epitsentr": ["Epicentr", "FC Epitsentr"],
    "Karpaty Lviv": ["Karpaty Lvov", "FC Karpaty"],
    "Kolos Kovalivka": ["Kolos", "FC Kolos"],
    "Kryvbas": ["Kryvbas KR", "Kryvbas Kryvyi Rih", "FC Kryvbas"],
    "Kudrivka": ["FC Kudrivka", "Kudrivka-Nyva"],
    "Livyi Bereh": ["FC Livyi Bereh", "Left Bank"],
    "Metalist 1925": ["Metalist 1925 Kharkiv", "Metalist Kharkiv", "FC Metalist 1925"],
    "Obolon Kyiv": ["Obolon", "FC Obolon"],
    "Polissya Zhytomyr": ["Polessya Zhitomir", "Polissya", "FC Polissya"],
    "Shakhtar Donetsk": ["Shakhtar", "FC Shakhtar"],
    "Veres Rivne": ["Veres Livne", "Veres", "FC Veres"],
    "Zorya Luhansk": ["Zorya", "FC Zorya"],

    # =====================================================================
    # GRECIA — Super League
    # =====================================================================
    "Panathinaikos": ["Panathinaikos FC", "PAO"],
    "Panetolikos": ["Panetolikos FC", "PAE Panetolikos"],
    "AEK Athens": ["AEK", "AEK Atenas", "AEK Athens FC"],
    "Olympiacos": ["Olympiacos FC", "Olympiacos Piraeus"],
    "PAOK": ["PAOK FC", "PAOK Thessaloniki"],
    "OFI Crete": ["OFI", "OFI Creta", "OFI Crete FC"],
    "Aris": ["Aris FC", "Aris Thessaloniki"],
    "Iraklis": ["Iraklis FC", "Iraklis Thessaloniki"],
    "Volos NFC": ["Volos", "Volos Football Club"],
    "Atromitos": ["Atromitos FC", "Atromitos Athens"],
    "Kalamata": ["Kalamata FC"],
    "Kifisia": ["Kifisia FC"],
    "Asteras Tripolis": ["Asteras Tripoli", "Asteras", "Asteras Tripoli FC"],
    "Levadiakos": ["Levadiakos FC"],

    # =====================================================================
    # SUIZA — Super League
    # =====================================================================
    "Basel": ["FC Basel", "Basilea", "FC Basel 1893"],
    "Lugano": ["FC Lugano"],
    "Vaduz": ["FC Vaduz"],
    "Grasshopper": ["Grasshopper Zurich", "Grasshopper Club Zürich", "GC"],
    "Lausanne": ["Lausanne Sports", "Lausanne-Sport", "FC Lausanne-Sport"],
    "Luzern": ["FC Luzern", "Lucerna"],
    "Servette": ["Servette FC", "Servette Genève"],
    "Sion": ["FC Sion"],
    "St. Gallen": ["FC St. Gallen", "San Gallo", "FC St. Gallen 1879"],
    "Thun": ["FC Thun", "FC Thun Berner Oberland"],
    "Young Boys": ["BSC Young Boys", "YB", "Young Boys Bern"],
    "Zürich": ["Zurich", "FC Zurich"],

    # =====================================================================
    # AUSTRIA — Bundesliga
    # =====================================================================
    "LASK Linz": ["LASK", "Linzer ASK"],
    "RB Salzburg": ["Salzburg", "Red Bull Salzburg", "FC Red Bull Salzburg"],
    "Rapid Vienna": ["Rapid Viena", "Rapid Wien", "SK Rapid Wien"],
    "Sturm Graz": ["SK Sturm Graz", "Sturm"],
    "WSG Tirol": ["WSG Swarovski Tirol", "WSG"],
    "Hartberg": ["TSV Hartberg"],
    "Austria Lustenau": ["Lustenau", "SC Austria Lustenau"],
    "Ried": ["SV Josko Ried", "SV Ried"],
    "Wolfsberger AC": ["Wolfsberger", "WAC"],
    "Grazer AK": ["GAK", "Grazer Athletiksport Klub"],
    "Rheindorf Altach": ["SC Rheindorf Altach", "Altach", "SCR Altach"],
    "Austria Vienna": ["Austria Viena", "Austria Wien", "FK Austria Wien"],

    # =====================================================================
    # DINAMARCA — Superliga
    # =====================================================================
    "Copenhagen": ["F.C. København", "FCK", "FC Copenhagen", "København"],
    "Midtjylland": ["FC Midtjylland", "FCM"],
    "Nordsjælland": ["FC Nordsjælland", "FCN"],
    "Viborg": ["Viborg FF", "VFF"],
    "Brøndby": ["Brøndby IF", "Brondby"],
    "Randers": ["Randers FC", "RFC"],
    "Horsens": ["AC Horsens", "ACH"],
    "Lyngby": ["Lyngby Boldklub", "Lyngby BK"],
    "Silkeborg": ["Silkeborg IF", "SIF"],
    "Odense": ["Odense Boldklub", "OB", "Odense BK"],
    "Aarhus": ["Aarhus GF", "AGF"],
    "Sønderjyske": ["Sonderjyske", "SE"],

    # =====================================================================
    # NORUEGA — Eliteserien
    # =====================================================================
    "Bodø/Glimt": ["Bodo/Glimt", "Bodo Glimt", "FK Bodø/Glimt"],
    "Viking": ["Viking FK", "Viking Stavanger"],
    "Tromsø": ["Tromso", "Tromsø IL"],
    "Molde": ["Molde FK", "MFK"],
    "Lillestrøm": ["Lillestrom", "LSK"],
    "Rosenborg": ["Rosenborg BK", "RBK"],
    "Brann": ["SK Brann", "Brann Bergen"],
    "Fredrikstad": ["Fredrikstad FK", "FFK"],
    "Sarpsborg 08": ["Sarpsborg", "Sarpsborg FK", "SFK"],
    "HamKam": ["Hamarkameratene", "Ham-Kam"],
    "Vålerenga": ["Valerenga", "VIF"],
    "Sandefjord": ["Sandefjord Fotball", "SF"],
    "Kristiansund": ["Kristiansund BK", "KBK"],
    "KFUM Oslo": ["KFUM", "KFUM-Kameratene Oslo"],
    "Aalesund": ["Aalesunds FK", "AaFK"],
    "IK Start": ["Start", "Start Kristiansand"],

    # =====================================================================
    # SUECIA — Allsvenskan
    # =====================================================================
    "Sirius": ["IK Sirius", "Sirius Uppsala"],
    "Djurgården": ["Djurgarden", "Djurgårdens IF", "DIF"],
    "Hammarby": ["Hammarby IF", "HIF"],
    "Häcken": ["BK Häcken", "Hacken"],
    "AIK": ["AIK Solna", "AIK Fotboll"],
    "Elfsborg": ["IF Elfsborg", "IFE"],
    "Malmö FF": ["Malmo FF", "Malmö", "MFF"],
    "Västerås": ["Västerås SK", "Vasteras", "VSK"],
    "GAIS": ["Göteborg Atlet- och Idrottssällskap"],
    "Brommapojkarna": ["IF Brommapojkarna", "BP"],
    "IFK Göteborg": ["Goteborg", "IFK"],
    "Mjällby": ["Mjällby AIF", "Mjallby", "MAIF"],
    "Kalmar FF": ["Kalmar", "KFF"],
    "Degerfors": ["Degerfors IF", "DIF"],
    "Örgryte": ["Örgryte IS", "Orgryte", "ÖIS"],
    "Halmstad": ["Halmstads BK", "HBK"],

    # =====================================================================
    # MÉXICO — Liga MX
    # =====================================================================
    "América": ["Club América", "América CD", "Águilas del América"],
    "Chivas Guadalajara": ["Guadalajara", "Chivas", "CD Guadalajara"],
    "Toluca": ["Deportivo Toluca", "Toluca FC", "Diablos Rojos"],
    "Tijuana": ["Club Tijuana", "Xolos", "Xolos de Tijuana"],
    "Atlas": ["Atlas FC", "Atlas de Guadalajara", "Zorros"],
    "Cruz Azul": ["Cruz Azul FC", "La Máquina", "Cementeros"],
    "Pumas UNAM": ["Pumas", "UNAM Pumas", "Club Universidad Nacional"],
    "Querétaro": ["Queretaro", "Gallos Blancos", "Querétaro FC"],
    "Puebla": ["Puebla FC", "La Franja"],
    "León": ["Club León", "León FC", "La Fiera"],
    "Monterrey": ["CF Monterrey", "Rayados", "Rayados de Monterrey"],
    "Pachuca": ["CF Pachuca", "Tuzos", "Tuzos del Pachuca"],
    "Necaxa": ["Club Necaxa", "Rayos"],
    "Atlante": ["Atlante FC", "Potros de Hierro"],
    "Tigres UANL": ["Tigres", "UANL Tigres", "Tigres de la UANL"],
    "Atlético San Luis": ["Atlético de San Luis", "San Luis", "Atletico de San Luis"],
    "Santos Laguna": ["Santos", "Club Santos Laguna", "Guerreros"],
    "Juárez": ["FC Juarez", "FC Juárez", "Bravos de Juárez"],

    # =====================================================================
    # ESTADOS UNIDOS — MLS
    # =====================================================================
    "Inter Miami": ["Inter Miami CF", "Miami CF"],
    "Nashville SC": ["Nashville", "Nashville Soccer Club", "NSC"],
    "New England Revolution": ["New England", "Revolution", "NER"],
    "Chicago Fire": ["Chicago Fire FC", "Fire", "CFC"],
    "Charlotte FC": ["Charlotte", "CLTFC"],
    "Orlando City": ["Orlando City SC", "Orlando", "OCSC"],
    "FC Cincinnati": ["Cincinnati", "Cincinnati FC", "FCC"],
    "Philadelphia Union": ["Philadelphia", "Union", "PHI"],
    "New York City FC": ["NYCFC", "New York City", "NYC FC"],
    "Toronto FC": ["Toronto", "TFC"],
    "DC United": ["D.C. United", "DCU"],
    "New York Red Bulls": ["NY Red Bulls", "Red Bull New York", "RBNY"],
    "Columbus Crew": ["Columbus", "Crew", "Columbus Crew SC"],
    "Atlanta United": ["Atlanta United FC", "Atlanta", "ATLUTD"],
    "Montreal Impact": ["CF Montréal", "Montreal", "CF Montreal"],
    "Vancouver Whitecaps": ["Vancouver", "Whitecaps", "VWFC"],
    "Houston Dynamo": ["Houston Dynamo FC", "Houston", "Dynamo"],
    "Los Angeles FC": ["LAFC", "Los Angeles Football Club"],
    "FC Dallas": ["Dallas", "FCD"],
    "San Jose Earthquakes": ["San Jose", "Earthquakes", "SJE"],
    "St. Louis City": ["St. Louis CITY SC", "St Louis City", "STL City"],
    "Colorado Rapids": ["Colorado", "Rapids", "CR"],
    "Portland Timbers": ["Portland", "Timbers", "PTFC"],
    "San Diego FC": ["San Diego", "SDFC"],
    "Real Salt Lake": ["RSL", "Salt Lake"],
    "Minnesota United": ["Minnesota United FC", "Minnesota", "MNUFC"],
    "LA Galaxy": ["Galaxy", "Los Angeles Galaxy", "LAG"],
    "Seattle Sounders": ["Seattle Sounders FC", "Seattle", "SSFC"],
    "Austin FC": ["Austin", "ATXFC"],
    "Sporting Kansas City": ["Sporting KC", "SKC"],

    # =====================================================================
    # COLOMBIA — Liga BetPlay
    # =====================================================================
    "América de Cali": ["América", "America de Cali", "Los Diablos Rojos"],
    "Deportes Tolima": ["Tolima", "El Vinotinto y Oro"],
    "Independiente Medellín": ["DIM", "Medellín", "Independiente Medellin"],
    "Millonarios": ["Millonarios FC", "Embajadores"],
    "Atlético Nacional": ["Nacional", "Atletico Nacional", "Verdolaga"],
    "Llaneros": ["Llaneros FC", "Llaneros de Villavicencio"],
    "Santa Fe": ["Independiente Santa Fe", "Los Cardenales"],
    "Águilas Doradas": ["Aguilas Doradas", "Águilas", "Rionegro Águilas"],
    "Atlético Bucaramanga": ["Bucaramanga", "Atletico Bucaramanga", "El Leopardo"],
    "Once Caldas": ["Caldas", "El Blanco Blanco"],
    "Deportivo Cali": ["Cali", "Los Azucareros"],
    "Cúcuta Deportivo": ["Cúcuta", "Cucuta Deportivo", "El Motilón"],
    "Internacional de Bogotá": ["Internacional", "Inter Bogotá"],
    "Fortaleza": ["Fortaleza CEIF", "Los Lanceros"],
    "Deportivo Pereira": ["Pereira", "El Matecaña"],
    "Jaguares": ["Jaguares de Córdoba", "Jaguares FC"],
    "Boyacá Chicó": ["Boyacá Chicó FC", "Chicó", "Boyaca Chico"],
    "Junior": ["Atlético Junior", "Atletico Junior", "Junior de Barranquilla"],
    "Deportivo Pasto": ["Pasto", "El Tricolor"],
    "Alianza FC": ["Alianza", "Alianza Petrolera"],

    # =====================================================================
    # ARGENTINA — Liga Profesional
    # =====================================================================
    "Vélez Sarsfield": ["Velez", "Vélez", "Club Atlético Vélez Sarsfield"],
    "Gimnasia (Mendoza)": ["Gimnasia Mendoza", "Gimnasia de Mendoza"],
    "Instituto (Córdoba)": ["Instituto", "Instituto de Córdoba", "Instituto Atlético Central Córdoba"],
    "Defensa y Justicia": ["Defensa", "Halcones de Varela"],
    "Unión (Santa Fe)": ["Unión", "Union Santa Fe", "Club Atlético Unión"],
    "Newell's Old Boys": ["Newells", "Newell's", "NOB"],
    "Independiente": ["Independiente de Avellaneda", "Rojo", "CA Independiente"],
    "Boca Juniors": ["Boca", "CA Boca Juniors", "Xeneize"],
    "Lanús": ["Club Atlético Lanús", "Granate"],
    "San Lorenzo": ["San Lorenzo de Almagro", "Ciclón", "CASLA"],
    "Deportivo Riestra": ["Riestra", "El Malevo"],
    "Platense": ["Club Atlético Platense", "Calamar"],
    "Estudiantes de La Plata": ["Estudiantes", "Estudiantes LP", "Pincharratas"],
    "Central Córdoba": ["Central Córdoba (Santiago del Estero)", "Central Córdoba SdE", "Ferroviario"],
    "Talleres": ["Talleres (Córdoba)", "Talleres de Córdoba", "La T"],
    "Argentinos Juniors": ["Argentinos", "El Bicho"],
    "Sarmiento": ["Sarmiento (Junín)", "Sarmiento de Junín", "Verde"],
    "Gimnasia": ["Gimnasia La Plata", "Gimnasia y Esgrima La Plata", "Lobo"],
    "Atlético Tucumán": ["Tucumán", "Atletico Tucuman", "Decano"],
    "Belgrano": ["Belgrano (Córdoba)", "Belgrano de Córdoba", "Pirata"],
    "Tigre": ["Club Atlético Tigre", "Matador"],
    "Rosario Central": ["Central", "Canalla"],
    "Independiente Rivadavia": ["Rivadavia", "Lepra"],
    "Barracas Central": ["Barracas", "Guapo"],
    "River Plate": ["River", "CA River Plate", "Millonario"],
    "Huracán": ["Huracan", "Club Atlético Huracán", "Globo"],
    "Banfield": ["Club Atlético Banfield", "Taladro"],
    "Estudiantes de Río Cuarto": ["Estudiantes Río Cuarto", "Estudiantes de Rio Cuarto", "León"],
    "Aldosivi": ["Club Atlético Aldosivi", "Tiburón"],
    "Racing Club": ["Racing", "Racing de Avellaneda", "La Academia"],

    # =====================================================================
    # BRASIL — Brasileirão
    # =====================================================================
    "Flamengo": ["CR Flamengo", "Mengão"],
    "Palmeiras": ["SE Palmeiras", "Verdão"],
    "Athletico Paranaense": ["Athletico PR", "CAP", "Furacão"],
    "Fluminense": ["Fluminense FC", "Tricolor", "Flu"],
    "Bahia": ["EC Bahia", "Tricolor de Aço"],
    "Cruzeiro": ["Cruzeiro EC", "Raposa"],
    "Coritiba": ["Coritiba FC", "Coxa"],
    "Atlético Mineiro": ["Atlético-MG", "Galo", "Atletico-MG"],
    "Red Bull Bragantino": ["Bragantino", "RB Bragantino", "Massa Bruta"],
    "São Paulo": ["Sao Paulo", "São Paulo FC", "Tricolor Paulista"],
    "Vitória": ["EC Vitória", "Leão", "Vitoria"],
    "Corinthians": ["SC Corinthians", "Timão"],
    "Santos": ["Santos FC", "Peixe"],
    "Botafogo": ["Botafogo FR", "Fogão"],
    "Grêmio": ["Gremio", "Grêmio FBPA", "Imortal"],
    "Mirassol": ["Mirassol FC", "Leão da Alta Araraquarense"],
    "Vasco da Gama": ["Vasco", "CR Vasco da Gama", "Gigante da Colina"],
    "Internacional": ["Inter de Porto Alegre", "SC Internacional", "Colorado"],
    "Remo": ["Clube do Remo", "Leão Azul"],
    "Chapecoense": ["Chape", "Verdão do Oeste"],

    # =====================================================================
    # URUGUAY — Primera División
    # =====================================================================
    "Liverpool Montevideo": ["Liverpool FC", "Liverpool", "Negro de la Cuchilla"],
    "Montevideo City Torque": ["Torque", "MCT"],
    "Cerro": ["CA Cerro", "El Cerro"],
    "Juventud": ["Juventud de Las Piedras", "JUV"],
    "Deportivo Maldonado": ["Maldonado", "El Depor"],
    "Racing Montevideo": ["Racing (Montevideo)", "Racing", "La Escuelita"],
    "Boston River": ["El Boston"],
    "Peñarol": ["Penarol", "CA Peñarol", "Manyas"],
    "Nacional Montevideo": ["Nacional", "Club Nacional", "Tricolor"],
    "Montevideo Wanderers": ["Wanderers", "Bohemios"],
    "Progreso": ["CA Progreso", "Gaucho"],
    "Cerro Largo": ["Cerro Largo FC", "Misión"],
    "Central Español": ["Central Español Fútbol Club", "Palermitano"],
    "Danubio": ["Danubio FC", "La Franja"],
    "Defensor Sporting": ["Defensor", "Tuerto"],
    "Albion FC": ["Albion"],

    # =====================================================================
    # CHILE — Primera División
    # =====================================================================
    "Colo-Colo": ["Colo Colo", "CSD Colo-Colo", "Eterno Campeón"],
    "Universidad Católica": ["UC", "Universidad Catolica", "Cruzados"],
    "Universidad de Chile": ["U de Chile", "La U", "Azul Azul"],
    "Palestino": ["CD Palestino", "Árabes"],
    "Everton": ["Everton CD", "Everton de Viña del Mar", "Ruleteros"],
    "Deportes Limache": ["Limache"],
    "Ñublense": ["Nublense", "Deportes Ñublense", "Diablos Rojos"],
    "Deportes Concepción": ["Concepción", "Deportes Concepcion", "León de Collao"],
    "La Serena": ["Deportes La Serena", "Papayeros"],
    "Coquimbo Unido": ["Coquimbo", "Piratas"],
    "O'Higgins": ["O'Higgins FC", "Capo de Provincia"],
    "Audax Italiano": ["Audax", "Tanos"],
    "Huachipato": ["Huachipato FC", "Acereros"],
    "Universidad de Concepción": ["U de Concepción", "Universidad de Concepcion", "Campanil"],
    "Cobresal": ["CD Cobresal", "Mineros"],
    "Unión La Calera": ["La Calera", "Union La Calera", "Cementeros"],

    # =====================================================================
    # ECUADOR — Serie A
    # =====================================================================
    "Independiente del Valle": ["Independiente DV", "IDV", "Rayados"],
    "Aucas": ["SD Aucas", "Orientales"],
    "Universidad Católica Quito": ["U. Católica", "Universidad Catolica Quito", "Chatoleí"],
    "Macará": ["Macara", "CSD Macará", "Celeste"],
    "LDU Quito": ["Liga de Quito", "Albos"],
    "Barcelona SC": ["Barcelona", "Barcelona de Guayaquil", "Ídolo del Ecuador"],
    "Libertad": ["Libertad FC", "Libertad de Loja"],
    "Leones": ["Leones FC"],
    "Emelec": ["CS Emelec", "Eléctricos"],
    "Mushuc Runa": ["Mushuc Runa SC", "Ponchitos"],
    "Guayaquil City": ["Guayaquil City FC", "Ciudadanos"],
    "Deportivo Cuenca": ["Cuenca", "Morlacos"],
    "Orense": ["Orense SC"],
    "Técnico Universitario": ["Tecnico Universitario", "Amarillos"],
    "Delfín": ["Delfin", "Delfín SC", "Cetáceos"],
    "Manta FC": ["Manta F.C.", "Manta", "Atuneros"],

    # =====================================================================
    # PARAGUAY — Primera División
    # =====================================================================
    "Libertad Asunción": ["Club Libertad", "Libertad", "Gumarelo"],
    "2 de Mayo": ["Club 2 de Mayo"],
    "Olimpia": ["Club Olimpia", "Decano"],
    "Sportivo Ameliano": ["Ameliano", "La Academia"],
    "Nacional Asunción": ["Nacional"],
    "Sportivo Trinidense": ["Trinidense", "El Triangular"],
    "Cerro Porteño": ["Cerro", "Ciclón"],
    "Guaraní": ["Club Guaraní", "Guarani", "Aurinegro"],
    "Sportivo Luqueño": ["Luqueño", "Sportivo Luqueno", "El Chanchón"],
    "Rubio Ñú": ["Rubio Ñu", "Rubio Nu", "El Sabalero"],
    "Deportivo Recoleta": ["Recoleta"],
    "Sportivo San Lorenzo": ["San Lorenzo", "El Santo"],

    # =====================================================================
    # PERÚ — Liga 1
    # =====================================================================
    "Deportivo Garcilaso": ["Garcilaso", "El Vendaval"],
    "Universitario": ["Universitario de Deportes", "La U", "Crema"],
    "Alianza Atlético": ["Alianza Atletico", "El Vendaval"],
    "Cusco FC": ["Cusco", "Los Dorados"],
    "Juan Pablo II": ["Juan Pablo II College", "JPII"],
    "Melgar": ["FBC Melgar", "El Dominó"],
    "Sport Boys": ["Boys", "La Misilera"],
    "Sporting Cristal": ["Cristal", "Los Celestes"],
    "Alianza Lima": ["Alianza", "Los Íntimos"],
    "Sport Huancayo": ["Huancayo", "El Rojo Matador"],
    "Atlético Grau": ["Grau", "Atletico Grau", "El Verdolaga"],
    "Comerciantes Unidos": ["Comerciantes", "Los Comerciantes"],
    "Cienciano": ["Cienciano del Cusco", "El Papá"],
    "Deportivo Moquegua": ["Moquegua"],
    "FC Cajamarca": ["Cajamarca"],
    "Los Chankas": ["Chankas"],
    "ADT": ["Asociación Deportiva Tarma"],
    "UTC": ["Universidad Técnica de Cajamarca"],

    # =====================================================================
    # INTERNACIONAL — UEFA (otros)
    # =====================================================================
    "Slavia Prague": ["Slavia Praga", "Slavia Praha", "SK Slavia Praha"],
    "Sparta Prague": ["Sparta Praga", "AC Sparta Praha", "Sparta"],
    "Viktoria Plzen": ["Viktoria", "FC Viktoria Plzeň", "Plzen"],
    "Slovan Bratislava": ["Slovan", "ŠK Slovan Bratislava"],
    "Sabah FK": ["Sabah"],
    "Ferencvaros": ["Ferencváros", "FTC"],
    "Red Star Belgrade": ["Estrella Roja", "Crvena Zvezda", "FK Crvena Zvezda"],
    "Dinamo Zagreb": ["Dinamo", "GNK Dinamo Zagreb"],
    "Hajduk Split": ["Hajduk", "HNK Hajduk Split"],
    "Hapoel Be'er": ["Hapoel Beer Sheva", "Hapoel Be'er Sheva", "Hapoel"],
    "Jagiellonia Bialystok": ["Jagiellonia", "Jagiellonia Białystok", "Jaga"],
    "Lech Poznan": ["Lech", "Lech Poznań", "Kolejorz"],
    "Levski Sofia": ["Levski", "PFC Levski Sofia"],
    "CSKA Sofia": ["CSKA", "PFC CSKA Sofia"],
    "Omonia Nicosia": ["Omonia", "AC Omonia"],
    "Pafos": ["Pafos FC"],
    "Kairat Almaty": ["Kairat", "FC Kairat"],
    "Ararat-Armenia": ["Ararat", "Ararat Armenia", "FC Ararat-Armenia"],
    "Iberia 1999": ["Iberia", "FC Iberia 1999"],
    "Riga FC": ["Riga"],
    "Kauno Zalgiris": ["Kauno Žalgiris", "FK Kauno Žalgiris"],
    "KuPS Kuopio": ["KuPS", "Kuopion Palloseura"],
    "Shamrock Rovers": ["Shamrock", "Shamrock Rovers FC"],
    "Lincoln Red Imps": ["Lincoln"],
    "Inter D'Escaldes": ["Inter Escaldes", "Inter Club d'Escaldes", "Inter"],
    "The New Saints": ["TNS", "The New Saints FC"],
    "Borac Banja Luka": ["Borac", "FK Borac Banja Luka"],
    "NK Celje": ["Celje", "NK Celje"],
    "Jablonec": ["FK Jablonec"],
    "Egnatia": ["KF Egnatia"],
    "CSU Craiova": ["Craiova", "CS Universitatea Craiova", "CSU Craiova"],
    "Torreense": ["SCU Torreense"],
    "Cercle Brugge": ["Cercle Brugge KSV", "Cercle"],
    "Kairat": ["FC Kairat"],
    "Panevėžys": ["FK Panevėžys", "Panevezys"],
    "Drita": ["FC Drita", "Drita"],
    "Milsami": ["FC Milsami", "Milsami Orhei"],
    "Noah": ["FC Noah", "Noah"],
    "Pyunik": ["FC Pyunik", "Pyunik"],
    "Zrinjski": ["HŠK Zrinjski Mostar", "Zrinjski Mostar"],
    "FCSB": ["FCSB", "Steaua București"],
    "Universitatea Craiova": ["U Craiova", "Universitatea Craiova"],

    # =====================================================================
    # INTERNACIONAL — CONMEBOL (otros)
    # =====================================================================
    "Bolívar": ["Bolivar", "Club Bolívar", "La Academia"],
    "Deportivo La Guaira": ["La Guaira", "Naranja"],
    "Always Ready": ["Club Always Ready", "El Millonario"],
    "UCV FC": ["UCV", "Universidad César Vallejo"],
    "Ceará": ["Ceara", "Ceará SC", "Vozão"],
    "Godoy Cruz": ["Godoy Cruz Antonio Tomba", "Tomba"],
    "Unión Española": ["Union Espanola", "Los Rojos"],
}


import unicodedata
import re

# ============================================================
# LIMPIEZA DE NOMBRES (para matching con APIs externas)
# ============================================================

# Prefijos comunes que se pueden eliminar
PREFIJOS_IGNORAR = [
    'fc', 'cf', 'sc', 'rc', 'cd', 'ca', 'ac', 'afc', 'sd', 'ud', 'sv',
    'vfl', 'vfb', 'tsg', 'bsc', 'sg', 'fk', 'sk', 'nk', 'hk', 'if', 'bk',
    'as', 'us', 'ss', 'ssc', 'sss', 'acf', 'sl', 'sport', 'sports',
]

# Sufijos comunes que se pueden eliminar
SUFIJOS_IGNORAR = [
    'fc', 'cf', 'sc', 'rc', 'cd', 'ca', 'ac', 'afc',
    'fc 1901', 'fc 1909', '1909', '1907', '1901', '1899', '1893',
    '1963', '1965', '65', '05', '04', '07', '96', '98', '99',
    'a.f.c.', 'f.c.', 's.c.', 'c.f.',
]


def _limpiar_nombre(nombre):
    """
    Limpia un nombre de equipo para facilitar el matching:
    - Quita tildes
    - Minúsculas
    - Quita puntuación
    - Quita prefijos y sufijos comunes
    - Normaliza espacios
    """
    if not nombre:
        return ''
    
    # 1. Quitar tildes
    nombre = unicodedata.normalize('NFD', nombre)
    nombre = ''.join(c for c in nombre if unicodedata.category(c) != 'Mn')
    
    # 2. Minúsculas
    nombre = nombre.lower()
    
    # 3. Quitar puntuación (excepto espacios y apóstrofes dentro de palabras)
    nombre = re.sub(r"[^\w\s']", ' ', nombre)
    nombre = re.sub(r"'", '', nombre)
    
    # 4. Normalizar espacios
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    return nombre


def _limpiar_para_match(nombre):
    """
    Versión más agresiva: quita prefijos y sufijos comunes.
    """
    nombre_limpio = _limpiar_nombre(nombre)
    tokens = nombre_limpio.split()
    
    # Quitar prefijos
    while tokens and tokens[0] in PREFIJOS_IGNORAR:
        tokens.pop(0)
    
    # Quitar sufijos
    while tokens and tokens[-1] in PREFIJOS_IGNORAR:
        tokens.pop()
    
    # Quitar números al final (ej: "1901", "1963")
    while tokens and re.match(r'^\d+$', tokens[-1]):
        tokens.pop()
    
    return ' '.join(tokens)


def normalizar_equipo(nombre):
    """
    Devuelve el nombre canónico de un equipo.
    Si no lo encuentra, intenta limpiar y volver a buscar.
    """
    if not nombre:
        return nombre

    nombre_limpio = nombre.strip()

    # ========== 1. ¿Es ya un nombre canónico? ==========
    if nombre_limpio in ALIASES_EQUIPOS:
        return nombre_limpio

    # ========== 2. Buscar en aliases (case-insensitive) ==========
    nombre_lower = nombre_limpio.lower()
    for canonico, aliases in ALIASES_EQUIPOS.items():
        if nombre_lower in [a.lower() for a in aliases]:
            return canonico
        if nombre_lower == canonico.lower():
            return canonico

    # ========== 3. NUEVO: limpiar y buscar de nuevo ==========
    nombre_limpio_agresivo = _limpiar_para_match(nombre_limpio)
    nombre_limpio_simple = _limpiar_nombre(nombre_limpio)
    
    # 3a. Buscar el nombre limpio agresivo en aliases
    for canonico, aliases in ALIASES_EQUIPOS.items():
        canonico_limpio = _limpiar_para_match(canonico)
        
        # Match exacto con el canónico limpio
        if nombre_limpio_agresivo == canonico_limpio:
            return canonico
        
        # Match contra aliases limpios
        for alias in aliases:
            alias_limpio = _limpiar_para_match(alias)
            if nombre_limpio_agresivo == alias_limpio:
                return canonico
    
    # 3b. Buscar el nombre limpio simple (menos agresivo)
    for canonico, aliases in ALIASES_EQUIPOS.items():
        canonico_limpio = _limpiar_nombre(canonico)
        
        if nombre_limpio_simple == canonico_limpio:
            return canonico
        
        for alias in aliases:
            alias_limpio = _limpiar_nombre(alias)
            if nombre_limpio_simple == alias_limpio:
                return canonico
    
    # 3c. Match por inclusión (último recurso)
    # Si el nombre limpio está contenido en un canónico o viceversa
    if len(nombre_limpio_agresivo) >= 4:
        for canonico, aliases in ALIASES_EQUIPOS.items():
            canonico_limpio = _limpiar_para_match(canonico)
            
            # Solo si ambos tienen >=4 caracteres (evitar falsos positivos)
            if len(canonico_limpio) >= 4:
                # ¿El nombre de la API está dentro del canónico?
                if nombre_limpio_agresivo in canonico_limpio or canonico_limpio in nombre_limpio_agresivo:
                    return canonico

    # ========== 4. No encontrado → devolver tal cual ==========
    return nombre_limpio


def obtener_aliases(equipo_canonico):
    """Devuelve todos los aliases de un equipo canónico"""
    return ALIASES_EQUIPOS.get(equipo_canonico, [])


def es_mismo_equipo(nombre1, nombre2):
    """Determina si dos nombres se refieren al mismo equipo"""
    return normalizar_equipo(nombre1) == normalizar_equipo(nombre2)
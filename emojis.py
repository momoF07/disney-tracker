# emojis.py

# Structure organisée par Parc > Land > Attraction: Emoji
PARKS_DATA = {
    "Disneyland Park": {
        "MAINSTREET": {
            "Disneyland Railroad Main Street Station": "🚉",
            "Main Street Vehicles": "🚔",
        },
        "FRONTIERLAND": {
            "Big Thunder Mountain": "⛰️",
            "Phantom Manor": "👻",
            "Thunder Mesa Riverboat Landing": "🚢",
            "Rustler Roundup Shootin' Gallery": "🎯",
            "Disneyland Railroad Frontierland Depot": "🚂",
            "Frontierland Playground": "🌵",
        },
        "ADVENTURELAND": {
            "Pirates of the Caribbean": "⚔️",
            "Indiana Jones™ and the Temple of Peril": "🤠",
            "La Cabane des Robinson": "🌳",
            "Adventure Isle": "🏝️",
            "Pirate Galleon": "🏴‍C️",
            "Pirates' Beach": "🏖️",
            "Le Passage Enchanté d'Aladdin": "🧞",
        },
        "FANTASYLAND": {
            "Peter Pan's Flight": "🧚",
            "it's a small world": "🌍",
            "Dumbo the Flying Elephant": "🐘",
            "Mad Hatter's Tea Cups": "☕",
            "Le Carrousel de Lancelot": "🎠",
            "Blanche-Neige et les Sept Nains®": "🍎",
            "Les Voyages de Pinocchio": "🤥",
            "Alice's Curious Labyrinth": "🃏",
            "Casey Jr. – le Petit Train du Cirque": "🚂",
            "Le Pays des Contes de Fées, presented by Vittel": "📖",
            "La Tanière du Dragon": "🐉",
        },
        "DISCOVERYLAND": {
            "Star Wars Hyperspace Mountain": "🚀",
            "Star Tours: The Adventures Continue*": "🌌",
            "Buzz Lightyear Laser Blast": "🔫",
            "Orbitron®": "🛰️",
            "Autopia, presented by Avis": "🚗",
            "Les Mystères du Nautilus": "🌀",
        }
    },
    "Disney Adventure World": {
        "AVENGERS CAMPUS": {
            "Avengers Assemble: Flight Force": "🛡️",
            "Spider-Man W.E.B. Adventure": "🕷️",
        },
        "WORLD OF PIXAR": {
            "Ratatouille : L’Aventure Totalement Toquée de Rémy​": "🐭",
            "RC Racer": "🏎️",
            "Slinky® Dog Zigzag Spin": "🐶",
            "Toy Soldiers Parachute Drop": "🪂",
            "Cars ROAD TRIP": "🌵",
        },
        "PRODUCTION 3": {
            "Les Tapis Volants - Flying Carpets Over Agrabah®": "🧞",
            "Crush's Coaster": "🐢",
            "The Twilight Zone Tower of Terror": "🏨",
            "Cars Quatre Roues Rallye": "🏁",
        },
        "WORLD OF FROZEN": {
            "Entry to World of Frozen": "❄️",
            "Frozen Ever After": "⛄",
        },
        "ADVENTURE WAY": {
            "Raiponce Tangled Spin": "🍳",
        }
    }
}

# --- FONCTIONS UTILITAIRES ---

def get_emoji(name):
    """Parcourt la structure pour trouver l'émoji correspondant au nom"""
    if "Test" in name:
        return "🤖"
    for park, lands in PARKS_DATA.items():
        for land, attractions in lands.items():
            for attr_name, emoji in attractions.items():
                if attr_name.lower() in name.lower():
                    return emoji
    return "🎡"

def get_rides_by_zone(zone_code, all_rides_list):
    """
    Filtre les attractions selon les raccourcis parcs ou les LANDS (avec alias).
    Supporte maintenant les codes numériques 101 et 102 pour les tests.
    """
    zone_code = zone_code.upper().replace("*", "").strip()
    targets = []

    # --- LOGIQUE TEST (Réparée pour 101, 102 et TEST) ---
    if zone_code in ["101", "102", "TEST"]:
        return [r for r in all_rides_list if "test" in r.lower()]

    # --- LOGIQUE ALL ---
    if zone_code == "ALL":
        return all_rides_list
        
    # --- DICTIONNAIRE D'ALIAS ---
    ALIAS_MAP = {
        "MS": "MAINSTREET",
        "MAINSTREET": "MAINSTREET",
        "FRONTIER": "FRONTIERLAND",
        "FRONTIERLAND": "FRONTIERLAND",
        "ADVENTURE": "ADVENTURELAND",
        "ADVENTURELAND": "ADVENTURELAND",
        "FANTASY": "FANTASYLAND",
        "FANTASYLAND": "FANTASYLAND",
        "DISCO": "DISCOVERYLAND",
        "DISCOVERYLAND": "DISCOVERYLAND",
        "AVENGERS": "AVENGERS CAMPUS",
        "CAMPUS": "AVENGERS CAMPUS",
        "AVENGERS-CAMPUS": "AVENGERS CAMPUS",
        "PIXAR": "WORLD OF PIXAR",
        "WORLD-OF-PIXAR": "WORLD OF PIXAR",
        "PROD4": "WORLD OF PIXAR",
        "PRODUCTION4": "WORLD OF PIXAR",
        "PROD3": "PRODUCTION 3",
        "PRODUCTION 3": "PRODUCTION 3",
        "WOF": "WORLD OF FROZEN",
        "FROZEN": "WORLD OF FROZEN",
        "WORLD-OF-FROZEN": "WORLD OF FROZEN",
        "WAY": "ADVENTURE WAY",
        "ADVENTURE-WAY": "ADVENTURE WAY"
    }

    # --- GESTION PARCS ---
    if zone_code == "DLP":
        for land in PARKS_DATA["Disneyland Park"].values():
            targets.extend(land.keys())
    elif zone_code in ["DAW", "WDS", "STUDIOS"]:
        for land in PARKS_DATA["Disney Adventure World"].values():
            targets.extend(land.keys())

    # --- GESTION LANDS ---
    else:
        target_land_name = ALIAS_MAP.get(zone_code, zone_code)
        for park, lands in PARKS_DATA.items():
            for land_name, attractions in lands.items():
                if target_land_name in land_name.upper():
                    targets.extend(attractions.keys())

    # Filtrage final
    matched = []
    for ride in all_rides_list:
        if any(target.lower() in ride.lower() for target in targets):
            matched.append(ride)
    
    return matched

# emojis.py

# Structure organisée par Parc > Land > Attraction: Emoji
PARKS_DATA = {
    "Disneyland Park": {
        "Main Street": {
            "Disneyland Railroad Main Street Station": "🚉",
            "Main Street Vehicles": "🚔",
        },
        "Frontierland": {
            "Big Thunder Mountain": "⛰️",
            "Phantom Manor": "👻",
            "Thunder Mesa Riverboat Landing": "🚢",
            "Rustler Roundup Shootin' Gallery": "🎯",
            "Disneyland Railroad Frontierland Depot": "🚂",
            "Frontierland Playground": "🌵",
        },
        "Adventureland": {
            "Pirates of the Caribbean": "⚔️",
            "Indiana Jones™ and the Temple of Peril": "🤠",
            "La Cabane des Robinson": "🌳",
            "Adventure Isle": "🏝️",
            "Pirate Galleon": "🏴‍☠️",
            "Pirates' Beach": "🏖️",
            "Le Passage Enchanté d'Aladdin": "🧞",
        },
        "Fantasyland": {
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
            "Raiponce Tangled Spin": "🍳",
        },
        "Discoveryland": {
            "Star Wars Hyperspace Mountain": "🚀",
            "Star Tours: The Adventures Continue*": "🌌",
            "Buzz Lightyear Laser Blast": "🔫",
            "Orbitron®": "🛰️",
            "Autopia, presented by Avis": "🚗",
            "Les Mystères du Nautilus": "🌀",
        }
    },
    "Walt Disney Studios": {
        "Avengers Campus": {
            "Avengers Assemble: Flight Force": "🛡️",
            "Spider-Man W.E.B. Adventure": "🕷️",
        },
        "Worlds of Pixar": {
            "Crush's Coaster": "🐢",
            "Ratatouille : L’Aventure Totalement Toquée de Rémy​": "🐭",
            "RC Racer": "🏎️",
            "Slinky® Dog Zigzag Spin": "🐶",
            "Toy Soldiers Parachute Drop": "🪂",
            "Cars Quatre Roues Rallye": "🏁",
            "Cars ROAD TRIP": "🌵",
        },
        "Production Courtyard": {
            "The Twilight Zone Tower of Terror": "🏨",
        },
        "World of Frozen": {
            "Entry to World of Frozen": "❄️",
            "Frozen Ever After": "⛄",
        }
    }
}

# --- FONCTIONS UTILITAIRES ---

def get_emoji(name):
    """Parcourt la structure pour trouver l'émoji correspondant au nom"""
    for park, lands in PARKS_DATA.items():
        for land, attractions in lands.items():
            for attr_name, emoji in attractions.items():
                if attr_name.lower() in name.lower():
                    return emoji
    return "🎡"

def get_rides_by_zone(zone_code, all_rides_list):
    """
    Filtre les attractions selon les raccourcis *DLP, *DAW ou les LANDS.
    """
    zone_code = zone_code.upper().replace("*", "")
    targets = []

    # Raccourcis de Parcs complets
    if zone_code == "DLP":
        for land in PARKS_DATA["Disneyland Park"].values():
            targets.extend(land.keys())
    elif zone_code in ["DAW", "WDS"]:
        for land in PARKS_DATA["Walt Disney Studios"].values():
            targets.extend(land.keys())
    
    # Raccourcis par Lands spécifiques
    else:
        for park, lands in PARKS_DATA.items():
            for land_name, attractions in lands.items():
                # Si le raccourci correspond au nom du land (ex: FANTASY dans FANTASYLAND)
                if zone_code in land_name.upper():
                    targets.extend(attractions.keys())

    # Filtrage final : on ne garde que ce qui existe réellement dans les logs actuels
    matched = []
    for ride in all_rides_list:
        if any(target.lower() in ride.lower() for target in targets):
            matched.append(ride)
    
    return matched

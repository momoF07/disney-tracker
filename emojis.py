# emojis.py

# Dictionnaire principal pour les émojis
EMOJI_MAP = {
    # --- Disneyland Park ---
    "it's a small world": "🌍",
    "Adventure Isle": "🏝️",
    "Alice's Curious Labyrinth": "🃏",
    "Autopia, presented by Avis": "🚗",
    "Big Thunder Mountain": "⛰️",
    "Blanche-Neige et les Sept Nains®": "🍎",
    "Buzz Lightyear Laser Blast": "🔫",
    "Casey Jr. – le Petit Train du Cirque": "🚂",
    "Disneyland Railroad Frontierland Depot": "🚂",
    "Disneyland Railroad Main Street Station": "🚉",
    "Dumbo the Flying Elephant": "🐘",
    "Frontierland Playground": "🌵",
    "Indiana Jones™ and the Temple of Peril": "🤠",
    "La Cabane des Robinson": "🌳",
    "La Tanière du Dragon": "🐉",
    "Le Carrousel de Lancelot": "🎠",
    "Le Passage Enchanté d'Aladdin": "🧞",
    "Le Pays des Contes de Fées, presented by Vittel": "📖",
    "Les Mystères du Nautilus": "🌀",
    "Les Voyages de Pinocchio": "🤥",
    "Mad Hatter's Tea Cups": "☕",
    "Main Street Vehicles": "🚔",
    "Orbitron®": "🛰️",
    "Peter Pan's Flight": "🧚",
    "Phantom Manor": "👻",
    "Pirate Galleon": "🏴‍☠️",
    "Pirates of the Caribbean": "⚔️",
    "Pirates' Beach": "🏖️",
    "Raiponce Tangled Spin": "🍳",
    "Rustler Roundup Shootin' Gallery": "🎯",
    "Star Tours: The Adventures Continue*": "🌌",
    "Star Wars Hyperspace Mountain": "🚀",
    "Thunder Mesa Riverboat Landing": "🚢",

    # --- Walt Disney Studios ---
    "Avengers Assemble: Flight Force": "🛡️",
    "Cars Quatre Roues Rallye": "🏁",
    "Cars ROAD TRIP": "🌵",
    "Crush's Coaster": "🐢",
    "Les Tapis Volants - Flying Carpets Over Agrabah®": "🧞",
    "RC Racer": "🏎️",
    "Ratatouille : L’Aventure Totalement Toquée de Rémy​": "🐭",
    "Slinky® Dog Zigzag Spin": "🐶",
    "Spider-Man W.E.B. Adventure": "🕷️",
    "The Twilight Zone Tower of Terror": "🏨",
    "Toy Soldiers Parachute Drop": "🪂",
    "Entry to World of Frozen": "❄️",
    "Frozen Ever After": "⛄"
}

# --- LOGIQUE DE CLASSEMENT PAR PARC ---
# Ce dictionnaire sert pour tes recherches *DLP et *DAW
ZONES = {
    "DLP": [
        "it's a small world", "Adventure Isle", "Alice's Curious Labyrinth", 
        "Autopia", "Big Thunder Mountain", "Blanche-Neige", "Buzz Lightyear", 
        "Casey Jr", "Disneyland Railroad", "Dumbo", "Frontierland", "Indiana Jones", 
        "Cabane des Robinson", "Tanière du Dragon", "Carrousel de Lancelot", 
        "Passage Enchanté d'Aladdin", "Pays des Contes de Fées", "Mystères du Nautilus", 
        "Pinocchio", "Mad Hatter", "Main Street Vehicles", "Orbitron", "Peter Pan", 
        "Phantom Manor", "Pirate Galleon", "Pirates of the Caribbean", "Pirates' Beach", 
        "Raiponce", "Rustler Roundup", "Star Tours", "Star Wars", "Thunder Mesa"
    ],
    "DAW": [
        "Avengers", "Cars", "Crush's Coaster", "Tapis Volants", "RC Racer", 
        "Ratatouille", "Slinky", "Spider-Man", "Tower of Terror", 
        "Toy Soldiers", "Frozen"
    ]
}

def get_emoji(name):
    for ride, emoji in EMOJI_MAP.items():
        if ride.lower() in name.lower():
            return emoji
    return "🎡"

def get_rides_by_zone(zone_code, all_rides_list):
    """
    Filtre une liste d'attractions selon le code zone (*DLP ou *DAW)
    """
    if zone_code not in ZONES:
        return []
    
    keywords = ZONES[zone_code]
    matched = []
    
    for ride in all_rides_list:
        if any(key.lower() in ride.lower() for key in keywords):
            matched.append(ride)
    return matched

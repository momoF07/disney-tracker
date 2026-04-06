from datetime import time

# Dictionnaire des attractions avec fermeture anticipée
# Format : "Nom exact de l'attraction": time(heure, minute)
ANTICIPATED_CLOSINGS = {
    "Le Passage Enchanté d'Aladdin": time(22, 15),
    "Pirates' Beach": time(22, 15),
    "Rustler Roundup Shootin' Gallery": time(21, 35),
    "Cars ROAD TRIP": time(21, 40),
    "La Tanière du Dragon": time(20, 55),
    "Alice's Curious Labyrinth": time(20, 0),
    "Casey Jr. – le Petit Train du Cirque": time(20, 0),
    "Disneyland Railroad Frontierland Depot": time(19, 45),
    "Disneyland Railroad Main Street Station": time(19, 45),
    "Frontierland Playground": time(19, 55),
    "Le Pays des Contes de Fées, presented by Vittel": time(20, 0),
    "Discoveryland Theater": time(17, 30),
    "Thunder Mesa Riverboat Landing": time(17, 0),
    
}

# Liste des attractions qui ferment TOUJOURS 1h05 avant le show nocturne (Fantasyland)
# On pourra calculer cela dynamiquement dans l'app
FANTASYLAND_EARLY_CLOSE = [
    "Dumbo the Flying Elephant",
    "Mad Hatter's Tea Cups",
    "Le Carrousel de Lancelot",
    "Blanche-Neige et les Sept Nains®",
    "Les Voyages de Pinocchio",
]

EMT_EARLY_OPEN = [
    "Big Thunder Mountain",
    "Peter Pan's Flight", 
    "Dumbo The Flying Elephant", 
    "HyperSpace Mountain", 
    "Buzz Lightyear Laserblast",
    "Main Street Vehicles",
    "Crush's Coaster",
    "WEB", 
    "Flight Force",
    "Tour de la Terreur", 
    "Slinky Dog", 
    "Ratatouille",
    "Frozen Ever After",
    "Raiponce Tangled Spin",
]

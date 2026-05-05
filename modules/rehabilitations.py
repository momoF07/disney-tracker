from datetime import date

# Format : "Nom exact": {"debut": date(Y,M,D), "fin": date(Y,M,D), "msg": "..."}
REHAB_LIST = {
    "Blanche-Neige et les Sept Nains®": {
        "debut": date(2026, 3, 10),
        "fin": date(2026, 5, 29), 
        "msg": "Réouverture prévue le 30 mai"
    },
    "RC Racer": {
        "debut": date(2026, 5, 18),
        "fin": date(2026, 5, 22),
        "msg": "Réouverture prévue le 23 mai"
    },
    "Entry to World of Frozen": {
        "msg": "Fermeture définitive, en attente de la supression de l'API."
    },
    "Pirate Galleon": {
        "msg": "Fermeture jusqu'à nouvel ordre."
    }
}
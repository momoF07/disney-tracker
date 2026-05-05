# bot/modules_bot.py
# Pont entre le bot et les modules existants du projet
# Copie ou importe les constantes nécessaires

from datetime import time
from modules.rehabilitations import REHAB_LIST
from modules.emojis import PARKS_DATA, RIDES_DLP, RIDES_DAW
from modules.special_hours import (
    ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN,
    FANTASYLAND_EARLY_CLOSE, SPECIAL_OPENING_HOURS
)
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
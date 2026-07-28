APP_TITLE = "Centro de Inteligencia Operacional KOA"
APP_SUBTITLE = "Estudios de tiempos, puntualidad, paraderos y simulación operacional"
APP_VERSION = "5.0.2"
DEFAULT_WORKBOOK = "Dinamica_de_paraderos_KOA_ES.xlsx"
DEFAULT_SHEET = "seguimiento_h_op"

MORNING_STOPS = ["OXXO HÉROES"]
AFTERNOON_STOPS = ["VIRREY", "HÉROES", "POLO"]
ALL_STOPS = MORNING_STOPS + AFTERNOON_STOPS
STOPS = AFTERNOON_STOPS
ROUTES = ["R1", "R2", "R3"]
SHIFTS = ["MANANA", "TARDE"]

# Regla operacional de puntualidad
MORNING_TOLERANCE_MIN = 5
AFTERNOON_TOLERANCE_MIN = 5
MAX_VALID_DEVIATION_MIN = 180
MIN_VALID_TRIP_MIN = 1
MAX_VALID_TRIP_MIN = 240

COLORS = {
    "primary": "#123D76",
    "secondary": "#1D5DA7",
    "light": "#EEF3F9",
    "danger": "#B3261E",
    "warning": "#B26A00",
    "success": "#137333",
    "gray": "#6B7280",
}

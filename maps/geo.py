from __future__ import annotations
import math
import pandas as pd

DEFAULT_KOA = {"name": "KOA", "lat": 4.6761, "lon": -74.0571}
CURRENT_STOPS = [
    {"name": "OXXO HÉROES", "type": "Paradero actual", "lat": 4.6693, "lon": -74.0597},
    {"name": "VIRREY", "type": "Paradero actual", "lat": 4.6758, "lon": -74.0557},
    {"name": "HÉROES", "type": "Paradero actual", "lat": 4.6690, "lon": -74.0594},
    {"name": "POLO", "type": "Paradero actual", "lat": 4.6657, "lon": -74.0670},
]
TRANSMILENIO_STATIONS = [
    {"name": "Virrey", "type": "Estación TransMilenio", "lat": 4.6745, "lon": -74.0564},
    {"name": "Calle 100", "type": "Estación TransMilenio", "lat": 4.6841, "lon": -74.0528},
    {"name": "Calle 85", "type": "Estación TransMilenio", "lat": 4.6709, "lon": -74.0581},
    {"name": "Héroes", "type": "Estación TransMilenio", "lat": 4.6687, "lon": -74.0601},
    {"name": "Polo", "type": "Estación TransMilenio", "lat": 4.6615, "lon": -74.0666},
]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def candidates_table(koa_lat: float, koa_lon: float, walking_speed_m_min: float = 75) -> pd.DataFrame:
    rows = []
    for point in TRANSMILENIO_STATIONS:
        distance = haversine_m(koa_lat, koa_lon, point["lat"], point["lon"])
        rows.append({
            "Alternativa": point["name"], "Tipo": point["type"],
            "Distancia lineal a KOA (m)": round(distance),
            "Caminata estimada (min)": max(1, round(distance / walking_speed_m_min)),
            "Latitud": point["lat"], "Longitud": point["lon"],
        })
    return pd.DataFrame(rows).sort_values("Distancia lineal a KOA (m)").reset_index(drop=True)

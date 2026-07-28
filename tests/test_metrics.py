import pandas as pd
from core.loader import load_workbook
from core.metrics import kpis, stop_frequency


def test_punctuality_rules(tmp_path):
    # Regla probada directamente sobre un dataframe compatible.
    df = pd.DataFrame({
        "jornada": ["MANANA", "MANANA", "TARDE", "TARDE"],
        "desv_min": [0, 1, 5, 6],
        "clasificacion_puntualidad": ["PUNTUAL", "RETRASADA", "PUNTUAL", "RETRASADA"],
        "puntualidad_oficial": [True, False, True, False],
        "puntual_pm5": [True, True, True, False],
        "anticipada": [False]*4, "retraso_oficial": [False, True, False, True],
        "estado_operativo": ["EFECTIVO"]*4, "trayecto": [20,20,20,20], "espera": [0]*4,
        "fecha": pd.to_datetime(["2026-01-01"]*4), "usuarios": [1]*4, "recorrido": ["R1"]*4,
    })
    result = kpis(df)
    assert result["puntualidad_manana"] == 0.5
    assert result["puntualidad_tarde"] == 0.5
    assert result["puntualidad_general"] == 0.5


def test_official_stops_from_default_workbook():
    df = load_workbook("Dinamica_de_paraderos_KOA_ES.xlsx")
    stops = stop_frequency(df)
    assert set(stops["paradero"]) == {"OXXO HÉROES", "VIRREY", "HÉROES", "POLO"}
    heroes = stops.loc[stops["paradero"] == "HÉROES", "usos_registrados"].iloc[0]
    assert heroes < 10  # No debe contar OXXO HÉROES como HÉROES de la tarde.

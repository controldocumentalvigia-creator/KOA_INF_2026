from __future__ import annotations
import numpy as np
import pandas as pd
from config import (
    DEFAULT_SHEET, ALL_STOPS, MAX_VALID_DEVIATION_MIN,
    MIN_VALID_TRIP_MIN, MAX_VALID_TRIP_MIN,
    MORNING_TOLERANCE_MIN, AFTERNOON_TOLERANCE_MIN,
)
from core.utils import norm, to_minutes, canonical_stops, stop_slug

REQUIRED_COLUMNS = [
    "DIA DEL SERVICIO", "RECORRIDO", "JORNADA", "USUARIOS", "PARADAS",
    "HORARIO-P1-REAL DE INICIO", "Hora de inicio R1P1",
    "Hora de llegada a KOA  P2", "Tiempo  de trayecto ida -regreso",
    "tiempo de espera vehiculo",
]


def _find_column(columns, expected):
    for column in columns:
        if norm(column) == norm(expected):
            return column
    raise KeyError(f"No se encontró la columna requerida: {expected}")


def _date_series(raw: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(raw, errors="coerce")
    excel = pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")
    parsed = pd.to_datetime(raw, dayfirst=True, errors="coerce")
    return excel.fillna(parsed).dt.normalize()


def _punctuality_class(row) -> str:
    dev = row["desv_min"]
    shift = row["jornada"]
    if pd.isna(dev):
        return "SIN DATO"
    if dev < 0:
        return "ANTICIPADA"
    if shift == "MANANA":
        return "PUNTUAL" if dev <= MORNING_TOLERANCE_MIN else "RETRASADA"
    if shift == "TARDE":
        return "PUNTUAL" if dev <= AFTERNOON_TOLERANCE_MIN else "RETRASADA"
    return "SIN CLASIFICAR"


def load_workbook(source, sheet_name=DEFAULT_SHEET) -> pd.DataFrame:
    raw = pd.read_excel(source, sheet_name=sheet_name, engine="openpyxl")
    raw.columns = [str(c).strip() for c in raw.columns]
    mapping = {name: _find_column(raw.columns, name) for name in REQUIRED_COLUMNS}

    out = pd.DataFrame(index=raw.index)
    out["fecha"] = _date_series(raw[mapping["DIA DEL SERVICIO"]])
    out["recorrido"] = raw[mapping["RECORRIDO"]].map(norm)
    out["jornada"] = raw[mapping["JORNADA"]].map(norm).replace({"MAÑANA": "MANANA"})
    out["usuarios"] = pd.to_numeric(raw[mapping["USUARIOS"]], errors="coerce").fillna(0).clip(lower=0)
    out["paradas"] = raw[mapping["PARADAS"]].fillna("").astype(str)
    out["paradas_n"] = out["paradas"].map(norm)
    out["combinacion_paradas"] = [canonical_stops(v, j) for v, j in zip(out["paradas"], out["jornada"])]

    for target, source_name in {
        "prog": "HORARIO-P1-REAL DE INICIO",
        "inicio": "Hora de inicio R1P1",
        "llegada": "Hora de llegada a KOA  P2",
        "trayecto": "Tiempo  de trayecto ida -regreso",
        "espera": "tiempo de espera vehiculo",
    }.items():
        out[target] = to_minutes(raw[mapping[source_name]])

    deviation = out["inicio"] - out["prog"]
    out["desv_min"] = np.where(deviation > 720, deviation - 1440, np.where(deviation < -720, deviation + 1440, deviation))
    out.loc[out["desv_min"].abs() > MAX_VALID_DEVIATION_MIN, "desv_min"] = np.nan
    out.loc[~out["trayecto"].between(MIN_VALID_TRIP_MIN, MAX_VALID_TRIP_MIN, inclusive="both"), "trayecto"] = np.nan

    out["clasificacion_puntualidad"] = out.apply(_punctuality_class, axis=1)
    out["puntualidad_oficial"] = out["clasificacion_puntualidad"].eq("PUNTUAL")
    out["anticipada"] = out["clasificacion_puntualidad"].eq("ANTICIPADA")
    out["retraso_oficial"] = out["clasificacion_puntualidad"].eq("RETRASADA")

    # Compatibilidad con módulos V3 sin alterar la regla oficial.
    out["puntual_0_5"] = out["puntualidad_oficial"]
    out["puntual_pm5"] = out["desv_min"].abs().le(5)
    out["retraso_mayor_5"] = out["retraso_oficial"]

    def operational_status(row):
        combo, users = row["combinacion_paradas"], row["usuarios"]
        if combo == "NO EJECUTADO": return "NO EJECUTADO"
        if combo == "VALIDAR": return "VALIDAR"
        if combo == "NO USUARIOS": return "SIN USUARIOS"
        if combo == "SIN REGISTRO": return "SIN REGISTRO PARADAS"
        if combo not in {"OTRO", "SIN REGISTRO"} and users > 0: return "EFECTIVO"
        if combo not in {"OTRO", "SIN REGISTRO"} and users <= 0: return "PARADA REGISTRADA SIN USUARIOS"
        return "OTRO"

    out["estado_operativo"] = out.apply(operational_status, axis=1)
    for stop in ALL_STOPS:
        slug = stop_slug(stop)
        normalized = norm(stop)
        def uses_stop(row):
            combo_parts = {norm(part) for part in str(row["combinacion_paradas"]).split(" + ")}
            if stop == "OXXO HÉROES":
                return int(row["jornada"] == "MANANA" and norm(row["combinacion_paradas"]) == normalized)
            return int(row["jornada"] == "TARDE" and normalized in combo_parts)
        out[f"usa_{slug}"] = out.apply(uses_stop, axis=1)

    out["mes"] = out["fecha"].dt.to_period("M").astype(str)
    out["numero_semana_mes"] = ((out["fecha"].dt.day - 1) // 7 + 1).astype("Int64")
    out["semana_mes"] = out["numero_semana_mes"].map(lambda v: f"Semana {int(v)}" if pd.notna(v) else "SIN FECHA")
    out["mes_semana"] = out["mes"] + " | " + out["semana_mes"]
    out["dia_semana"] = out["fecha"].dt.day_name(locale=None)
    out["dia"] = out["fecha"].dt.strftime("%d/%m/%Y")
    return out.reset_index(drop=True)

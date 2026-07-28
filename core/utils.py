from __future__ import annotations
import re
import unicodedata
import numpy as np
import pandas as pd


def norm(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text.upper().strip())


def to_minutes(series: pd.Series) -> pd.Series:
    def convert(value):
        if pd.isna(value):
            return np.nan
        if isinstance(value, pd.Timedelta):
            return value.total_seconds() / 60
        if hasattr(value, "hour"):
            return value.hour * 60 + value.minute + getattr(value, "second", 0) / 60
        try:
            number = float(value)
            return number * 1440 if abs(number) <= 2 else number
        except (TypeError, ValueError):
            parts = str(value).strip().split(":")
            if len(parts) >= 2:
                try:
                    return float(parts[0]) * 60 + float(parts[1]) + (float(parts[2]) / 60 if len(parts) > 2 else 0)
                except (TypeError, ValueError):
                    return np.nan
            return np.nan
    return series.map(convert)


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else np.nan


def stop_slug(stop: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm(stop).lower()).strip("_")


def canonical_stops(value, journey: str = "") -> str:
    """Normaliza exclusivamente la columna PARADAS según la jornada."""
    text = norm(value)
    shift = norm(journey)
    if not text:
        return "SIN REGISTRO"
    if "NO SALIERON" in text:
        return "NO USUARIOS"
    if "NO SE ALCANZO" in text:
        return "NO EJECUTADO"
    if "VALIDAR" in text:
        return "VALIDAR"

    if shift == "MANANA":
        # OXXO HÉROES es un único punto operacional, aunque venga escrito sin espacio.
        if "OXXO" in text or "HEROES" in text:
            return "OXXO HÉROES"
        return "OTRO"

    found = [stop for stop in ["VIRREY", "HÉROES", "POLO"] if norm(stop) in text]
    return " + ".join(found) if found else "OTRO"

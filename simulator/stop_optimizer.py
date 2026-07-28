from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from config import AFTERNOON_STOPS
from core.metrics import effective_records
from core.utils import norm


def rank_stop_combinations(df: pd.DataFrame, max_stops: int = 3) -> pd.DataFrame:
    source = effective_records(df[df["jornada"] == "TARDE"])
    if source.empty:
        return pd.DataFrame()
    rows = []
    baseline_time = source["trayecto"].mean()
    total_users = source["usuarios"].sum()
    for size in range(1, min(max_stops, len(AFTERNOON_STOPS)) + 1):
        for combo in itertools.combinations(AFTERNOON_STOPS, size):
            mask = source["combinacion_paradas"].map(lambda x: any(norm(s) in norm(x) for s in combo))
            covered = source[mask]
            users = covered["usuarios"].sum()
            coverage = users / total_users if total_users else np.nan
            time = covered["trayecto"].mean() if len(covered) else np.nan
            saving = baseline_time - time if pd.notna(time) else np.nan
            score = (0 if pd.isna(coverage) else coverage * 70) + (0 if pd.isna(saving) else max(saving, 0) * 3) - size * 2
            rows.append({"combinación": " + ".join(combo), "paraderos": size, "recorridos_evidencia": len(covered), "usuarios_cubiertos": int(users), "cobertura": coverage, "tiempo_promedio_evidencia": time, "ahorro_estimado_min": saving, "puntaje": score})
    return pd.DataFrame(rows).sort_values(["puntaje", "cobertura"], ascending=False).reset_index(drop=True)

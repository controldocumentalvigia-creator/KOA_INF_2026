from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from config import ALL_STOPS, MORNING_STOPS, AFTERNOON_STOPS
from core.utils import stop_slug


def selected_label(df):
    journeys = sorted(df["jornada"].dropna().astype(str).unique())
    if not journeys: return "periodo filtrado"
    if len(journeys) == 1: return f"jornada {journeys[0].lower()}"
    return "jornadas seleccionadas"


def active_stops(df):
    journeys = set(df["jornada"].dropna().astype(str).unique())
    if journeys == {"MANANA"}: return MORNING_STOPS
    if journeys == {"TARDE"}: return AFTERNOON_STOPS
    return ALL_STOPS


def effective_records(df):
    return df[df["estado_operativo"] == "EFECTIVO"].copy()


def _punctual_valid(df):
    return df[df["desv_min"].notna() & df["clasificacion_puntualidad"].isin(["ANTICIPADA", "PUNTUAL", "RETRASADA"])].copy()


def _pct(valid, condition):
    return float(condition.mean()) if len(valid) else np.nan


def kpis(df):
    effective = effective_records(df)
    valid = _punctual_valid(df)
    morning = valid[valid["jornada"] == "MANANA"]
    afternoon = valid[valid["jornada"] == "TARDE"]
    times = effective["trayecto"].dropna()
    return {
        "registros": len(df),
        "registros_validos": len(valid),
        "dias": int(df["fecha"].nunique()),
        "usuarios": int(df["usuarios"].sum()),
        "recorridos": int(df["recorrido"].notna().sum()),
        "puntualidad_general": _pct(valid, valid["puntualidad_oficial"]),
        "puntualidad_manana": _pct(morning, morning["puntualidad_oficial"]),
        "puntualidad_tarde": _pct(afternoon, afternoon["puntualidad_oficial"]),
        "puntual_0_5": _pct(valid, valid["puntualidad_oficial"]),
        "puntual_pm5": _pct(valid, valid["puntual_pm5"]),
        "anticipadas": _pct(valid, valid["anticipada"]),
        "retrasos": _pct(valid, valid["retraso_oficial"]),
        "efectivos": len(effective),
        "sin_usuarios": (df["estado_operativo"] == "SIN USUARIOS").mean() if len(df) else np.nan,
        "tiempo_efectivo_promedio": times.mean() if len(times) else np.nan,
        "tiempo_mediana": times.median() if len(times) else np.nan,
        "tiempo_p80": times.quantile(.80) if len(times) else np.nan,
        "tiempo_efectivo_p90": times.quantile(.90) if len(times) else np.nan,
        "tiempo_p95": times.quantile(.95) if len(times) else np.nan,
        "tiempo_minimo": times.min() if len(times) else np.nan,
        "tiempo_maximo": times.max() if len(times) else np.nan,
        "tiempo_desviacion": times.std() if len(times) else np.nan,
        "tiempo_total_recorrido": times.sum() if len(times) else 0.0,
        "tiempo_total_espera": df["espera"].dropna().sum() if "espera" in df else 0.0,
    }


def _period_summary(group):
    m = kpis(group)
    return {
        "registros": m["registros"], "dias": m["dias"], "usuarios": m["usuarios"],
        "puntualidad_general": m["puntualidad_general"], "puntualidad_manana": m["puntualidad_manana"],
        "puntualidad_tarde": m["puntualidad_tarde"], "puntual_0_5": m["puntual_0_5"],
        "puntual_pm5": m["puntual_pm5"], "anticipadas": m["anticipadas"], "retrasos": m["retrasos"],
        "efectivos": m["efectivos"], "sin_usuarios": int((group["estado_operativo"] == "SIN USUARIOS").sum()),
        "efectividad": m["efectivos"] / len(group) if len(group) else np.nan,
        "tiempo_promedio": m["tiempo_efectivo_promedio"], "mediana": m["tiempo_mediana"],
        "p80": m["tiempo_p80"], "p90": m["tiempo_efectivo_p90"], "p95": m["tiempo_p95"],
    }


def monthly_summary(df):
    rows = []
    for month, group in df.groupby("mes", dropna=False):
        rows.append({"mes": month, **_period_summary(group)})
    return pd.DataFrame(rows).sort_values("mes") if rows else pd.DataFrame()


def weekly_summary(df, month=None):
    source = df[df["mes"] == month] if month else df
    rows = []
    for key, group in source.groupby(["mes", "numero_semana_mes", "semana_mes"], dropna=False):
        rows.append({"mes": key[0], "numero_semana": key[1], "semana": key[2], **_period_summary(group)})
    return pd.DataFrame(rows).sort_values(["mes", "numero_semana"]) if rows else pd.DataFrame()


def demand_summary(df):
    if df.empty: return pd.DataFrame()
    summary = df.groupby("recorrido").agg(
        salidas=("recorrido", "size"), usuarios=("usuarios", "sum"), promedio_usuarios=("usuarios", "mean"),
        efectivos=("estado_operativo", lambda x: (x == "EFECTIVO").sum()),
        sin_usuarios=("estado_operativo", lambda x: (x == "SIN USUARIOS").sum()),
    ).reset_index()
    summary["utilizacion_operativa"] = summary["efectivos"] / summary["salidas"]
    total = summary["usuarios"].sum()
    summary["participacion_usuarios"] = summary["usuarios"] / total if total else np.nan
    return summary


def stop_frequency(df):
    effective = effective_records(df)
    rows = []
    for stop in active_stops(df):
        column = f"usa_{stop_slug(stop)}"
        if column not in df.columns: continue
        all_uses, effective_uses = int(df[column].sum()), int(effective[column].sum())
        used = effective[effective[column] == 1]
        rows.append({
            "paradero": stop, "usos_registrados": all_uses,
            "frecuencia_registrada": all_uses / len(df) if len(df) else np.nan,
            "usos_efectivos": effective_uses,
            "frecuencia_efectiva": effective_uses / len(effective) if len(effective) else np.nan,
            "usuarios_asociados": int(used["usuarios"].sum()),
            "dias_uso_efectivo": used["fecha"].nunique(), "tiempo_promedio": used["trayecto"].mean(),
        })
    return pd.DataFrame(rows)


def combinations(df):
    effective = effective_records(df)
    if effective.empty: return pd.DataFrame()
    return effective.groupby(["jornada", "recorrido", "combinacion_paradas"]).agg(
        recorridos=("recorrido", "size"), usuarios=("usuarios", "sum"), usuarios_promedio=("usuarios", "mean"),
        tiempo_promedio=("trayecto", "mean"), mediana=("trayecto", "median"),
        p80=("trayecto", lambda x: x.dropna().quantile(.80) if x.notna().any() else np.nan),
        p90=("trayecto", lambda x: x.dropna().quantile(.90) if x.notna().any() else np.nan),
        p95=("trayecto", lambda x: x.dropna().quantile(.95) if x.notna().any() else np.nan),
        minimo=("trayecto", "min"), maximo=("trayecto", "max"), desviacion=("trayecto", "std"),
    ).reset_index()


def punctuality_summary(df):
    valid = _punctual_valid(df)
    if valid.empty: return pd.DataFrame()
    return valid.groupby(["jornada", "recorrido"]).agg(
        registros_validos=("desv_min", "size"),
        puntualidad_oficial=("puntualidad_oficial", "mean"), puntual_0_5=("puntualidad_oficial", "mean"),
        puntual_pm5=("puntual_pm5", "mean"), anticipadas=("anticipada", "mean"),
        retraso_mayor_5=("retraso_oficial", "mean"), desviacion_promedio=("desv_min", "mean"),
        desviacion_p90=("desv_min", lambda x: x.quantile(.90)),
    ).reset_index()


def return_margin(df):
    rows = []
    for (journey, date), group in df.groupby(["jornada", "fecha"]):
        route_map = {row["recorrido"]: row for _, row in group.iterrows()}
        for first, second in [("R1", "R2"), ("R2", "R3")]:
            if first in route_map and second in route_map:
                current, nxt = route_map[first], route_map[second]
                if current["estado_operativo"] == "EFECTIVO" and pd.notna(current["llegada"]) and pd.notna(nxt["prog"]):
                    margin = nxt["prog"] - current["llegada"]
                    if margin > 720: margin -= 1440
                    if margin < -720: margin += 1440
                    rows.append({"jornada": journey, "fecha": date, "tramo": f"{first}->{second}", "margen_min": margin})
    return pd.DataFrame(rows)


def weekly_punctuality_by_route(df, month=None):
    source = df[df["mes"] == month].copy() if month else df.copy()
    valid = _punctual_valid(source)
    if valid.empty: return pd.DataFrame()
    return valid.groupby(["mes", "numero_semana_mes", "semana_mes", "jornada", "recorrido"], dropna=False).agg(
        registros_validos=("desv_min", "size"), puntualidad_oficial=("puntualidad_oficial", "mean"),
        puntual_0_5=("puntualidad_oficial", "mean"), puntual_pm5=("puntual_pm5", "mean"),
        anticipadas=("anticipada", "mean"), retrasos_mayor_5=("retraso_oficial", "mean"),
    ).reset_index().rename(columns={"numero_semana_mes": "numero_semana", "semana_mes": "semana"}).sort_values(["mes", "numero_semana", "jornada", "recorrido"])


def weekly_route_usage(df, month=None):
    source = df[df["mes"] == month].copy() if month else df.copy()
    if source.empty: return pd.DataFrame()
    grouped = source.groupby(["mes", "numero_semana_mes", "semana_mes", "jornada", "recorrido"], dropna=False).agg(
        salidas_programadas=("recorrido", "size"), recorridos_efectivos=("estado_operativo", lambda x: (x == "EFECTIVO").sum()),
        usuarios=("usuarios", "sum"), promedio_usuarios_salida=("usuarios", "mean"),
    ).reset_index().rename(columns={"numero_semana_mes": "numero_semana", "semana_mes": "semana"})
    grouped["utilizacion_operativa"] = grouped["recorridos_efectivos"] / grouped["salidas_programadas"]
    totals = grouped.groupby(["mes", "numero_semana", "jornada"])["usuarios"].transform("sum")
    grouped["participacion_usuarios"] = np.where(totals > 0, grouped["usuarios"] / totals, np.nan)
    return grouped.sort_values(["mes", "numero_semana", "jornada", "recorrido"])


def time_statistics(df):
    data = effective_records(df)["trayecto"].dropna()
    if data.empty: return pd.DataFrame()
    mode = data.mode()
    return pd.DataFrame([{
        "n": len(data), "promedio": data.mean(), "mediana": data.median(),
        "moda": mode.iloc[0] if len(mode) else np.nan, "p80": data.quantile(.80),
        "p90": data.quantile(.90), "p95": data.quantile(.95), "desviacion": data.std(),
        "minimo": data.min(), "maximo": data.max(),
    }])


def before_after_summary(df, cut_date):
    cut = pd.Timestamp(cut_date)
    rows = []
    for label, group in [("Antes", df[df["fecha"] < cut]), ("Después", df[df["fecha"] >= cut])]:
        if group.empty: continue
        rows.append({"periodo": label, **kpis(group)})
    return pd.DataFrame(rows)

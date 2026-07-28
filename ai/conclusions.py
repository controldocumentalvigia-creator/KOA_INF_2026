import numpy as np
from core.metrics import kpis, demand_summary, stop_frequency, monthly_summary, selected_label


def generate_conclusions(df):
    label = selected_label(df)
    result = kpis(df)
    demand = demand_summary(df)
    stops = stop_frequency(df)
    monthly = monthly_summary(df)
    conclusions = []
    if not demand.empty:
        low = demand.sort_values("usuarios").iloc[0]
        high = demand.sort_values("usuarios", ascending=False).iloc[0]
        conclusions.append(f"En la {label}, {high['recorrido']} concentra la mayor demanda con {int(high['usuarios'])} usuarios, mientras {low['recorrido']} registra la menor con {int(low['usuarios'])}.")
    valid_stops = stops.dropna(subset=["frecuencia_efectiva"]) if not stops.empty else stops
    if not valid_stops.empty:
        top = valid_stops.sort_values("frecuencia_efectiva", ascending=False).iloc[0]
        conclusions.append(f"{top['paradero']} es el paradero más utilizado en recorridos efectivos, con una frecuencia de {top['frecuencia_efectiva']:.1%}.")
    if not np.isnan(result["puntual_0_5"]):
        conclusions.append(f"La puntualidad general ponderada es {result['puntualidad_general']:.1%}; las salidas anticipadas representan {result['anticipadas']:.1%} y las salidas retrasadas según la regla de cada jornada {result['retrasos']:.1%}.")
    if len(monthly) >= 2 and monthly.iloc[0]["usuarios"] != 0:
        variation = (monthly.iloc[-1]["usuarios"] - monthly.iloc[0]["usuarios"]) / monthly.iloc[0]["usuarios"]
        conclusions.append(f"Entre {monthly.iloc[0]['mes']} y {monthly.iloc[-1]['mes']}, el volumen de usuarios varió {variation:+.1%}.")
    if not np.isnan(result["tiempo_efectivo_promedio"]):
        conclusions.append(f"El tiempo medio de los recorridos efectivos es {result['tiempo_efectivo_promedio']:.1f} minutos y el P90 es {result['tiempo_efectivo_p90']:.1f} minutos.")
    return conclusions

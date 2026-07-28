from core.metrics import demand_summary, punctuality_summary, stop_frequency, selected_label


def generate_recommendations(df):
    label = selected_label(df)
    recs = []
    demand = demand_summary(df)
    punctual = punctuality_summary(df)
    stops = stop_frequency(df)
    if not demand.empty:
        low = demand.sort_values("usuarios").iloc[0]
        recs.append({"prioridad": "Alta", "accion": f"Revisar la configuración y uso de {low['recorrido']}.", "motivo": f"Es el recorrido con menor demanda acumulada en la {label}.", "plazo": "30 días"})
    if not punctual.empty and punctual["puntual_0_5"].mean() < 0.8:
        recs.append({"prioridad": "Alta", "accion": "Implementar seguimiento semanal de puntualidad por ruta y causa.", "motivo": "La puntualidad está por debajo del umbral gerencial del 80%.", "plazo": "Inmediato"})
    low_evidence = stops[(stops["usos_efectivos"] < 5) & (stops["usos_registrados"] > 0)] if not stops.empty else stops
    if not low_evidence.empty:
        names = ", ".join(low_evidence["paradero"].tolist())
        recs.append({"prioridad": "Media", "accion": f"Validar mediante piloto el comportamiento de {names}.", "motivo": "La muestra efectiva es insuficiente para una decisión permanente.", "plazo": "2 semanas"})
    recs.append({"prioridad": "Media", "accion": "Completar obligatoriamente PARADAS y documentar novedades.", "motivo": "Mejora la trazabilidad y evita sesgos en los indicadores.", "plazo": "Inmediato"})
    return recs

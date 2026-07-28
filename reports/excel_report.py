from io import BytesIO
import pandas as pd
from core.metrics import (
    kpis, monthly_summary, weekly_summary, demand_summary, stop_frequency,
    combinations, punctuality_summary, return_margin,
    weekly_punctuality_by_route, weekly_route_usage
)
from ai.recommendations import generate_recommendations

def build_excel(df) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame([kpis(df)]).to_excel(writer, sheet_name="KPI", index=False)
        monthly_summary(df).to_excel(writer, sheet_name="Mensual", index=False)
        weekly_summary(df).to_excel(writer, sheet_name="Semanal", index=False)
        demand_summary(df).to_excel(writer, sheet_name="Demanda", index=False)
        stop_frequency(df).to_excel(writer, sheet_name="Paraderos", index=False)
        combinations(df).to_excel(writer, sheet_name="Combinaciones", index=False)
        punctuality_summary(df).to_excel(writer, sheet_name="Puntualidad", index=False)
        weekly_punctuality_by_route(df).to_excel(writer, sheet_name="Puntualidad semanal", index=False)
        weekly_route_usage(df).to_excel(writer, sheet_name="Uso rutas semanal", index=False)
        return_margin(df).to_excel(writer, sheet_name="Retorno", index=False)
        pd.DataFrame(generate_recommendations(df)).to_excel(writer, sheet_name="Plan accion", index=False)
        df.to_excel(writer, sheet_name="Detalle auditado", index=False)
    return output.getvalue()

import plotly.express as px
import streamlit as st
from core.metrics import punctuality_summary
from dashboard.common import chart, table


def render(df):
    st.subheader("Puntualidad por jornada y recorrido")
    st.caption("Mañana y tarde: puntual entre 0 y 5 minutos; anticipada antes de la hora programada y retrasada desde el minuto 6.")
    summary = punctuality_summary(df)
    if summary.empty:
        st.info("No hay registros válidos de puntualidad.")
        return
    table(summary, {
        "puntualidad_oficial": "{:.1%}", "puntual_0_5": "{:.1%}", "puntual_pm5": "{:.1%}",
        "anticipadas": "{:.1%}", "retraso_mayor_5": "{:.1%}", "desviacion_promedio": "{:.1f}", "desviacion_p90": "{:.1f}",
    })
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(summary, x="recorrido", y="puntualidad_oficial", color="jornada", barmode="group", text_auto=".1%", title="Puntualidad oficial")
        fig.update_yaxes(tickformat=".0%", range=[0,1])
        chart(fig, "punctual-official")
    with c2:
        melted = summary.melt(id_vars=["jornada", "recorrido"], value_vars=["anticipadas", "puntualidad_oficial", "retraso_mayor_5"], var_name="clasificación", value_name="porcentaje")
        fig = px.bar(melted, x="recorrido", y="porcentaje", color="clasificación", facet_col="jornada", barmode="stack", title="Distribución de salidas")
        fig.update_yaxes(tickformat=".0%", range=[0,1])
        chart(fig, "punctual-distribution")

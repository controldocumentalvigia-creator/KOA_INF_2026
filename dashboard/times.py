import plotly.express as px
import streamlit as st
from core.metrics import combinations, effective_records, selected_label
from dashboard.common import chart, table


def render(df):
    label = selected_label(df)
    st.subheader(f"Combinaciones y tiempos — {label}")
    combo = combinations(df)
    if combo.empty:
        st.info("No existen recorridos efectivos para analizar tiempos con los filtros seleccionados.")
        return
    table(combo, {"usuarios_promedio": "{:.2f}", "tiempo_promedio": "{:.1f}", "mediana": "{:.1f}", "p90": "{:.1f}", "p95": "{:.1f}", "minimo": "{:.1f}", "maximo": "{:.1f}", "desviacion": "{:.1f}"})
    effective = effective_records(df)
    c1, c2 = st.columns(2)
    with c1:
        chart(px.box(effective, x="recorrido", y="trayecto", color="jornada", points="outliers", title="Distribución de tiempos por recorrido"), "time-box")
    with c2:
        chart(px.scatter(combo, x="tiempo_promedio", y="usuarios_promedio", size="recorridos", color="combinacion_paradas", facet_col="recorrido", hover_data=["jornada", "p90", "p95"], title="Tiempo vs. demanda por combinación"), "time-demand")

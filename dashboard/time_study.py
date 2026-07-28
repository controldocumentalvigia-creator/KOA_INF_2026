import plotly.express as px
import streamlit as st
from core.metrics import effective_records, time_statistics
from dashboard.common import chart, table


def render(df):
    st.subheader("Estudio estadístico de tiempos")
    stats = time_statistics(df)
    if stats.empty:
        st.info("No hay tiempos válidos para los filtros seleccionados.")
        return
    table(stats, {c: "{:.1f}" for c in stats.columns if c != "n"})
    effective = effective_records(df).dropna(subset=["trayecto"])
    c1, c2 = st.columns(2)
    with c1:
        chart(px.histogram(effective, x="trayecto", color="jornada", nbins=25, marginal="box", title="Distribución de tiempos"), "study-hist")
    with c2:
        chart(px.box(effective, x="recorrido", y="trayecto", color="jornada", points="outliers", title="Variabilidad por recorrido"), "study-box")
    daily = effective.groupby(["fecha", "jornada", "recorrido"], as_index=False)["trayecto"].mean()
    chart(px.line(daily, x="fecha", y="trayecto", color="recorrido", line_dash="jornada", markers=True, title="Serie temporal del tiempo promedio"), "study-series")

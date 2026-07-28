import pandas as pd
import plotly.express as px
import streamlit as st
from core.metrics import before_after_summary
from dashboard.common import chart


def render(df):
    st.subheader("Comparativo antes vs. después")
    if df["fecha"].dropna().empty:
        st.info("No hay fechas válidas.")
        return
    min_d, max_d = df["fecha"].min().date(), df["fecha"].max().date()
    default = min_d + (max_d - min_d) / 2
    cut = st.date_input("Fecha de inicio del cambio operacional", value=default, min_value=min_d, max_value=max_d)
    summary = before_after_summary(df, cut)
    if len(summary) < 2:
        st.warning("La fecha debe dejar registros tanto antes como después.")
        return
    cols = ["periodo", "registros", "usuarios", "efectivos", "puntualidad_general", "tiempo_efectivo_promedio", "tiempo_efectivo_p90", "tiempo_total_espera"]
    st.dataframe(summary[cols].style.format({"puntualidad_general":"{:.1%}", "tiempo_efectivo_promedio":"{:.1f}", "tiempo_efectivo_p90":"{:.1f}", "tiempo_total_espera":"{:.1f}"}), hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(summary, x="periodo", y="puntualidad_general", text_auto=".1%", title="Puntualidad antes vs. después")
        fig.update_yaxes(tickformat=".0%", range=[0,1])
        chart(fig, "cmp-punctual")
    with c2:
        chart(px.bar(summary, x="periodo", y=["tiempo_efectivo_promedio", "tiempo_efectivo_p90"], barmode="group", title="Tiempo promedio y P90"), "cmp-time")

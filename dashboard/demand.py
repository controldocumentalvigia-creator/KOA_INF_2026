import plotly.express as px
import streamlit as st
from core.metrics import demand_summary, selected_label
from dashboard.common import chart, table


def render(df):
    label = selected_label(df)
    st.subheader(f"Demanda — {label}")
    summary = demand_summary(df)
    if summary.empty:
        st.info("No hay datos de demanda con los filtros seleccionados.")
        return
    table(summary, {"promedio_usuarios": "{:.2f}", "utilizacion_operativa": "{:.1%}", "participacion_usuarios": "{:.1%}"})
    daily = df.groupby(["fecha", "recorrido"], as_index=False)["usuarios"].sum()
    c1, c2 = st.columns(2)
    with c1:
        chart(px.bar(summary, x="recorrido", y="usuarios", text_auto=True, title="Usuarios acumulados"), "demand-total")
    with c2:
        chart(px.bar(summary, x="recorrido", y=["efectivos", "sin_usuarios"], barmode="group", title="Recorridos efectivos vs. sin usuarios"), "demand-status")
    chart(px.line(daily, x="fecha", y="usuarios", color="recorrido", markers=True, title="Evolución diaria de usuarios"), "demand-daily")

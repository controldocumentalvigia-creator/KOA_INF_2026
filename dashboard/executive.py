import plotly.express as px
import streamlit as st
from core.metrics import monthly_summary, demand_summary, selected_label
from ai.conclusions import generate_conclusions
from ai.recommendations import generate_recommendations
from dashboard.common import chart


def render(df):
    label = selected_label(df)
    st.subheader(f"Resumen ejecutivo — {label}")
    monthly = monthly_summary(df)
    demand = demand_summary(df)
    c1, c2 = st.columns(2)
    with c1:
        chart(px.line(monthly, x="mes", y="usuarios", markers=True, title=f"Usuarios por mes — {label}"), "exec-users")
    with c2:
        if demand.empty:
            st.info("No hay datos de demanda con los filtros seleccionados.")
        else:
            chart(px.bar(demand, x="recorrido", y="usuarios", text_auto=True, title=f"Demanda acumulada por recorrido — {label}"), "exec-demand")
    st.markdown("#### Hallazgos automáticos")
    conclusions = generate_conclusions(df)
    if conclusions:
        for conclusion in conclusions: st.markdown(f"- {conclusion}")
    else:
        st.info("No hay evidencia suficiente para generar hallazgos con estos filtros.")
    st.markdown("#### Plan de acción")
    st.dataframe(generate_recommendations(df), hide_index=True, use_container_width=True)

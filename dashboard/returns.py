import plotly.express as px
import streamlit as st
from core.metrics import return_margin
from dashboard.common import chart

def render(df):
    st.subheader("Retorno real")
    margins = return_margin(df)
    if margins.empty:
        st.info("No existen datos válidos para calcular el retorno.")
        return
    summary = margins.groupby("tramo").margen_min.agg(
        n="count", promedio="mean", mediana="median", minimo="min", maximo="max",
        retorno_antes=lambda x: (x >= 0).mean(),
        margen_5min=lambda x: (x >= 5).mean(),
    ).reset_index()
    st.dataframe(summary.style.format({
        "promedio": "{:.1f}", "mediana": "{:.1f}", "minimo": "{:.1f}", "maximo": "{:.1f}",
        "retorno_antes": "{:.1%}", "margen_5min": "{:.1%}",
    }), hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        chart(px.box(margins, x="tramo", y="margen_min", points="all",
                     title="Margen real de retorno"), "return-box")
    with c2:
        fig = px.bar(summary, x="tramo", y=["retorno_antes", "margen_5min"],
                     barmode="group", title="Cumplimiento del retorno")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "return-bar")
    chart(px.line(margins, x="fecha", y="margen_min", color="tramo", markers=True,
                  title="Evolución diaria del margen"), "return-line")

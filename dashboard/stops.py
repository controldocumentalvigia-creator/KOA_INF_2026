import pandas as pd
import plotly.express as px
import streamlit as st
from core.metrics import stop_frequency, active_stops, selected_label
from core.utils import stop_slug
from dashboard.common import chart, table


def render(df):
    label = selected_label(df)
    st.subheader(f"Frecuencia de paraderos — {label}")
    freq = stop_frequency(df)
    if freq.empty:
        st.info("No existen paraderos identificables con los filtros seleccionados.")
        return
    table(freq, {"frecuencia_registrada": "{:.1%}", "frecuencia_efectiva": "{:.1%}", "tiempo_promedio": "{:.1f}"})
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(freq, x="paradero", y=["frecuencia_registrada", "frecuencia_efectiva"], barmode="group", title="Frecuencia registrada vs. efectiva")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "stops-frequency")
    with c2:
        chart(px.bar(freq, x="paradero", y="dias_uso_efectivo", text_auto=True, title="Días con uso efectivo"), "stops-days")
    heat_rows = []
    for route, group in df.groupby("recorrido"):
        for stop in active_stops(df):
            column = f"usa_{stop_slug(stop)}"
            if column in group.columns:
                heat_rows.append({"recorrido": route, "paradero": stop, "frecuencia": group[column].mean()})
    heat = pd.DataFrame(heat_rows)
    if not heat.empty:
        chart(px.density_heatmap(heat, x="paradero", y="recorrido", z="frecuencia", histfunc="avg", text_auto=".0%", color_continuous_scale="Blues", title="Mapa de calor por recorrido"), "stops-heat")
    month_rows = []
    for month, group in df.groupby("mes"):
        for stop in active_stops(df):
            column = f"usa_{stop_slug(stop)}"
            if column in group.columns:
                month_rows.append({"mes": month, "paradero": stop, "frecuencia": group[column].mean()})
    monthly = pd.DataFrame(month_rows)
    if not monthly.empty:
        fig = px.line(monthly, x="mes", y="frecuencia", color="paradero", markers=True, title="Evolución mensual de paraderos")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "stops-month")

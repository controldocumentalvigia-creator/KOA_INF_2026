import plotly.express as px
import streamlit as st
from core.metrics import monthly_summary, weekly_summary, weekly_punctuality_by_route, weekly_route_usage, selected_label
from dashboard.common import chart, table

PCT = {"puntual_0_5": "{:.1%}", "puntual_pm5": "{:.1%}", "anticipadas": "{:.1%}", "retrasos": "{:.1%}", "efectividad": "{:.1%}", "tiempo_promedio": "{:.1f}", "p90": "{:.1f}"}


def render(df):
    label = selected_label(df)
    st.subheader(f"Análisis mensual y semanal — {label}")
    monthly = monthly_summary(df)
    if monthly.empty:
        st.info("No hay datos mensuales con los filtros seleccionados.")
        return
    table(monthly, PCT)
    c1, c2 = st.columns(2)
    with c1:
        chart(px.bar(monthly, x="mes", y="usuarios", text_auto=True, title="Usuarios por mes"), "month-users")
    with c2:
        fig = px.line(monthly, x="mes", y="puntual_0_5", markers=True, title="Puntualidad mensual")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "month-punctual")
    available = sorted(df["mes"].dropna().unique())
    selected = st.selectbox("Mes para análisis semanal", available, index=len(available)-1)
    weekly = weekly_summary(df, selected)
    table(weekly, PCT)
    c3, c4 = st.columns(2)
    with c3:
        chart(px.bar(weekly, x="semana", y="usuarios", text_auto=True, title=f"Usuarios semanales - {selected}"), "week-users")
    with c4:
        fig = px.line(weekly, x="semana", y="puntual_0_5", markers=True, title=f"Puntualidad semanal - {selected}")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "week-punctual")
    selected_df = df[df["mes"] == selected]
    users_route = selected_df.groupby(["semana_mes", "recorrido"], as_index=False)["usuarios"].sum()
    chart(px.bar(users_route, x="semana_mes", y="usuarios", color="recorrido", barmode="group", title=f"Usuarios por recorrido y semana - {selected}"), "week-route")
    st.markdown("### Puntualidad semanal por recorrido")
    weekly_punctuality = weekly_punctuality_by_route(df, selected)
    if weekly_punctuality.empty:
        st.info("No existen registros válidos de puntualidad para el mes seleccionado.")
    else:
        st.dataframe(weekly_punctuality.style.format({"puntual_0_5": "{:.1%}", "puntual_pm5": "{:.1%}", "anticipadas": "{:.1%}", "retrasos_mayor_5": "{:.1%}"}), hide_index=True, use_container_width=True)
        p1, p2 = st.columns(2)
        with p1:
            fig = px.bar(weekly_punctuality, x="semana", y="puntual_0_5", color="recorrido", barmode="group", text_auto=".1%", title=f"Puntualidad oficial semanal por ruta - {selected}")
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            chart(fig, "weekly-punctual-route")
        with p2:
            fig = px.line(weekly_punctuality, x="semana", y="retrasos_mayor_5", color="recorrido", markers=True, title=f"Retrasos >5 min por semana - {selected}")
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            chart(fig, "weekly-delays-route")
    st.markdown("### Uso semanal de las rutas")
    route_usage = weekly_route_usage(df, selected)
    if route_usage.empty:
        st.info("No existen registros para calcular el uso semanal.")
    else:
        st.dataframe(route_usage.style.format({"utilizacion_operativa": "{:.1%}", "participacion_usuarios": "{:.1%}", "promedio_usuarios_salida": "{:.2f}"}), hide_index=True, use_container_width=True)
        u1, u2 = st.columns(2)
        with u1:
            fig = px.bar(route_usage, x="semana", y="utilizacion_operativa", color="recorrido", barmode="group", text_auto=".1%", title=f"% utilización operativa semanal - {selected}")
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            chart(fig, "weekly-route-utilization")
        with u2:
            fig = px.bar(route_usage, x="semana", y="participacion_usuarios", color="recorrido", barmode="stack", text_auto=".1%", title=f"Participación semanal de usuarios por ruta - {selected}")
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            chart(fig, "weekly-route-share")

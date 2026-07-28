import plotly.express as px
import streamlit as st
from simulator.stop_optimizer import rank_stop_combinations
from dashboard.common import chart


def render(df):
    st.subheader("Simulador inteligente de combinaciones de paraderos")
    st.caption("Evalúa combinaciones de 1 a 3 paraderos con evidencia histórica. Los resultados son exploratorios y requieren piloto.")
    ranking = rank_stop_combinations(df, 3)
    if ranking.empty:
        st.info("No hay evidencia efectiva de jornada tarde para ejecutar el optimizador.")
        return
    top_n = st.select_slider("Cantidad de propuestas a mostrar", [2,3,5], value=3)
    view = ranking.head(top_n)
    st.dataframe(view.style.format({"cobertura":"{:.1%}", "tiempo_promedio_evidencia":"{:.1f}", "ahorro_estimado_min":"{:.1f}", "puntaje":"{:.1f}"}), hide_index=True, use_container_width=True)
    chart(px.scatter(ranking, x="tiempo_promedio_evidencia", y="cobertura", size="usuarios_cubiertos", color="paraderos", hover_name="combinación", title="Cobertura vs. tiempo por combinación"), "optimizer-scatter")

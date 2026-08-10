import plotly.express as px
import streamlit as st

from core.metrics import demand_summary, selected_label
from dashboard.common import chart, table


def render(df):

    label = selected_label(df)

    st.subheader(
        f"Utilización y demanda operativa — {label}"
    )

    # ==========================================================
    # RESUMEN
    # ==========================================================

    summary = demand_summary(df)

    if summary.empty:
        st.info(
            "No hay datos de utilización con los filtros seleccionados."
        )
        return

    # ==========================================================
    # TABLA
    # ==========================================================

    table(
        summary,
        {
            "promedio_usuarios": "{:.2f}",
            "utilizacion_operativa": "{:.1%}",
            "participacion_usuarios": "{:.1%}",
        },
    )

    # ==========================================================
    # USUARIOS POR DÍA Y RECORRIDO
    # ==========================================================

    daily = (
        df.groupby(
            ["fecha", "recorrido"],
            as_index=False,
        )["usuarios"]
        .sum()
    )

    # ==========================================================
    # GRÁFICOS
    # ==========================================================

    c1, c2 = st.columns(2)

    with c1:

        chart(
            px.bar(
                summary,
                x="recorrido",
                y="usuarios",
                text_auto=True,
                title="Usuarios transportados acumulados",
                labels={
                    "recorrido": "Recorrido",
                    "usuarios": "Usuarios registrados",
                },
            ),
            "demand-total",
        )

        st.caption(
            "Corresponde a la suma de usuarios registrados "
            "en todos los recorridos del periodo filtrado. "
            "No representa usuarios únicos ni demanda declarada "
            "en la encuesta."
        )

    with c2:

        chart(
            px.bar(
                summary,
                x="recorrido",
                y=["efectivos", "sin_usuarios"],
                barmode="group",
                title="Recorridos efectivos vs. sin usuarios",
                labels={
                    "recorrido": "Recorrido",
                    "value": "Cantidad de recorridos",
                    "variable": "Estado",
                },
            ),
            "demand-status",
        )

    # ==========================================================
    # EVOLUCIÓN DIARIA
    # ==========================================================

    chart(
        px.line(
            daily,
            x="fecha",
            y="usuarios",
            color="recorrido",
            markers=True,
            title="Usuarios transportados por día",
            labels={
                "fecha": "Fecha",
                "usuarios": "Usuarios registrados",
                "recorrido": "Recorrido",
            },
        ),
        "demand-daily",
    )

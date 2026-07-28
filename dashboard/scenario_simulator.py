import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import STOPS, ROUTES
from core.scenarios import (
    evaluate_scenario, analyze_operating_window, analyze_historical_schedule,
    minutes_to_clock,
)


def _timeline_figure(schedule, title):
    fig = go.Figure()
    for _, row in schedule.iterrows():
        route = row["recorrido"]
        fig.add_trace(go.Bar(
            name="Ida",
            y=[route],
            x=[row["fin_ida_min"] - row["inicio_min"]],
            base=[row["inicio_min"]],
            orientation="h",
            text=[f"Ida {minutes_to_clock(row['inicio_min'])}–{minutes_to_clock(row['fin_ida_min'])}"],
            textposition="inside",
            hovertemplate=(
                f"<b>{route} - Ida</b><br>Salida: {row['salida_programada']}"
                f"<br>Llegada: {row['llegada_destino']}<extra></extra>"
            ),
        ))
        fig.add_trace(go.Bar(
            name="Retorno",
            y=[route],
            x=[row["fin_ciclo_min"] - row["fin_ida_min"]],
            base=[row["fin_ida_min"]],
            orientation="h",
            text=[f"Retorno hasta {row['retorno_KOA']}"],
            textposition="inside",
            hovertemplate=(
                f"<b>{route} - Retorno</b><br>Inicio retorno: {row['llegada_destino']}"
                f"<br>Regreso a KOA: {row['retorno_KOA']}<extra></extra>"
            ),
        ))

    tick_start = int(schedule["inicio_min"].min()) - 5
    tick_end = int(schedule["fin_ciclo_min"].max()) + 5
    ticks = list(range(tick_start, tick_end + 1, 5))
    fig.update_layout(
        title=title,
        barmode="overlay",
        height=390,
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=25, r=25, t=80, b=40),
        xaxis=dict(
            title="Hora",
            tickmode="array",
            tickvals=ticks,
            ticktext=[minutes_to_clock(value) for value in ticks],
            range=[tick_start, tick_end],
            gridcolor="rgba(0,0,0,0.08)",
        ),
        yaxis=dict(title="Recorrido", autorange="reversed"),
    )
    return fig



def _historical_timeline_figure(history):
    fig = go.Figure()

    for _, row in history.iterrows():
        if pd.isna(row["tiempo_promedio_real_min"]):
            continue

        route = row["recorrido"]
        start = row["inicio_min"]
        fig.add_trace(go.Bar(
            name="Tiempo promedio real",
            y=[route],
            x=[row["tiempo_promedio_real_min"]],
            base=[start],
            orientation="h",
            text=[f"Promedio {row['tiempo_promedio_real_min']:.1f} min"],
            textposition="inside",
            hovertemplate=(
                f"<b>{route}</b><br>Salida: {row['salida_programada']}"
                f"<br>Promedio real: {row['tiempo_promedio_real_min']:.1f} min"
                f"<br>Retorno promedio: {minutes_to_clock(row['fin_promedio_min'])}<extra></extra>"
            ),
            marker_color="#1D5DA7",
        ))
        fig.add_trace(go.Bar(
            name="Extensión hasta P90",
            y=[route],
            x=[max(0, row["p90_real_min"] - row["tiempo_promedio_real_min"])],
            base=[row["fin_promedio_min"]],
            orientation="h",
            text=[f"P90 {row['p90_real_min']:.1f} min"],
            textposition="inside",
            hovertemplate=(
                f"<b>{route} - P90</b><br>Retorno P90: "
                f"{minutes_to_clock(row['fin_p90_min'])}<extra></extra>"
            ),
            marker_color="#F39C3D",
        ))

    for _, row in history.iterrows():
        fig.add_vline(
            x=row["inicio_min"],
            line_width=2,
            line_dash="dash",
            line_color="#123D76",
            annotation_text=f"{row['recorrido']} {row['salida_programada']}",
            annotation_position="top",
        )

    min_x = int(history["inicio_min"].min()) - 5
    max_x = int(history["fin_p90_min"].dropna().max()) + 5
    ticks = list(range(min_x, max_x + 1, 5))
    fig.update_layout(
        title="Tiempo histórico real frente a las salidas asignadas",
        barmode="overlay",
        height=430,
        legend=dict(orientation="h", y=1.16),
        margin=dict(l=25, r=25, t=95, b=45),
        xaxis=dict(
            title="Hora",
            tickmode="array",
            tickvals=ticks,
            ticktext=[minutes_to_clock(value) for value in ticks],
            range=[min_x, max_x],
            gridcolor="rgba(0,0,0,0.08)",
        ),
        yaxis=dict(title="Recorrido", autorange="reversed"),
    )
    return fig

def _schedule_section(title, departures, shift_ends, outbound, return_time, minimum_margin):
    schedule, summary = analyze_operating_window(
        departures=departures,
        shift_end_times=shift_ends,
        outbound_minutes=outbound,
        return_minutes=return_time,
        minimum_positioning_minutes=minimum_margin,
    )

    st.markdown(f"### {title}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ciclo por recorrido", f"{summary['tiempo_ciclo_min']} min")
    c2.metric("Tres recorridos", f"{summary['tiempo_total_tres_recorridos_min']} min")
    c3.metric("Margen mínimo real", (
        f"{summary['margen_minimo_min']:.0f} min"
        if pd.notna(summary["margen_minimo_min"]) else "N/D"
    ))
    c4.metric("Viabilidad con un vehículo", "SÍ" if summary["viable_un_vehiculo"] else "NO")

    st.plotly_chart(_timeline_figure(schedule, f"Línea de tiempo operacional — {title}"), use_container_width=True)

    display = schedule[[
        "recorrido", "fin_jornada_usuarios", "salida_programada", "espera_usuarios_min",
        "llegada_destino", "retorno_KOA", "margen_antes_siguiente_min", "estado"
    ]].copy()
    display.columns = [
        "Recorrido", "Fin jornada usuarios", "Salida", "Ventana de abordaje (min)",
        "Llegada destino", "Retorno a KOA", "Margen antes de siguiente salida (min)", "Estado"
    ]
    st.dataframe(display, hide_index=True, use_container_width=True)

    conflicts = schedule[schedule["estado"].isin(["SIN HOLGURA", "SOLAPAMIENTO"])]
    if len(conflicts):
        route_names = ", ".join(conflicts["recorrido"].tolist())
        st.error(
            f"La programación presenta riesgo en {route_names}. El vehículo retorna con margen inferior "
            f"a {minimum_margin} minutos antes de la siguiente salida."
        )
    else:
        st.success(
            f"La secuencia es viable con un solo vehículo y conserva al menos {minimum_margin} minutos "
            "para posicionamiento y abordaje antes de cada salida posterior."
        )
    return schedule, summary


def render(df):
    if "TARDE" not in set(df["jornada"].dropna().unique()):
        st.info("El simulador operativo está diseñado para la jornada tarde. Seleccione TARDE en el filtro lateral para evaluar horarios y paraderos de salida.")
        return
    st.subheader("Simulador de escenarios")

    st.markdown("## 1. Escenario por paraderos y demanda")
    c1, c2 = st.columns(2)
    with c1:
        route = st.selectbox("Ruta", ROUTES)
        stops = st.multiselect("Paraderos", STOPS, default=["VIRREY"])
    with c2:
        demand = st.slider("Variación esperada de demanda (%)", -50, 100, 0)
        minutes = st.slider("Minutos adicionales estimados", 0, 30, 0)
    if stops:
        result = evaluate_scenario(df, route, stops, demand, minutes)
        st.dataframe([result], hide_index=True, use_container_width=True)
        if result["evidencia"] == "Baja":
            st.warning(result["nota"])
    else:
        st.warning("Seleccione al menos un paradero.")

    st.divider()
    st.markdown("## 2. Visual de tiempos y disponibilidad del vehículo")
    st.caption(
        "El análisis considera un solo vehículo, 15 minutos de ida y 15 minutos de retorno. "
        "También muestra cuánto tiempo tienen los usuarios para abordar después de terminar su jornada."
    )

    p1, p2, p3 = st.columns(3)
    with p1:
        outbound = st.number_input("Minutos de ida", min_value=1, max_value=60, value=15)
    with p2:
        return_time = st.number_input("Minutos de retorno", min_value=1, max_value=60, value=15)
    with p3:
        minimum_margin = st.number_input(
            "Margen mínimo para posicionamiento", min_value=0, max_value=30, value=5,
            help="Tiempo mínimo recomendado entre el retorno a KOA y la siguiente salida."
        )

    morning_schedule, morning_summary = _schedule_section(
        "Jornada mañana",
        departures=["06:45", "07:15", "07:45"],
        shift_ends=["06:35", "07:05", "07:35"],
        outbound=outbound,
        return_time=return_time,
        minimum_margin=minimum_margin,
    )

    afternoon_schedule, afternoon_summary = _schedule_section(
        "Jornada tarde",
        departures=["17:10", "17:45", "18:15"],
        shift_ends=["17:00", "17:30", "18:00"],
        outbound=outbound,
        return_time=return_time,
        minimum_margin=minimum_margin,
    )

    st.markdown("### Lectura ejecutiva del escenario actual")
    r1 = afternoon_schedule.iloc[0]
    r2 = afternoon_schedule.iloc[1]
    r3 = afternoon_schedule.iloc[2]
    st.markdown(
        f"""
- **R1:** los usuarios terminan a las 17:00 y salen a las 17:10, por lo que cuentan con **{int(r1['espera_usuarios_min'])} minutos** para abordar. El vehículo retorna a KOA a las **{r1['retorno_KOA']}**.
- **R2:** los usuarios terminan a las 17:30 y salen a las 17:45, con **{int(r2['espera_usuarios_min'])} minutos** para abordar. R1 deja un margen de **{int(r2['margen_antes_siguiente_min'])} minutos** antes de R2.
- **R3:** los usuarios terminan a las 18:00 y salen a las 18:15, con **{int(r3['espera_usuarios_min'])} minutos** teóricos para abordar; sin embargo, R2 retorna a las **{r2['retorno_KOA']}**, por lo que el vehículo dispone de **{int(r3['margen_antes_siguiente_min'])} minutos** reales antes de la salida de R3.
"""
    )

    if not afternoon_summary["viable_un_vehiculo"]:
        recommended_r3 = minutes_to_clock(
            afternoon_schedule.iloc[1]["fin_ciclo_min"] + minimum_margin
        )
        st.warning(
            f"Con ciclos de {outbound + return_time} minutos, el horario de las 18:15 no conserva margen "
            f"operativo. Para asegurar al menos {minimum_margin} minutos de posicionamiento, R3 debería "
            f"salir a las **{recommended_r3}** o se tendría que reducir el tiempo de ciclo/usar otro vehículo."
        )


    st.divider()
    st.markdown("## 3. Realidad histórica: ¿los tiempos alcanzan para los horarios asignados?")
    st.caption(
        "Esta visual ya no utiliza el supuesto de 15 minutos de ida y 15 de retorno. "
        "Compara directamente los tiempos reales registrados en la base con los intervalos "
        "programados R1→R2 y R2→R3."
    )

    historical = analyze_historical_schedule(
        df,
        departures=("17:10", "17:45", "18:15"),
        minimum_positioning_minutes=minimum_margin,
    )

    st.plotly_chart(
        _historical_timeline_figure(historical),
        use_container_width=True,
        key="historical-real-timeline",
    )

    historical_display = historical[[
        "recorrido", "salida_programada", "siguiente_salida",
        "intervalo_asignado_min", "observaciones",
        "tiempo_promedio_real_min", "p90_real_min",
        "margen_promedio_min", "margen_p90_min",
        "cumple_antes_siguiente_pct", "cumple_margen_minimo_pct",
        "estado_promedio", "estado_p90",
    ]].copy()
    historical_display.columns = [
        "Recorrido", "Salida", "Siguiente salida", "Intervalo asignado (min)",
        "Datos válidos", "Tiempo promedio real (min)", "P90 real (min)",
        "Margen con promedio (min)", "Margen con P90 (min)",
        "% retorna antes de siguiente salida", "% conserva margen mínimo",
        "Estado promedio", "Estado P90",
    ]

    st.dataframe(
        historical_display.style.format({
            "Intervalo asignado (min)": "{:.0f}",
            "Tiempo promedio real (min)": "{:.1f}",
            "P90 real (min)": "{:.1f}",
            "Margen con promedio (min)": "{:.1f}",
            "Margen con P90 (min)": "{:.1f}",
            "% retorna antes de siguiente salida": "{:.1%}",
            "% conserva margen mínimo": "{:.1%}",
        }),
        hide_index=True,
        use_container_width=True,
    )

    r1_hist = historical[historical["recorrido"] == "R1"].iloc[0]
    r2_hist = historical[historical["recorrido"] == "R2"].iloc[0]

    st.markdown("### Lectura ejecutiva basada en los tiempos reales")
    st.markdown(
        f"""
- **R1 dispone de {r1_hist['intervalo_asignado_min']:.0f} minutos** entre su salida de las 17:10 y R2 de las 17:45. Su tiempo real promedio es **{r1_hist['tiempo_promedio_real_min']:.1f} minutos** y el P90 es **{r1_hist['p90_real_min']:.1f} minutos**. Con el P90, el vehículo retorna aproximadamente a las **{minutes_to_clock(r1_hist['fin_p90_min'])}**, generando un margen de **{r1_hist['margen_p90_min']:.1f} minutos** frente a R2.
- **R2 dispone de {r2_hist['intervalo_asignado_min']:.0f} minutos** entre las 17:45 y las 18:15. Su tiempo real promedio es **{r2_hist['tiempo_promedio_real_min']:.1f} minutos** y el P90 es **{r2_hist['p90_real_min']:.1f} minutos**. En el escenario P90, el retorno ocurre alrededor de las **{minutes_to_clock(r2_hist['fin_p90_min'])}**, con un margen de **{r2_hist['margen_p90_min']:.1f} minutos** antes de R3.
- Para una programación confiable no basta con que el promedio alcance. El horario debe soportar también los días de mayor duración; por eso el **P90** es el indicador principal para determinar si la secuencia es sostenible.
"""
    )

    conflicts = historical[
        historical["estado_p90"].isin(["SIN HOLGURA", "SOLAPAMIENTO"])
    ]
    if not conflicts.empty:
        affected = ", ".join(conflicts["recorrido"].tolist())
        st.error(
            f"Los tiempos históricos demuestran que la programación no es robusta en {affected}. "
            "En el escenario P90 el vehículo no conserva el margen mínimo requerido o retorna "
            "después de la siguiente salida. La limitación corresponde al diseño del horario, "
            "no solamente a la ejecución del conductor."
        )
    else:
        st.success(
            "Los tiempos históricos P90 caben dentro de los intervalos programados y conservan "
            f"al menos {minimum_margin} minutos de margen."
        )

from pathlib import Path

import pandas as pd
import streamlit as st

from config import (
    APP_TITLE,
    APP_SUBTITLE,
    APP_VERSION,
    DEFAULT_WORKBOOK,
)

from core.loader import load_workbook
from core.filters import apply_filters
from core.metrics import kpis
from core.validator import validate_dataset

from dashboard import (
    executive,
    monthly_weekly,
    demand,
    stops,
    times,
    punctuality,
    returns,
    quality,
    scenario_simulator,
    strategic_map,
    time_study,
    comparison,
    stop_optimizer,
)

from reports.report_center import render as render_reports


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

st.set_page_config(
    page_title=f"KOA Analytics V{APP_VERSION}",
    page_icon="🚌",
    layout="wide",
)


# ==========================================================
# ENCABEZADO
# ==========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        {APP_TITLE}
    </h2>

    <p style="margin-top:0;color:#667085;">
        {APP_SUBTITLE} · V{APP_VERSION}
    </p>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# CARGA CACHEADA
# ==========================================================

@st.cache_data(show_spinner=False)
def cached_load(
    path: str,
    app_version: str,
):
    return load_workbook(path)


# ==========================================================
# CARGA DE BASE
# ==========================================================

upload = st.sidebar.file_uploader(
    "Cargar base KOA (.xlsx)",
    type=["xlsx"],
)


try:

    if upload is not None:

        df = load_workbook(
            upload
        )

    else:

        path = Path(
            DEFAULT_WORKBOOK
        )

        if not path.exists():

            path = (
                Path("data")
                / DEFAULT_WORKBOOK
            )

        if not path.exists():

            raise FileNotFoundError(
                f"No se encontró {DEFAULT_WORKBOOK}"
            )

        df = cached_load(
            str(path),
            APP_VERSION,
        )

except Exception as exc:

    st.error(
        f"No fue posible cargar la base: {exc}"
    )

    st.stop()


# ==========================================================
# VALIDACIONES INICIALES
# ==========================================================

if df.empty:

    st.error(
        "La base está vacía."
    )

    st.stop()


if "fecha" not in df.columns:

    st.error(
        "La base no contiene la columna 'fecha'."
    )

    st.stop()


df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce",
)


if df["fecha"].dropna().empty:

    st.error(
        "La base no contiene registros con fechas válidas."
    )

    st.stop()


# ==========================================================
# AUDITORÍA GLOBAL
# ==========================================================

audit_global = validate_dataset(
    df
)


if audit_global.get(
    "issues"
):

    with st.sidebar.expander(
        "⚠️ Alertas generales de calidad"
    ):

        for issue in audit_global["issues"]:

            st.warning(
                issue
            )


# ==========================================================
# FILTRO PRINCIPAL: RANGO DE FECHAS
# ==========================================================

valid_dates = (
    df["fecha"]
    .dropna()
)


date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=(
        valid_dates.min().date(),
        valid_dates.max().date(),
    ),
    min_value=valid_dates.min().date(),
    max_value=valid_dates.max().date(),
)


if (
    isinstance(
        date_range,
        (tuple, list),
    )
    and len(date_range) == 2
):

    start_date = date_range[0]
    end_date = date_range[1]

else:

    start_date = date_range
    end_date = date_range


# ==========================================================
# BASE TEMPORAL SEGÚN RANGO
# ==========================================================

start_ts = pd.Timestamp(
    start_date
)

end_ts = (
    pd.Timestamp(
        end_date
    )
    + pd.Timedelta(
        days=1
    )
)


df_range = df[
    (
        df["fecha"]
        >= start_ts
    )
    &
    (
        df["fecha"]
        < end_ts
    )
].copy()


if df_range.empty:

    st.warning(
        "No existen registros dentro del rango de fechas seleccionado."
    )

    st.stop()


# ==========================================================
# FILTRO MES
# ==========================================================

months = sorted(
    df_range["mes"]
    .dropna()
    .unique()
)


selected_months = st.sidebar.multiselect(
    "Meses",
    months,
    default=months,
    help=(
        "Los meses disponibles corresponden únicamente "
        "al rango de fechas seleccionado."
    ),
)


# ==========================================================
# FILTRO JORNADA
# ==========================================================

jornada_options = sorted(
    df_range["jornada"]
    .dropna()
    .unique()
)


jornadas = st.sidebar.multiselect(
    "Jornada",
    jornada_options,
    default=jornada_options,
)


# ==========================================================
# BASE TEMPORAL SEGÚN JORNADA
# ==========================================================

df_jornada = df_range.copy()


if jornadas:

    df_jornada = df_jornada[
        df_jornada[
            "jornada"
        ].isin(
            jornadas
        )
    ]


# ==========================================================
# FILTRO RECORRIDO
# ==========================================================

ruta_options = sorted(
    df_jornada[
        "recorrido"
    ]
    .dropna()
    .unique()
)


rutas = st.sidebar.multiselect(
    "Recorrido",
    ruta_options,
    default=ruta_options,
)


# ==========================================================
# BASE TEMPORAL SEGÚN RECORRIDO
# ==========================================================

df_ruta = df_jornada.copy()


if rutas:

    df_ruta = df_ruta[
        df_ruta[
            "recorrido"
        ].isin(
            rutas
        )
    ]


# ==========================================================
# FILTRO SEMANA DEL MES
# ==========================================================

weeks = sorted(
    int(x)
    for x
    in df_ruta[
        "numero_semana_mes"
    ]
    .dropna()
    .unique()
)


selected_weeks = st.sidebar.multiselect(
    "Semana del mes",
    weeks,
    default=weeks,
)


# ==========================================================
# FILTRO DÍA DE LA SEMANA
# ==========================================================

weekdays = sorted(
    df_ruta[
        "dia_semana"
    ]
    .dropna()
    .unique()
)


selected_days = st.sidebar.multiselect(
    "Día de la semana",
    weekdays,
    default=weekdays,
)


# ==========================================================
# FILTRO ESTADO OPERATIVO
# ==========================================================

statuses = sorted(
    df_ruta[
        "estado_operativo"
    ]
    .dropna()
    .unique()
)


selected_status = st.sidebar.multiselect(
    "Tipo de recorrido",
    statuses,
    default=statuses,
)


# ==========================================================
# FILTRO PARADEROS / COMBINACIONES
# ==========================================================

invalid_stop_values = {
    "SIN REGISTRO",
    "OTRO",
    "VALIDAR",
}


stop_options = sorted(
    x
    for x
    in df_ruta[
        "combinacion_paradas"
    ]
    .dropna()
    .unique()
    if str(x).strip().upper()
    not in invalid_stop_values
)


selected_stops = st.sidebar.multiselect(
    "Paradero o combinación",
    stop_options,
    default=[],
)


# ==========================================================
# APLICAR FILTROS DEFINITIVOS
# ==========================================================

filtered = apply_filters(
    df=df,
    start_date=start_date,
    end_date=end_date,
    jornadas=jornadas,
    rutas=rutas,
    months=selected_months,
    weeks=selected_weeks,
    weekdays=selected_days,
    stops=selected_stops,
    operation_types=selected_status,
)


if filtered.empty:

    st.warning(
        "No hay registros para los filtros seleccionados."
    )

    st.stop()


# ==========================================================
# AUDITORÍA DEL PERIODO FILTRADO
# ==========================================================

audit_filtered = validate_dataset(
    filtered
)


# ==========================================================
# INFORMACIÓN DEL PERIODO ACTIVO
# ==========================================================

st.caption(
    f"""
    Periodo activo: 
    **{pd.Timestamp(start_date).strftime('%d/%m/%Y')}**
    al
    **{pd.Timestamp(end_date).strftime('%d/%m/%Y')}**
    · Registros filtrados: **{len(filtered):,}**
    """
)


# ==========================================================
# KPI
# ==========================================================

m = kpis(
    filtered
)


def pct(value):

    return (
        "N/D"
        if pd.isna(value)
        else f"{value:.1%}"
    )


def mins(value):

    return (
        "N/D"
        if pd.isna(value)
        else f"{value:.1f} min"
    )


# ==========================================================
# KPI FILA 1
# ==========================================================

row1 = st.columns(
    8
)


metrics_row1 = [
    (
        "Registros",
        m["registros"],
    ),
    (
        "Días",
        m["dias"],
    ),
    (
        "Usuarios",
        m["usuarios"],
    ),
    (
        "Recorridos efectivos",
        m["efectivos"],
    ),
    (
        "Puntualidad general",
        pct(
            m[
                "puntualidad_general"
            ]
        ),
    ),
    (
        "Puntualidad mañana",
        pct(
            m[
                "puntualidad_manana"
            ]
        ),
    ),
    (
        "Puntualidad tarde",
        pct(
            m[
                "puntualidad_tarde"
            ]
        ),
    ),
    (
        "Retrasos",
        pct(
            m[
                "retrasos"
            ]
        ),
    ),
]


for col, (
    label,
    value,
) in zip(
    row1,
    metrics_row1,
):

    col.metric(
        label,
        value,
    )


# ==========================================================
# KPI FILA 2
# ==========================================================

row2 = st.columns(
    8
)


metrics_row2 = [
    (
        "Tiempo promedio",
        mins(
            m[
                "tiempo_efectivo_promedio"
            ]
        ),
    ),
    (
        "Mediana",
        mins(
            m[
                "tiempo_mediana"
            ]
        ),
    ),
    (
        "P80",
        mins(
            m[
                "tiempo_p80"
            ]
        ),
    ),
    (
        "P90",
        mins(
            m[
                "tiempo_efectivo_p90"
            ]
        ),
    ),
    (
        "P95",
        mins(
            m[
                "tiempo_p95"
            ]
        ),
    ),
    (
        "Anticipadas",
        pct(
            m[
                "anticipadas"
            ]
        ),
    ),
    (
        "Tiempo recorrido",
        mins(
            m[
                "tiempo_total_recorrido"
            ]
        ),
    ),
    (
        "Tiempo detenido",
        mins(
            m[
                "tiempo_total_espera"
            ]
        ),
    ),
]


for col, (
    label,
    value,
) in zip(
    row2,
    metrics_row2,
):

    col.metric(
        label,
        value,
    )


# ==========================================================
# REGLA OPERATIVA
# ==========================================================

st.caption(
    """
    Regla oficial: mañana y tarde con espera autorizada de hasta 5 minutos.
    La puntualidad general es ponderada por registros válidos,
    no el promedio simple de jornadas.
    """
)


# ==========================================================
# PESTAÑAS
# ==========================================================

tabs = st.tabs(
    [
        "Resumen ejecutivo",
        "Mensual y semanal",
        "Demanda",
        "Paraderos",
        "Mapa estratégico",
        "Combinaciones y tiempos",
        "Estudio de tiempos",
        "Puntualidad",
        "Retorno",
        "Calidad",
        "Simulador operativo",
        "Optimizador de paraderos",
        "Antes vs. después",
        "Informes",
        "Auditoría y detalle",
    ]
)


# ==========================================================
# RENDER PESTAÑAS
# ==========================================================

with tabs[0]:

    executive.render(
        filtered
    )


with tabs[1]:

    monthly_weekly.render(
        filtered
    )


with tabs[2]:

    demand.render(
        filtered
    )


with tabs[3]:

    stops.render(
        filtered
    )


with tabs[4]:

    strategic_map.render(
        filtered
    )


with tabs[5]:

    times.render(
        filtered
    )


with tabs[6]:

    time_study.render(
        filtered
    )


with tabs[7]:

    punctuality.render(
        filtered
    )


with tabs[8]:

    returns.render(
        filtered
    )


with tabs[9]:

    quality.render(
        filtered
    )


with tabs[10]:

    scenario_simulator.render(
        filtered
    )


with tabs[11]:

    stop_optimizer.render(
        filtered
    )


with tabs[12]:

    comparison.render(
        filtered
    )


with tabs[13]:

    render_reports(
        filtered
    )


# ==========================================================
# AUDITORÍA Y DETALLE
# ==========================================================

with tabs[14]:

    st.subheader(
        "Auditoría matemática y detalle"
    )

    st.markdown(
        f"""
        **Periodo analizado:**  
        {pd.Timestamp(start_date).strftime('%d/%m/%Y')}
        al
        {pd.Timestamp(end_date).strftime('%d/%m/%Y')}

        **Registros incluidos:**  
        {len(filtered):,}
        """
    )


    st.markdown(
        "### Auditoría del periodo filtrado"
    )

    st.json(
        audit_filtered
    )


    st.markdown(
        """
        ### Reglas auditadas

        - Mañana: anticipada `< 0`; puntual entre `0 y 5`; retrasada `> 5` minutos.
        - Tarde: anticipada `< 0`; puntual entre `0 y 5`; retrasada `> 5` minutos.
        - Paraderos: se leen exclusivamente de `PARADAS`.
        - OXXO HÉROES corresponde a un solo punto en la mañana.
        - Tiempo efectivo: recorridos efectivos con duración válida entre 0 y 240 minutos.
        - P80, P90 y P95: percentiles calculados únicamente con tiempos efectivos válidos.
        - Los mapas y simulaciones son exploratorios y requieren validación de campo y piloto.
        """
    )


    st.markdown(
        "### Detalle de registros filtrados"
    )

    st.dataframe(
        filtered,
        hide_index=True,
        use_container_width=True,
    )

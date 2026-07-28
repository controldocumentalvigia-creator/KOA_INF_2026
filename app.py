from pathlib import Path
import pandas as pd
import streamlit as st

from config import APP_TITLE, APP_SUBTITLE, APP_VERSION, DEFAULT_WORKBOOK
from core.loader import load_workbook
from core.filters import apply_filters
from core.metrics import kpis
from core.validator import validate_dataset
from dashboard import (
    executive, monthly_weekly, demand, stops, times, punctuality, returns,
    quality, scenario_simulator, strategic_map, time_study, comparison, stop_optimizer,
)
from reports.report_center import render as render_reports

st.set_page_config(page_title=f"KOA Analytics V{APP_VERSION}", page_icon="🚌", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
[data-testid="stSidebar"] {background:#eef3f9;}
.koa-title {background:linear-gradient(90deg,#123d76,#1d5da7);color:white;padding:18px 22px;border-radius:12px;margin-bottom:14px;}
.koa-title h1 {margin:0;font-size:29px;}.koa-title p {margin:4px 0 0 0;opacity:.92;}
div[data-testid="stMetric"] {background:white;border:1px solid #dce4ed;border-radius:10px;padding:10px;}
</style>
""", unsafe_allow_html=True)
st.markdown(f'<div class="koa-title"><h1>{APP_TITLE}</h1><p>{APP_SUBTITLE} · V{APP_VERSION}</p></div>', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def cached_load(path: str):
    return load_workbook(path)

upload = st.sidebar.file_uploader("Cargar base KOA (.xlsx)", type=["xlsx"])
try:
    if upload is not None:
        df = load_workbook(upload)
    else:
        path = Path(DEFAULT_WORKBOOK)
        if not path.exists(): path = Path("data") / DEFAULT_WORKBOOK
        if not path.exists(): raise FileNotFoundError(f"No se encontró {DEFAULT_WORKBOOK}")
        df = cached_load(str(path))
except Exception as exc:
    st.error(f"No fue posible cargar la base: {exc}")
    st.stop()

if df.empty or df["fecha"].dropna().empty:
    st.error("La base no contiene registros con fechas válidas.")
    st.stop()

audit = validate_dataset(df)
if audit.get("issues"):
    with st.sidebar.expander("Alertas de calidad"):
        for issue in audit["issues"]: st.warning(issue)

valid_dates = df["fecha"].dropna()
date_range = st.sidebar.date_input("Rango de fechas", value=(valid_dates.min().date(), valid_dates.max().date()), min_value=valid_dates.min().date(), max_value=valid_dates.max().date())
start_date, end_date = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (date_range, date_range)

months = sorted(df["mes"].dropna().unique())
selected_months = st.sidebar.multiselect("Meses", months, default=months)
jornadas = st.sidebar.multiselect("Jornada", sorted(df["jornada"].dropna().unique()), default=sorted(df["jornada"].dropna().unique()))
rutas = st.sidebar.multiselect("Recorrido", sorted(df["recorrido"].dropna().unique()), default=sorted(df["recorrido"].dropna().unique()))
weeks = sorted(int(x) for x in df["numero_semana_mes"].dropna().unique())
selected_weeks = st.sidebar.multiselect("Semana del mes", weeks, default=weeks)
weekdays = sorted(df["dia_semana"].dropna().unique())
selected_days = st.sidebar.multiselect("Día de la semana", weekdays, default=weekdays)
statuses = sorted(df["estado_operativo"].dropna().unique())
selected_status = st.sidebar.multiselect("Tipo de recorrido", statuses, default=statuses)
stop_options = sorted(x for x in df["combinacion_paradas"].dropna().unique() if x not in ["SIN REGISTRO", "OTRO", "VALIDAR"])
selected_stops = st.sidebar.multiselect("Paradero o combinación", stop_options, default=[])

filtered = apply_filters(df, start_date, end_date, jornadas, rutas, selected_months, selected_weeks, selected_days, selected_stops, selected_status)
if filtered.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

m = kpis(filtered)
def pct(value): return "N/D" if pd.isna(value) else f"{value:.1%}"
def mins(value): return "N/D" if pd.isna(value) else f"{value:.1f} min"

row1 = st.columns(8)
for col, (label, value) in zip(row1, [
    ("Registros", m["registros"]), ("Días", m["dias"]), ("Usuarios", m["usuarios"]),
    ("Recorridos efectivos", m["efectivos"]), ("Puntualidad general", pct(m["puntualidad_general"])),
    ("Puntualidad mañana", pct(m["puntualidad_manana"])), ("Puntualidad tarde", pct(m["puntualidad_tarde"])),
    ("Retrasos", pct(m["retrasos"])),
]): col.metric(label, value)
row2 = st.columns(8)
for col, (label, value) in zip(row2, [
    ("Tiempo promedio", mins(m["tiempo_efectivo_promedio"])), ("Mediana", mins(m["tiempo_mediana"])),
    ("P80", mins(m["tiempo_p80"])), ("P90", mins(m["tiempo_efectivo_p90"])),
    ("P95", mins(m["tiempo_p95"])), ("Anticipadas", pct(m["anticipadas"])),
    ("Tiempo recorrido", mins(m["tiempo_total_recorrido"])), ("Tiempo detenido", mins(m["tiempo_total_espera"])),
]): col.metric(label, value)

st.caption("Regla oficial: mañana y tarde con espera autorizada de hasta 5 minutos. La puntualidad general es ponderada por registros válidos, no el promedio simple de jornadas.")

tabs = st.tabs([
    "Resumen ejecutivo", "Mensual y semanal", "Demanda", "Paraderos", "Mapa estratégico",
    "Combinaciones y tiempos", "Estudio de tiempos", "Puntualidad", "Retorno", "Calidad",
    "Simulador operativo", "Optimizador de paraderos", "Antes vs. después", "Informes", "Auditoría y detalle",
])
with tabs[0]: executive.render(filtered)
with tabs[1]: monthly_weekly.render(filtered)
with tabs[2]: demand.render(filtered)
with tabs[3]: stops.render(filtered)
with tabs[4]: strategic_map.render(filtered)
with tabs[5]: times.render(filtered)
with tabs[6]: time_study.render(filtered)
with tabs[7]: punctuality.render(filtered)
with tabs[8]: returns.render(filtered)
with tabs[9]: quality.render(filtered)
with tabs[10]: scenario_simulator.render(filtered)
with tabs[11]: stop_optimizer.render(filtered)
with tabs[12]: comparison.render(filtered)
with tabs[13]: render_reports(filtered)
with tabs[14]:
    st.subheader("Auditoría matemática y detalle")
    st.json(audit)
    st.markdown("""
**Reglas auditadas**
- Mañana: anticipada `< 0`; puntual entre `0 y 5`; retrasada `> 5` minutos.
- Tarde: anticipada `< 0`; puntual `0 a 5`; retrasada `> 5` minutos.
- Paraderos: se leen exclusivamente de `PARADAS`. OXXO HÉROES es un solo punto de mañana.
- Tiempo efectivo: recorridos efectivos con duración válida entre 0 y 240 minutos.
- P80, P90 y P95: percentiles de tiempos efectivos válidos.
- Los mapas y simulaciones son exploratorios; exigen validación de campo y piloto.
""")
    st.dataframe(filtered, hide_index=True, use_container_width=True)


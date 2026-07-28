from __future__ import annotations
import pandas as pd
import pydeck as pdk
import streamlit as st
from maps.geo import DEFAULT_KOA, CURRENT_STOPS, TRANSMILENIO_STATIONS, candidates_table


def render(_: pd.DataFrame | None = None) -> None:
    st.subheader("Mapa estratégico de paraderos y TransMilenio")
    st.caption("Las coordenadas son referencias editables. Valide en campo seguridad, acceso peatonal, señalización y restricciones viales antes de implementar una propuesta.")

    c1, c2 = st.columns(2)
    koa_lat = c1.number_input("Latitud KOA", value=float(DEFAULT_KOA["lat"]), format="%.6f")
    koa_lon = c2.number_input("Longitud KOA", value=float(DEFAULT_KOA["lon"]), format="%.6f")

    candidates = candidates_table(koa_lat, koa_lon)
    default_names = candidates.head(3)["Alternativa"].tolist()
    selected_names = st.multiselect("Propuestas para comparar", candidates["Alternativa"].tolist(), default=default_names, max_selections=5)
    radius = st.select_slider("Radio de cobertura alrededor de KOA", [300, 500, 800, 1000], value=500)
    show_current = st.checkbox("Mostrar paraderos actuales", True)
    show_stations = st.checkbox("Mostrar estaciones de TransMilenio", True)

    koa_df = pd.DataFrame([{"name": "KOA", "type": "Sede", "lat": koa_lat, "lon": koa_lon}])
    layers = [
        pdk.Layer("ScatterplotLayer", koa_df, get_position="[lon,lat]", get_radius=90, get_fill_color=[18,61,118,230], pickable=True),
        pdk.Layer("ScatterplotLayer", koa_df, get_position="[lon,lat]", get_radius=radius, stroked=True, filled=False, get_line_color=[18,61,118,130], line_width_min_pixels=2),
    ]
    if show_current:
        layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame(CURRENT_STOPS), get_position="[lon,lat]", get_radius=65, get_fill_color=[245,158,11,220], pickable=True))
    if show_stations:
        layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame(TRANSMILENIO_STATIONS), get_position="[lon,lat]", get_radius=60, get_fill_color=[220,38,38,210], pickable=True))
    if selected_names:
        proposed = pd.DataFrame([p for p in TRANSMILENIO_STATIONS if p["name"] in selected_names])
        layers.append(pdk.Layer("ScatterplotLayer", proposed, get_position="[lon,lat]", get_radius=85, get_fill_color=[22,163,74,235], pickable=True))

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=koa_lat, longitude=koa_lon, zoom=13.7),
        layers=layers,
        tooltip={"html": "<b>{name}</b><br>{type}"},
    )
    st.pydeck_chart(deck, use_container_width=True)
    st.markdown("### Ranking de alternativas")
    view = candidates[candidates["Alternativa"].isin(selected_names)] if selected_names else candidates.head(3)
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.info("La distancia es lineal, no reemplaza una medición peatonal real. La propuesta final debe validarse mediante visita de campo y prueba piloto.")

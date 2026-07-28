import numpy as np
import pandas as pd


def evaluate_scenario(df, route, selected_stops, demand_adjustment=0, added_minutes=0):
    effective = df[
        (df["jornada"] == "TARDE")
        & (df["estado_operativo"] == "EFECTIVO")
        & (df["recorrido"] == route)
    ].copy()
    selected = [stop.upper() for stop in selected_stops]
    exact = effective[
        effective["combinacion_paradas"].map(
            lambda value: all(stop in value for stop in selected)
        )
    ]
    evidence_n = len(exact)
    base = exact if evidence_n >= 3 else effective
    expected = base["trayecto"].mean() + added_minutes if len(base) else np.nan
    p90 = base["trayecto"].quantile(.90) + added_minutes if len(base) else np.nan
    expected_users = max(0, base["usuarios"].mean() * (1 + demand_adjustment / 100)) if len(base) else np.nan
    evidence = "Alta" if evidence_n >= 20 else "Media" if evidence_n >= 5 else "Baja"
    return {
        "ruta": route,
        "configuracion": " + ".join(selected),
        "observaciones_directas": evidence_n,
        "evidencia": evidence,
        "tiempo_esperado": expected,
        "p90": p90,
        "usuarios_esperados": expected_users,
        "nota": "Estimación exploratoria; validar mediante piloto cuando la evidencia sea baja.",
    }


def clock_to_minutes(value: str) -> int:
    """Convierte HH:MM a minutos desde medianoche."""
    hour, minute = [int(part) for part in value.split(":")]
    return hour * 60 + minute


def minutes_to_clock(value: float) -> str:
    """Convierte minutos desde medianoche a HH:MM, controlando cambio de día."""
    total = int(round(value)) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def analyze_operating_window(
    departures,
    shift_end_times,
    outbound_minutes=15,
    return_minutes=15,
    minimum_positioning_minutes=5,
):
    """
    Analiza la secuencia de un único vehículo.

    Reglas:
    - El vehículo sale de KOA en la hora programada.
    - La ida y el retorno conforman el tiempo de ciclo.
    - El margen operativo es la siguiente salida menos el retorno de la ruta anterior.
    - Para considerar viable la secuencia se exige al menos un margen mínimo de
      posicionamiento antes de la siguiente salida.
    """
    cycle = outbound_minutes + return_minutes
    rows = []
    previous_return = None

    for index, (departure_text, shift_end_text) in enumerate(zip(departures, shift_end_times), start=1):
        departure = clock_to_minutes(departure_text)
        shift_end = clock_to_minutes(shift_end_text)
        arrival_destination = departure + outbound_minutes
        return_origin = departure + cycle
        boarding_window = departure - shift_end

        if previous_return is None:
            positioning_margin = np.nan
            status = "INICIO DE OPERACIÓN"
        else:
            positioning_margin = departure - previous_return
            if positioning_margin >= minimum_positioning_minutes:
                status = "VIABLE"
            elif positioning_margin >= 0:
                status = "SIN HOLGURA"
            else:
                status = "SOLAPAMIENTO"

        rows.append({
            "recorrido": f"R{index}",
            "fin_jornada_usuarios": shift_end_text,
            "salida_programada": departure_text,
            "espera_usuarios_min": boarding_window,
            "llegada_destino": minutes_to_clock(arrival_destination),
            "retorno_KOA": minutes_to_clock(return_origin),
            "ciclo_min": cycle,
            "margen_antes_siguiente_min": positioning_margin,
            "estado": status,
            "inicio_min": departure,
            "fin_ida_min": arrival_destination,
            "fin_ciclo_min": return_origin,
        })
        previous_return = return_origin

    frame = pd.DataFrame(rows)
    valid_margins = frame["margen_antes_siguiente_min"].dropna()
    minimum_margin = valid_margins.min() if len(valid_margins) else np.nan
    is_viable = bool((valid_margins >= minimum_positioning_minutes).all()) if len(valid_margins) else True
    total_window = frame.iloc[-1]["fin_ciclo_min"] - frame.iloc[0]["inicio_min"] if len(frame) else 0

    summary = {
        "tiempo_ciclo_min": cycle,
        "tiempo_total_tres_recorridos_min": cycle * len(frame),
        "ventana_desde_primera_salida_hasta_ultimo_retorno_min": total_window,
        "margen_minimo_min": minimum_margin,
        "margen_requerido_min": minimum_positioning_minutes,
        "viable_un_vehiculo": is_viable,
    }
    return frame, summary


def analyze_historical_schedule(
    df,
    departures=("17:10", "17:45", "18:15"),
    minimum_positioning_minutes=5,
):
    """
    Compara la duración histórica real de cada recorrido de la tarde con el
    intervalo asignado hasta la siguiente salida.

    Para R1 y R2 calcula:
    - intervalo programado hasta la siguiente ruta;
    - promedio, mediana, P90 y P95 del tiempo real;
    - margen promedio y margen P90;
    - porcentaje de recorridos que retornan antes de la siguiente salida;
    - porcentaje que conserva el margen mínimo de posicionamiento.

    R3 no tiene una salida posterior dentro de la secuencia, por lo cual se
    presenta su duración histórica sin evaluar margen posterior.
    """
    effective = df[
        (df["jornada"] == "TARDE")
        & (df["estado_operativo"] == "EFECTIVO")
        & df["trayecto"].notna()
        & (df["trayecto"] > 0)
    ].copy()

    departure_minutes = [clock_to_minutes(value) for value in departures]
    rows = []

    for index, route in enumerate(["R1", "R2", "R3"]):
        sample = effective.loc[effective["recorrido"] == route, "trayecto"].dropna()
        n = len(sample)
        mean = sample.mean() if n else np.nan
        median = sample.median() if n else np.nan
        p90 = sample.quantile(.90) if n else np.nan
        p95 = sample.quantile(.95) if n else np.nan
        maximum = sample.max() if n else np.nan

        if index < len(departure_minutes) - 1:
            interval = departure_minutes[index + 1] - departure_minutes[index]
            required_limit = interval - minimum_positioning_minutes
            return_before_next = (sample <= interval).mean() if n else np.nan
            return_with_margin = (sample <= required_limit).mean() if n else np.nan
            average_margin = interval - mean if n else np.nan
            p90_margin = interval - p90 if n else np.nan
            average_status = (
                "VIABLE" if average_margin >= minimum_positioning_minutes
                else "SIN HOLGURA" if average_margin >= 0
                else "SOLAPAMIENTO"
            ) if n else "SIN DATOS"
            p90_status = (
                "VIABLE" if p90_margin >= minimum_positioning_minutes
                else "SIN HOLGURA" if p90_margin >= 0
                else "SOLAPAMIENTO"
            ) if n else "SIN DATOS"
            next_departure = departures[index + 1]
        else:
            interval = np.nan
            required_limit = np.nan
            return_before_next = np.nan
            return_with_margin = np.nan
            average_margin = np.nan
            p90_margin = np.nan
            average_status = "ÚLTIMO RECORRIDO"
            p90_status = "ÚLTIMO RECORRIDO"
            next_departure = "N/A"

        rows.append({
            "recorrido": route,
            "salida_programada": departures[index],
            "siguiente_salida": next_departure,
            "intervalo_asignado_min": interval,
            "observaciones": n,
            "tiempo_promedio_real_min": mean,
            "mediana_real_min": median,
            "p90_real_min": p90,
            "p95_real_min": p95,
            "maximo_real_min": maximum,
            "margen_promedio_min": average_margin,
            "margen_p90_min": p90_margin,
            "cumple_antes_siguiente_pct": return_before_next,
            "cumple_margen_minimo_pct": return_with_margin,
            "estado_promedio": average_status,
            "estado_p90": p90_status,
            "inicio_min": departure_minutes[index],
            "fin_promedio_min": departure_minutes[index] + mean if n else np.nan,
            "fin_p90_min": departure_minutes[index] + p90 if n else np.nan,
        })

    return pd.DataFrame(rows)

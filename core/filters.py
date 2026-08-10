from __future__ import annotations

from typing import Iterable
import pandas as pd

from core.utils import norm


def apply_filters(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    jornadas: Iterable[str] | None = None,
    rutas: Iterable[str] | None = None,
    months: Iterable[str] | None = None,
    weeks: Iterable[int] | None = None,
    weekdays: Iterable[str] | None = None,
    stops: Iterable[str] | None = None,
    operation_types: Iterable[str] | None = None,
) -> pd.DataFrame:

    data = df.copy()

    # ==========================================================
    # 1. ASEGURAR FECHA VÁLIDA
    # ==========================================================
    data["fecha"] = pd.to_datetime(
        data["fecha"],
        errors="coerce"
    )

    mask = pd.Series(True, index=data.index)

    # ==========================================================
    # 2. FILTRO PRINCIPAL POR FECHA
    # ==========================================================
    if start_date is not None:
        start_ts = pd.Timestamp(start_date)

        mask &= data["fecha"] >= start_ts

    if end_date is not None:
        # Se usa el inicio del día siguiente como límite exclusivo.
        # Así incluye TODO el día final aunque fecha tenga hora.
        end_ts = (
            pd.Timestamp(end_date)
            + pd.Timedelta(days=1)
        )

        mask &= data["fecha"] < end_ts

    # ==========================================================
    # 3. JORNADA
    # ==========================================================
    if jornadas:
        mask &= data["jornada"].isin(
            list(jornadas)
        )

    # ==========================================================
    # 4. RECORRIDO
    # ==========================================================
    if rutas:
        mask &= data["recorrido"].isin(
            list(rutas)
        )

    # ==========================================================
    # 5. MES
    # ==========================================================
    if months:
        mask &= data["mes"].isin(
            list(months)
        )

    # ==========================================================
    # 6. SEMANA DEL MES
    # ==========================================================
    if weeks:
        mask &= data["numero_semana_mes"].isin(
            list(weeks)
        )

    # ==========================================================
    # 7. DÍA DE LA SEMANA
    # ==========================================================
    if weekdays:
        mask &= data["dia_semana"].isin(
            list(weekdays)
        )

    # ==========================================================
    # 8. TIPO DE OPERACIÓN
    # ==========================================================
    if operation_types:
        mask &= data["estado_operativo"].isin(
            list(operation_types)
        )

    # ==========================================================
    # 9. PARADEROS
    # ==========================================================
    # Se conserva la lógica original porque una combinación
    # puede contener más de un paradero:
    # "VIRREY + HÉROES + POLO"
    #
    # Si el usuario selecciona "VIRREY", debe encontrar también
    # registros donde VIRREY forme parte de una combinación.
    if stops:

        selected = {
            norm(x)
            for x in stops
            if pd.notna(x)
        }

        mask &= data["combinacion_paradas"].fillna("").map(
            lambda x: any(
                item in norm(x)
                for item in selected
            )
        )

    # ==========================================================
    # 10. RESULTADO
    # ==========================================================
    return (
        data.loc[mask]
        .copy()
        .reset_index(drop=True)
    )

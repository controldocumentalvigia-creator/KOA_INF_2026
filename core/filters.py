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
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= df["fecha"] >= pd.Timestamp(start_date)
    if end_date is not None:
        mask &= df["fecha"] <= pd.Timestamp(end_date)
    if jornadas:
        mask &= df["jornada"].isin(list(jornadas))
    if rutas:
        mask &= df["recorrido"].isin(list(rutas))
    if months:
        mask &= df["mes"].isin(list(months))
    if weeks:
        mask &= df["numero_semana_mes"].isin(list(weeks))
    if weekdays:
        mask &= df["dia_semana"].isin(list(weekdays))
    if operation_types:
        mask &= df["estado_operativo"].isin(list(operation_types))
    if stops:
        selected = {norm(x) for x in stops}
        mask &= df["combinacion_paradas"].map(
            lambda x: any(item in norm(x) for item in selected)
        )
    return df.loc[mask].copy()

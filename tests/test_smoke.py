from pathlib import Path
from core.loader import load_workbook
from core.metrics import kpis, monthly_summary, weekly_summary, stop_frequency


def test_load_and_metrics():
    path = Path("Dinamica_de_paraderos_KOA_ES.xlsx")
    df = load_workbook(path)
    assert len(df) > 0
    assert kpis(df)["registros"] == len(df)
    assert not monthly_summary(df).empty
    assert not weekly_summary(df).empty
    assert len(stop_frequency(df)) == 4

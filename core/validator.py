import pandas as pd

def validate_dataset(df: pd.DataFrame) -> dict:
    issues = []
    if df.empty:
        issues.append("La base no contiene registros.")
    if df["fecha"].isna().any():
        issues.append(f"{int(df['fecha'].isna().sum())} filas sin fecha válida.")
    if df["recorrido"].eq("").any():
        issues.append(f"{int(df['recorrido'].eq('').sum())} filas sin recorrido.")
    if df["jornada"].eq("").any():
        issues.append(f"{int(df['jornada'].eq('').sum())} filas sin jornada.")
    if (df["usuarios"] < 0).any():
        issues.append("Existen valores negativos en usuarios.")
    return {
        "ok": not issues,
        "issues": issues,
        "rows": len(df),
        "valid_dates": int(df["fecha"].notna().sum()),
        "valid_punctuality": int(df["desv_min"].notna().sum()),
        "effective_afternoon": int(((df["jornada"] == "TARDE") & (df["estado_operativo"] == "EFECTIVO")).sum()),
    }

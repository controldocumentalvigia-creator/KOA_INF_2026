from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from core.metrics import kpis, monthly_summary, stop_frequency
from ai.conclusions import generate_conclusions

def _table_data(df):
    return [list(df.columns)] + [[str(v) for v in row] for row in df.values.tolist()]

def build_pdf(df) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("INFORME EJECUTIVO - KOA", styles["Title"]),
        Paragraph(f"Periodo: {df['fecha'].min():%d/%m/%Y} al {df['fecha'].max():%d/%m/%Y}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Resumen ejecutivo", styles["Heading1"]),
    ]
    for item in generate_conclusions(df):
        story.append(Paragraph(f"- {item}", styles["BodyText"]))
        story.append(Spacer(1, 4))

    for title, frame in [
        ("Indicadores principales", __import__("pandas").DataFrame([kpis(df)])),
        ("Análisis mensual", monthly_summary(df)),
        ("Frecuencia de paraderos", stop_frequency(df)),
    ]:
        story += [Spacer(1, 10), Paragraph(title, styles["Heading1"])]
        table = Table(_table_data(frame), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#123D76")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), .5, colors.grey),
            ("FONTSIZE", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(table)
    doc.build(story)
    return output.getvalue()

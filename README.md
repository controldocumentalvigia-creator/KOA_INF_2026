# KOA Analytics V5.0

Aplicación Streamlit para estudios de tiempos, puntualidad diferenciada por jornada, demanda, uso de paraderos, retorno del vehículo, simulación de horarios, optimización de combinaciones y mapa estratégico.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Despliegue en Streamlit Cloud

- Branch: `main`
- Main file path: `app.py`
- Python recomendado: 3.11

## Estructura

- `core/`: carga, validación, filtros y matemática.
- `dashboard/`: visualizaciones y pestañas.
- `maps/`: coordenadas y cálculos geográficos.
- `simulator/`: motores de escenarios.
- `ai/`: conclusiones y recomendaciones basadas en datos.
- `reports/`: exportación Excel, Word, PowerPoint y PDF.
- `tests/`: pruebas automáticas.

Las coordenadas del mapa son referencias editables y requieren validación en campo.

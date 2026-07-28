# Auditoría matemática — KOA Analytics V5.0

## Puntualidad

La desviación se calcula como `hora real de salida - hora programada`.

- **Mañana:** anticipada `< 0`; puntual `= 0`; retrasada `> 0`.
- **Tarde:** anticipada `< 0`; puntual entre `0 y 5`; retrasada `> 5`.
- La puntualidad general se calcula con todos los registros válidos: `salidas puntuales / registros válidos`. No es el promedio simple de los porcentajes por jornada.
- Se excluyen horas ausentes y desviaciones absolutas superiores a 180 minutos.

## Tiempos

- Solo se utilizan recorridos clasificados como **EFECTIVO**.
- Se excluyen duraciones menores a 1 minuto y mayores a 240 minutos.
- Se reportan promedio, mediana, moda, P80, P90, P95, desviación estándar, mínimo y máximo.

## Paraderos

- La única fuente es la columna `PARADAS`.
- Mañana: **OXXO HÉROES** es un solo punto operacional.
- Tarde: **VIRREY, HÉROES y POLO**.
- Una combinación como `VIRREY + POLO` cuenta uso de ambos paraderos, no crea un cuarto paradero.

## Simuladores y mapa

Los escenarios, ahorros y distancias son exploratorios. Deben validarse mediante visita de campo, medición peatonal real y prueba piloto antes de una decisión operacional.

# REPORTE: AUDITORÍA Y VALIDACIÓN DE DATOS (QUESTION 1)
**Proyecto:** Integración y Consistencia del Data Warehouse de Logística - LATAM Last Mile  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 27 de mayo de 2026  

---

## 📋 Resumen Ejecutivo
Para responder de manera precisa y exhaustiva a la **Pregunta 1**, este reporte consolida los hallazgos de calidad de datos tanto para las tablas históricas de control (`routes` y `shipments`) como para las tablas de producción activas (`routes_new` y `shipments_new`). 

El análisis comparativo revela que mientras las tablas de control mantenían una integridad de clave sólida, el incremento de volumen en las tablas de producción introdujo fallos severos de duplicidad, registros cronológicos físicos invertidos y corrupción en marcas de tiempo. A continuación se detallan los hallazgos, formas de descubrimiento, riesgos y estrategias de mitigación.

---

## 🔍 1. Hallazgos de la Auditoría y Comparación de Tablas

### A. Integridad de Claves Primarias (PK Duplication)
* **Tablas Afectadas**: `shipments` y `shipments_new`
* **Hallazgos**:
  * **`shipments` (Control)**: **0 duplicados**. Integridad de clave primaria de 100% sobre los registros de control históricos.
  * **`shipments_new` (Producción)**: **443,423 llaves duplicadas (7.95%)** sobre un total de 5,579,971 registros.
* **Cómo se descubrió**: Ejecutando consultas de agregación que restan el total de filas del conteo de llaves únicas:
  ```sql
  SELECT COUNT(shipment_id) - COUNT(DISTINCT shipment_id) FROM table
  ```
* **Estrategia de Mitigación**:
  Para queries que utilicen `shipments_new`, es obligatorio utilizar una Expresión de Tabla Común (CTE) de deduplicación dinámica con `ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)` para aislar el estado final del paquete y reducir la duplicidad a 0%.
* **Riesgo Operativo**: No aplicar la deduplicación infla artificialmente el volumen de despachos un 8%, alterando a la baja la efectividad real de entregas e impactando la facturación.

### B. Consistencia de Tiempos y Cronología en Rutas
* **Tablas Afectadas**: `routes` y `routes_new`
* **Hallazgos**:
  * **`routes` (Control)**: **0 violaciones cronológicas**. Los tiempos de inicio y fin real son consistentes.
  * **`routes_new` (Producción)**: **20,756 rutas completadas (17.40%)** presentan marcas de tiempo invertidas, donde la hora de finalización ocurre antes que la hora de inicio en la misma fecha (ej. inicia 22:09 y termina 20:07).
* **Cómo se descubrió**: Comparando la relación física temporal en BigQuery:
  ```sql
  COUNTIF(actual_route_end_time < actual_route_start_time)
  ```
* **Estrategia de Mitigación**:
  Excluir las 20,756 rutas corruptas del análisis de OTH por duración en BigQuery. El análisis general de tiempos de viaje debe usar filtros para excluir duraciones negativas.
* **Riesgo Operativo**: Calcular la duración del viaje incluyendo registros con cronología invertida produce duraciones negativas, distorsionando los promedios globales de tránsito de la flota.

### C. Doble Asignación y Solapamiento de Rutas (Route Overlaps)
* **Tablas Afectadas**: `routes` y `routes_new`
* **Hallazgos**:
  * **`routes` (Control)**: **2,103 solapamientos** de rutas.
  * **`routes_new` (Producción)**: **62,549 solapamientos** de rutas operadas por el mismo transportista el mismo día con horarios concurrentes.
* **Cómo se descubrió**: Realizando una auto-unión (`self-join`) por transportista y fecha, evaluando si el intervalo de una ruta se superpone con otra:
  ```sql
  ON r1.partner_id = r2.partner_id AND r1.route_date = r2.route_date
  WHERE r2.actual_route_start_time < r1.actual_route_end_time AND r2.actual_route_end_time > r1.actual_route_start_time
  ```
* **Estrategia de Mitigación**:
  Verificar si los solapamientos corresponden a carriers nacionales que operan en múltiples hubs (ej. el caso de PT-014 en Sao Paulo y Río). En el caso de socios urbanos locales, clasificarlos como fallos del GPS y tratarlos por separado en BI.
* **Riesgo Operativo**: Infla la flota activa reportada en el tablero de BI al asumir que cada ruta corresponde a un chofer único en tránsito.

### D. Inflación y Discrepancias de Paradas (Stops Inflation)
* **Tablas Afectadas**: `routes` y `routes_new`
* **Hallazgos**:
  * **`routes` (Control)**: **797 rutas** registran paradas reales (`actual_stops`) que exceden por **más del 50%** a las estimadas (`estimated_stops`).
  * **`routes_new` (Producción)**: Tasa de discrepancia normal, pero presenta **2,425 rutas sin transportista asignado (2.03%)** y **3,578 sin vehículo asignado (3.00%)**.
* **Cómo se descubrió**: Comparando paradas estimadas vs reales:
  ```sql
  COUNTIF(actual_stops > estimated_stops * 1.5)
  ```
* **Estrategia de Mitigación**:
  Excluir paradas infladas en la auditoría contractual de carriers. Agrupar rutas sin vehículo o transportista bajo etiquetas de "Recurso No Asignado".
* **Riesgo Operativo**: Posibles sobrecostos y fraude por reclamos de paradas adicionales no planificadas presentados por subcontratistas.

### E. Corrupción en Logs Horarios (Log Hour Corruption)
* **Tablas Afectadas**: `shipment_events` y `shipment_events_new`
* **Hallazgos**:
  * **`shipment_events` (Control)**: **174,672 registros corruptos (60.70%)**.
  * **`shipment_events_new` (Producción)**: **6,227,543 registros corruptos (85.29%)** donde el campo `event_hour_utc` está forzado a `0` para eventos que ocurren entre las 20:00 y las 23:59 UTC.
* **Cómo se descubrió**: Auditando la igualdad entre el campo entero nativo y el timestamp original (`event_hour_utc != EXTRACT(HOUR FROM event_timestamp)`).
* **Estrategia de Mitigación**:
  Ignorar por completo el campo precalculado `event_hour_utc` en todas las consultas y calcular la hora dinámicamente:
  ```sql
  EXTRACT(HOUR FROM event_timestamp)
  ```
* **Riesgo Operativo**: Reportar la distribución horaria por `event_hour_utc` resultará en la falsa conclusión de que el 85% de las entregas en LATAM se realizan a la medianoche.

---

## 📊 2. Matriz Comparativa de Calidad (Tablas de Control vs. Producción)

| Tipo de Tabla | Tabla Específica | Anotación / Métrica Evaluada | Registros Afectados | % de Error | Severidad | Riesgo Operativo |
|---|---|---|---|---|---|---|
| **Control** | `shipments` | PK Duplicados (`shipment_id`) | 0 | **0.00%** | 🟢 Baja | Ninguno, datos consistentes. |
| **Producción** | `shipments_new` | PK Duplicados (`shipment_id`) | 443,423 | **7.95%** | 🔴 Alta | Sobrecarga de volumen y tasas de efectividad infladas. |
| **Control** | `routes` | Chrono Violations (End < Start) | 0 | **0.00%** | 🟢 Baja | Ninguno. |
| **Producción** | `routes_new` | Chrono Violations (End < Start) | 20,756 | **17.40%** | 🔴 Alta | Duraciones de viaje negativas en los tableros. |
| **Control** | `routes` | Route Overlaps (Socio/Día) | 2,103 | **1.76%** | 🟡 Media | Inflación leve de flota. |
| **Producción** | `routes_new` | Route Overlaps (Socio/Día) | 62,549 | **52.43%** | 🔴 Alta | Conteo de flota en calle distorsionado de forma masiva. |
| **Control** | `shipment_events` | Corrupción de hora (`event_hour_utc`) | 174,672 | **60.70%** | 🔴 Alta | Sesgo de distribución horaria nocturna. |
| **Producción** | `shipment_events_new` | Corrupción de hora (`event_hour_utc`) | 6,227,543 | **85.29%** | 🔴 Alta | Análisis de husos horarios y OTH horaria inutilizable. |

---

## 🛠️ 3. Query de Validación Comparativa Unificada (BigQuery Standard SQL)

El siguiente script ejecuta simultáneamente la auditoría sobre las tablas históricas y las tablas nuevas, permitiendo evaluar las discrepancias de calidad directamente desde la GUI de BigQuery:

```sql
-- 1. Duplicidad de registros en envíos de control
SELECT 
  'shipments (Control) PK Duplication' as audit_check,
  COUNT(shipment_id) as total_records,
  COUNT(shipment_id) - COUNT(DISTINCT shipment_id) as error_count,
  ROUND((COUNT(shipment_id) - COUNT(DISTINCT shipment_id)) / COUNT(shipment_id) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipments`

UNION ALL

-- 2. Duplicidad de registros en envíos nuevos de producción
SELECT 
  'shipments_new (Production) PK Duplication' as audit_check,
  COUNT(shipment_id) as total_records,
  COUNT(shipment_id) - COUNT(DISTINCT shipment_id) as error_count,
  ROUND((COUNT(shipment_id) - COUNT(DISTINCT shipment_id)) / COUNT(shipment_id) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`

UNION ALL

-- 3. Rutas de control con cronología invertida
SELECT
  'routes (Control) Chrono Violations' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(actual_route_end_time < actual_route_start_time) as error_count,
  ROUND(COUNTIF(actual_route_end_time < actual_route_start_time) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes`

UNION ALL

-- 4. Rutas nuevas con cronología invertida
SELECT
  'routes_new (Production) Chrono Violations' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(actual_route_end_time < actual_route_start_time) as error_count,
  ROUND(COUNTIF(actual_route_end_time < actual_route_start_time) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new`

UNION ALL

-- 5. Inconsistencias de hora en logs de eventos de control
SELECT
  'shipment_events (Control) Hour Corruption' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) as error_count,
  ROUND(COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events`
WHERE event_timestamp IS NOT NULL

UNION ALL

-- 6. Inconsistencias de hora en logs de eventos nuevos
SELECT
  'shipment_events_new (Production) Hour Corruption' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) as error_count,
  ROUND(COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`
WHERE event_timestamp IS NOT NULL

ORDER BY error_pct DESC;
```

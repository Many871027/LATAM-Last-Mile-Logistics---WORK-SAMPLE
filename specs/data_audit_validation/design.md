# Data Design — LM-001 (Data Audit & Validation)

This document describes the design patterns, SQL structures, and mitigation strategies designed to satisfy requirements `A1` through `A9`.

## 1. Schema Auditing & Ingest Mitigation (A1)
* **Date Parsing & Formatting**: Raw CSV file date formats contain inconsistent format strings (slashes and dashes: `D/M/YYYY HH:MM` and `D/M/YYYY HH:MM:SS`).
* **Ingestion Mitigation**: The pipeline `load_to_bigquery.py` standardizes dates in Python pandas to ISO-8601 representation before loading to BigQuery with `max_bad_records = 0`.

## 2. Dynamic Deduplication Logic (A2)
* **Target Table**: `shipments_new`
* **CTE Structure**:
  To prevent overcounting due to duplicate primary keys (7.95% rate), all downstream queries must query a deduplicated CTE instead of accessing the raw table directly.
  ```sql
  WITH deduped_shipments AS (
    SELECT 
      * EXCEPT(rn)
    FROM (
      SELECT 
        *,
        ROW_NUMBER() OVER(PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC) as rn
      FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`
    )
    WHERE rn = 1
  )
  ```

## 3. Temporal Corrections (A3, A4)
* **Event Hour Corruption**: `event_hour_utc` has 85.2% corruption where hours from 20:00 to 23:59 are truncated to `0`.
* **Mitigation**: Derive hour from `event_timestamp` dynamically:
  ```sql
  EXTRACT(HOUR FROM event_timestamp) AS hour_utc
  ```
* **Timezone Shifts**:
  Timezone offset is retrieved from `distribution_centers.timezone_offset` and applied to `event_timestamp`:
  ```sql
  EXTRACT(HOUR FROM TIMESTAMP_ADD(event_timestamp, INTERVAL timezone_offset HOUR)) as hour_local
  ```

## 4. Chronological & Spatial Validation Logic (A5, A6)
* **Chronological Violations**: Filter out invalid routes where real duration is negative.
  ```sql
  actual_route_end_time >= actual_route_start_time
  ```
* **Driver/Partner Overlap Detection**:
  Self-join routes to find same-day, same-partner overlaps:
  ```sql
  SELECT 
    r1.partner_id, 
    r1.route_date,
    r1.route_id as route_a_id, 
    r2.route_id as route_b_id,
    r1.actual_route_start_time as start_a, 
    r1.actual_route_end_time as end_a,
    r2.actual_route_start_time as start_b, 
    r2.actual_route_end_time as end_b
  FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r1
  JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` r2
    ON r1.partner_id = r2.partner_id 
    AND r1.route_date = r2.route_date
    AND r1.route_id < r2.route_id
  WHERE r2.actual_route_start_time < r1.actual_route_end_time 
    AND r2.actual_route_end_time > r1.actual_route_start_time
  ```

## 5. Domain & Referential Integrity Logic (A7, A8)
* **Invalid Contracts**: Identify partners with inactive contract flag:
  ```sql
  active_flag = -1
  ```
* **Orphaned Routes**: Identify routes missing FK references:
  ```sql
  partner_id IS NULL OR vehicle_type_id IS NULL
  ```

## 6. Unified Data Quality Audit Query (A9)
The unified quality check query evaluates error rates and count profiles dynamically in BigQuery standard SQL:

```sql
-- 1. Duplicidad de registros en envios
SELECT 
  'shipments_new PK Duplication' as audit_check,
  COUNT(shipment_id) as total_records,
  COUNT(shipment_id) - COUNT(DISTINCT shipment_id) as error_count,
  ROUND((COUNT(shipment_id) - COUNT(DISTINCT shipment_id)) / COUNT(shipment_id) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`

UNION ALL

-- 2. Rutas nuevas con cronologia invertida (Fin antes de Inicio)
SELECT
  'routes_new Chrono Violations' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(actual_route_end_time < actual_route_start_time) as error_count,
  ROUND(COUNTIF(actual_route_end_time < actual_route_start_time) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new`

UNION ALL

-- 3. Inconsistencias de hora en el log de eventos
SELECT
  'shipment_events_new Hour Corruption' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) as error_count,
  ROUND(COUNTIF(event_hour_utc != EXTRACT(HOUR FROM event_timestamp)) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`
WHERE event_timestamp IS NOT NULL

UNION ALL

-- 4. Rutas nuevas sin chofer/transportista asignado
SELECT
  'routes_new Missing Partners' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(partner_id IS NULL) as error_count,
  ROUND(COUNTIF(partner_id IS NULL) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new`

UNION ALL

-- 5. Contratos marcados como inactivos/invalidos (-1) en partners
SELECT
  'partners Deprecated Contracts' as audit_check,
  COUNT(*) as total_records,
  COUNTIF(active_flag = -1) as error_count,
  ROUND(COUNTIF(active_flag = -1) / COUNT(*) * 100, 2) as error_pct
FROM `meli-last-mile-sql-assessment.LAstmile.partners`

ORDER BY error_pct DESC;
```

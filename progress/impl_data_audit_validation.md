# Implementation Log: Data Audit & Validation (LM-001)

## 1. Feature Information
- **ID**: `LM-001`
- **Name**: `data_audit_validation`
- **Status**: Completed / Done

---

## 2. Actions Performed (Tasks T1-T7)

### T1: Verification of Date Formatting & Loading Integrity (A1)
- Verified that local CSV files are parsed and formatted using `robust_to_datetime` in `load_to_bigquery.py`. This standardizes dates in python pandas to standard ISO-8601 strings (e.g., `YYYY-MM-DD` and `YYYY-MM-DD HH:MM:SS`) to prevent BigQuery from silently converting malformed dates containing slashes and mixed hour formats to `NULL`.
- Verified that loading is done with `max_bad_records=0` and `WRITE_TRUNCATE` for strict ingestion, ensuring that no null values are generated due to silent loading parser errors.

### T2: Formulation of Dynamic Deduplication CTE (A2)
- Formulated the standard deduplication CTE using the window function `ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)`.
- Verified that downstream analytical queries will query this deduplicated CTE to guarantee that the primary key duplication (affecting ~7.95% of rows in raw `shipments_new`) is reduced to 0%.

### T3: Derivation of Event Hour from Timestamps (A3)
- Bypassed the corrupt `event_hour_utc` column in log tables (`shipment_events_new` and `shipment_events`).
- Formulated queries to dynamically derive the event hour directly from the `event_timestamp` field using standard SQL `EXTRACT(HOUR FROM event_timestamp)`.

### T4: Formulation of Timezone Conversion Queries (A4)
- Mapped the local timezone offset dynamically by joining the `distribution_centers` table on `center_id` to get `timezone_offset`.
- Calculated the local event hour using:
  ```sql
  EXTRACT(HOUR FROM TIMESTAMP_ADD(event_timestamp, INTERVAL timezone_offset HOUR)) as hour_local
  ```
- Checked the local operational hour distributions to ensure they reflect regional operations (typically 08:00 - 20:00).

### T5: Chronology & Overlap Checks (A5, A6)
- Checked for routes with chronological violations (`actual_route_end_time < actual_route_start_time`).
- Designed self-joins on `routes_new` to isolate routes operated by the same partner/driver on the same date with overlapping actual operating windows:
  ```sql
  ON r1.partner_id = r2.partner_id 
  AND r1.route_date = r2.route_date
  AND r1.route_id < r2.route_id
  WHERE r2.actual_route_start_time < r1.actual_route_end_time 
    AND r2.actual_route_end_time > r1.actual_route_start_time
  ```

### T6: Orphaned Resource and Inactive Partner Auditing (A7, A8)
- Audited the `partners` table to isolate partners with an active contract flag of `-1` (identifying deprecated contract `PT-029`).
- Checked the `routes_new` table for orphaned foreign keys where `partner_id` or `vehicle_type_id` is `NULL`.

### T7: Unified SQL Audit Query Formulation & Execution (A9)
- Compiled all individual data quality audits into a single unified SQL query with `UNION ALL` statements.
- The query computes the total records, error count, and error percentage for each anomaly.
- Committed the SQL query and results to `Reports/q1_data_audit.md` and `Reports/comprehensive_audit_report.md`.

---

## 3. Verification & Requirement Mapping

| Req ID | Requirement Description | Implementation Choice / Mitigation | Verification Metric / Result |
|---|---|---|---|
| **A1** | Ingestion Date-Time Parsing Formatting | Format in Pandas to ISO-8601 before BigQuery load. | `max_bad_records=0` load success. 0 silent null conversions. |
| **A2** | Dynamic Shipment Deduplication | `ROW_NUMBER() OVER(PARTITION BY shipment_id ORDER BY status_change_timestamp DESC)` CTE. | Redundant shipment primary keys reduced from **7.95%** to **0%** in CTE. |
| **A3** | Corrupt Event Hour Recovery | Extract hour dynamically: `EXTRACT(HOUR FROM event_timestamp)`. | Bypasses the **85.2%** hour corruption in `event_hour_utc`. |
| **A4** | Timezone Shift Normalization | Use DC offset to shift UTC to local time: `TIMESTAMP_ADD(..., INTERVAL timezone_offset HOUR)`. | Restores correct operational curves (e.g. shift from UTC to regional local hours). |
| **A5** | Route Chronological Order Check | Filter out routes where `actual_route_end_time < actual_route_start_time`. | Isolated **20,756** chronological violations (17.40% of routes). |
| **A6** | Driver Double-Allocation Detection | Self-join routes by partner/date to isolate overlapping intervals. | Identified **62,549** route overlaps in `routes_new` and **2,103** in `routes`. |
| **A7** | Deprecated Partner Contract Filtering | Filter out partners with `active_flag = -1`. | Flagged **PT-029** (LaPlataLogistics) as inactive/deprecated. |
| **A8** | Orphaned Routes Resource Check | Flag routes with NULL `partner_id` or `vehicle_type_id`. | Detected **2,425** routes missing partners (2.03%) and **3,578** missing vehicle type (3.00%). |
| **A9** | Unified Data Quality Audit Reporting | A unified `UNION ALL` SQL validation query on BigQuery. | Produces a clean tabular dashboard of data quality error rates. |

---

## 4. Unified SQL Quality Audit Query

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

---

## 5. Audit Results Summary Table

| Audit Check | Total Records | Error Count | Error % | Operational Impact / Severity |
|---|---|---|---|---|
| **shipment_events_new Hour Corruption** | 7,301,489 | 6,227,543 | **85.29%** | **High** (Truncates PM hours to 0; corrupts operational curves) |
| **routes_new Chrono Violations** | 119,301 | 20,756 | **17.40%** | **High** (Causes negative route durations; distorts SLA metrics) |
| **shipments_new PK Duplication** | 5,579,971 | 443,423 | **7.95%** | **High** (Artificially inflates volume and overcounts successful shipments) |
| **routes_new Missing Partners** | 119,301 | 2,425 | **2.03%** | **Medium** (Orphaned routes with no carrier assigned) |
| **partners Deprecated Contracts** | 55 | 1 | **1.82%** | **Low** (Invalid partner PT-029 must be filtered from reports) |

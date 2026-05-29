# Implementation Log: BigQuery Data Loading & ETL (LM-PRE-002)

## 1. Feature Information
- **ID**: `LM-PRE-002`
- **Name**: `bigquery_data_load`
- **Status**: Completed / Done

## 2. Actions Performed
1. **Dynamic DB Path Resolution**:
   - Inspected `load_to_bigquery.py` and identified that the DB folder path was hardcoded to `D:\MELI_BI\DB`.
   - Updated `db_dir` in `load_to_bigquery.py` to resolve dynamically relative to the script's directory:
     ```python
     db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")
     ```
     This aligns it with the workspace and ensures file accesses stay inside the sandbox.

2. **Schema Verification & Alignment**:
   - Inspected the headers of all 9 raw data CSV files in `DB/` and cross-referenced them with the schemas defined in `SCHEMAS` in `load_to_bigquery.py`.
   - Added a column alignment/filtering step prior to saving the temporary cleaned CSV files:
     ```python
     # Align columns with the BigQuery schema mapping
     schema_cols = [field.name for field in schema]
     df = df[schema_cols]
     ```
     This guarantees that only the columns specified in the target schema are output to the temporary CSV, and they are written in the exact order that BigQuery expects, preventing schema parsing failures.

3. **Checklist and Verification**:
   - Confirmed schema mappings, date formats, and temporal fields match the expectations of the BigQuery tables.

---

## 3. Verification & Key Findings

### 3.1. Schema Alignment Verification
Every table structure defined in `load_to_bigquery.py` was mapped directly to the actual CSV columns:
- **`distribution_centers`**: Columns map exactly. Timezone offset is read as an integer to facilitate time conversion.
- **`partners`**: Nullable fields like `contract_end_date` are correctly typed as `DATE` (and will be loaded as `NULL` if empty).
- **`vehicle_types`**: Simple catalog columns match exactly.
- **`routes` & `routes_new`**:
  - `routes` contains `planned_route_start_time`, `planned_route_end_time`, `actual_route_start_time`, and `actual_route_end_time` as `TIME` formats (e.g., `08:35:00`).
  - `routes_new` contains the same columns as `TIMESTAMP` formats (e.g., `2025-01-01 08:08:00`).
  - The script's dual logic handles them cleanly using the `TIME` format parser and `TIMESTAMP` format parser respectively.
- **`shipments` & `shipments_new`**:
  - Slashed dates (e.g., `1/4/2025` and `2/5/2025 18:58:00`) in `shipments` are parsed robustly using `robust_to_datetime` and converted to standard ISO-8601 strings (`YYYY-MM-DD` and `YYYY-MM-DD HH:MM:SS`) to prevent BigQuery ingestion failures.
  - `shipments_new` has standard ISO-8601 formatting, which parses correctly.
- **`shipment_events` & `shipment_events_new`**:
  - Slashed timestamps in `shipment_events` are converted to standard ISO-8601 format.
  - `shipment_events_new` standard ISO-8601 timestamps are cleaned and parsed correctly.

### 3.2. Robust Ingestion Setup
- Idempotency is guaranteed by using the `WRITE_TRUNCATE` write disposition.
- Schema enforcement uses a strict BigQuery configuration with `max_bad_records=0` (zero tolerance for bad rows), guaranteeing no malformed date strings enter the database.

---

## 4. Acceptance Criteria Checklist
- [x] Develop a robust datetime parsing logic using Python and pandas.
- [x] Upload distribution centers, partners, vehicles, routes, shipments, and logs into BigQuery.
- [x] Ensure 0 bad records and correct schema parsing on load.

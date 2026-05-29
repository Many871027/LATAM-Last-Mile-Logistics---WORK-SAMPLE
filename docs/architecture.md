# Architecture & Quality Standards

This project follows an ELT (Extract, Load, Transform) pattern for analyzing last mile operations in LATAM.

## Data Layer Architecture
1. **Raw Source Data**: CSV files located in `DB/` containing regional distribution centers, partner carriers, vehicles, routes, shipments, and shipment logs.
2. **Ingestion & ETL**: Ingestion into Google BigQuery. Ingestion logic (in `load_to_bigquery.py`) formats date columns to ISO-8601 to prevent BigQuery from silently discarding mismatched timezone and date strings as `NULL`.
3. **Deduplication layer**: Raw shipment tables (`shipments_new`) contain PK duplication (~8%). Analytical queries must dynamically deduplicate records using:
   ```sql
   ROW_NUMBER() OVER(PARTITION BY shipment_id ORDER BY status_change_timestamp DESC)
   ```
4. **Timezone normalization**: Shipment events are stored in UTC-0. Distribution centers specify local offsets. Analytical dashboarding queries must calculate local timestamps using `TIMESTAMP_ADD(event_timestamp, INTERVAL timezone_offset HOUR)` to avoid the "timezone illusion".

## Definition of Quality Work
- **Traceability**: Every SQL query is fully documented with its business objective and logic.
- **Accuracy**: Data quality issues are audited, and query logic mitigates anomalies (e.g. ignoring the corrupt `event_hour_utc` column and recalculating hours from the timestamp, excluding routes with inverted start/end times).
- **Performance**: Standard SQL syntax, avoiding legacy SQL. Use of CTEs to keep queries modular, legible, and optimized.

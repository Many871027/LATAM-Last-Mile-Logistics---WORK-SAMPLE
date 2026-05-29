# Analytical Requirements — LM-001 (Data Audit & Validation)

This document defines the analytical and data quality requirements for the Last Mile Operations Data Warehouse. All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### Ingestion & Format Integrity
* **A1: Ingestion Date-Time Parsing Formatting (Event-Driven)**
  * **Trigger**: WHEN loading regional logistics data from local raw CSV files,
  * **System Response**: THEN the ETL pipeline shall parse and format all date and timestamp values to ISO-8601 representation (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) to prevent silent null conversion in BigQuery.

### Primary Key Integrity
* **A2: Dynamic Shipment Deduplication (Unwanted Behavior)**
  * **Undesired Condition**: IF `shipment_id` is duplicated in the raw `shipments_new` table (~7.95% duplication rate),
  * **System Response**: THEN the analytical queries shall deduplicate records dynamically using a Common Table Expression (CTE) with the `ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)` window function to ensure that only the latest state is evaluated.

### Log & Temporal Integrity
* **A3: Corrupt Event Hour Recovery (Unwanted Behavior)**
  * **Undesired Condition**: IF the precalculated log hour column `event_hour_utc` is corrupt in the log tables (`shipment_events` or `shipment_events_new`),
  * **System Response**: THEN the analytical queries shall ignore `event_hour_utc` and derive the event hour directly using `EXTRACT(HOUR FROM event_timestamp)` to avoid reporting incorrect hourly distributions.

* **A4: Timezone Shift Normalization (State-Driven)**
  * **State**: WHILE comparing operational patterns across regions with different timezone offsets,
  * **System Response**: THEN the system shall shift `event_timestamp` from UTC-0 to local time using `timezone_offset` from the `distribution_centers` table.

### Chronological & Spatial Integrity
* **A5: Route Chronological Order Check (Unwanted Behavior)**
  * **Undesired Condition**: IF a route in `routes_new` has an actual end time earlier than its actual start time (`actual_route_end_time < actual_route_start_time`),
  * **System Response**: THEN the quality audit shall flag the route as a chronological violation and exclude it from travel duration calculations.

* **A6: Driver Double-Allocation Detection (Unwanted Behavior)**
  * **Undesired Condition**: IF a partner carrier operates multiple active routes on the same `route_date` whose actual start and end times overlap,
  * **System Response**: THEN the quality audit shall identify these overlapping intervals as potential driver double-allocations or multi-regional coverage.

### Referential & Domain Integrity
* **A7: Deprecated Partner Contract Filtering (Unwanted Behavior)**
  * **Undesired Condition**: IF a partner has `active_flag = -1` in the `partners` table,
  * **System Response**: THEN the analytical query shall flag it as a deprecated contract and exclude it from active operations SLA compliance rankings.

* **A8: Orphaned Routes Resource Check (Unwanted Behavior)**
  * **Undesired Condition**: IF a route in `routes_new` has a NULL `partner_id` or a NULL `vehicle_type_id`,
  * **System Response**: THEN the quality audit shall flag it as a resource-orphaned route to highlight missing master keys.

### Quality Reporting
* **A9: Unified Data Quality Audit Reporting (Ubiquitous)**
  * **System Response**: The system shall execute a unified SQL quality audit query that computes total records, error counts, and error percentages for primary key duplication, route chronological violations, log hour corruption, missing partners, and deprecated contracts.

# Analytical Requirements — LM-006 (Partner Consistency)

This document defines the analytical and data quality requirements for the operational integrity audit of partner `PT-014` (SaoPauloShip). All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### 1. Stale Routes Audit
* **A1: Stale Route Classification (Unwanted Behavior)**
  * **Undesired Condition**: IF a route in the `routes_new` table remains in the `IN_PROGRESS` state past its scheduled `route_date`,
  * **System Response**: THEN the analytical query shall classify it as a stale route and exclude it from travel duration calculations.

* **A2: Route Closure Rate Calculation (Ubiquitous)**
  * **System Response**: The analytical layer SHALL calculate the route closure rate for partner `PT-014` using the `SAFE_DIVIDE` function over the count of completed routes and the total routes allocated to partner `PT-014` at the partner and route status level.

### 2. GPS & Temporal Chronology Audit
* **A3: Chronological Violation Detection (Unwanted Behavior)**
  * **Undesired Condition**: IF a route assigned to partner `PT-014` exhibits an actual end time earlier than its actual start time (`actual_route_end_time < actual_route_start_time`),
  * **System Response**: THEN the analytical query shall flag this record as a chronological violation and exclude it from OTH calculations by duration.

* **A4: GPS Synchronization Profiling (Unwanted Behavior)**
  * **Undesired Condition**: IF a completed route assigned to partner `PT-014` contains NULL values in either `actual_route_start_time` or `actual_route_end_time`,
  * **System Response**: THEN the quality audit shall flag the route as a GPS synchronization failure and exclude it from travel duration calculations.

### 3. Route Overlap & Hub Integrity Audit
* **A5: Multi-Hub Route Overlap Detection (Unwanted Behavior)**
  * **Undesired Condition**: IF a partner operates multiple active routes on the same `route_date` whose actual travel intervals (`actual_route_start_time` to `actual_route_end_time`) overlap and originate from different distribution hubs (`center_id`),
  * **System Response**: THEN the quality audit shall flag these concurrent intervals as multi-hub route overlaps.

* **A6: Multi-Hub Vehicle Double-Allocation (Unwanted Behavior)**
  * **Undesired Condition**: IF a single vehicle identifier (`vehicle_type_id`) is assigned to multiple overlapping routes for the same partner on the same `route_date` across different distribution centers (`center_id`),
  * **System Response**: THEN the analytical query shall flag it as an physically impossible resource allocation.

### 4. Contract Alignment & Reporting Governance
* **A7: Contract Expiration Audit (Unwanted Behavior)**
  * **Undesired Condition**: IF a partner has routes in `routes_new` with a `route_date` later than the partner's `contract_end_date` or while `active_flag = 0` in the `partners` table,
  * **System Response**: THEN the analytical query shall flag these as contract-expired route allocations.

* **A8: Partner Metrics Inclusion Threshold (State-Driven)**
  * **State**: WHILE the combined rate of chronological violations, stale routes, and multi-hub vehicle overlaps for partner `PT-014` exceeds 5% of its total assigned routes,
  * **System Response**: THEN the reporting layer shall exclude partner `PT-014` from standard SLA compliance and OTH reporting.

* **A9: Scheduled Audit Processing (Event-Driven)**
  * **Trigger**: WHEN the scheduled weekly partner performance job runs,
  * **System Response**: THEN the pipeline shall incrementally calculate the consistency metrics for all partners and update the quality control tables.

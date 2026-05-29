# Implementation Plan — LM-005 (Operational Patterns - Timezones)

This document maps analytical requirements to discrete, testable work units to be executed sequentially.

- [x] T1: Verification of Schema Associations and Scope Filtering
  * Verify table joins between `shipment_events_new` (`se`), `routes_new` (`r`), and `distribution_centers` (`dc`).
  * Verify filters retrieve only `'delivered'` events for completed delivery routes (`route_type = 'DELIVERY'`, `route_status = 'COMPLETED'`) in the date range '2025-04-01' to '2025-05-31'.
  * _Requirements: A1, A2_

- [x] T2: Formulation of Dynamic Timezone Conversion and Hour Extraction
  * Develop query logic to calculate local timestamps using `TIMESTAMP_ADD` and the center's `timezone_offset`.
  * Extract true UTC and local hours dynamically via `EXTRACT(HOUR FROM ...)` from the timestamps.
  * _Requirements: A3, A6_

- [x] T3: Calculation of Apparent vs. Real Late-Night Delivery Rates
  * Write the SQL query to calculate country-level total deliveries, apparent late-night deliveries (hour_utc >= 20), real late-night deliveries (hour_local >= 20), and their percentages using `SAFE_DIVIDE`.
  * Run the query and validate the output against reference values:
    * Brazil (BR): 0.73% local vs. 0.51% UTC
    * Colombia (CO): 3.12% local vs. 0.47% UTC
    * Mexico (MX): 5.64% local vs. 0.55% UTC
    * Peru (PE): 3.94% local vs. 0.64% UTC
    * Argentina (AR): 0.73% local vs. 0.57% UTC
    * Chile (CL): 1.13% local vs. 0.61% UTC
  * _Requirements: A4, A5_

- [x] T4: Diagnostic Audit of Logging Corruption
  * Implement query logic to isolate discrepancies between the precalculated `event_hour_utc` field and the true hour extracted from `event_timestamp`.
  * Verify that the corruption is localized specifically to events occurring between 20:00 and 23:59 UTC, where the database column is forced to `0`.
  * Calculate the total count and overall percentage of corrupt rows in the table.
  * _Requirements: A6_

- [x] T5: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A6_

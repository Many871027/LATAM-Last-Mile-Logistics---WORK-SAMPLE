# Implementation Plan — LM-004 (OTH - On-Time Handling)

This document maps analytical requirements to discrete, testable work units to be executed sequentially by the SQL/AI implementer.

- [x] T1: Verification of Route Filtering & Chronological Exclusions
  * Verify only completed delivery routes (`route_type = 'DELIVERY'`, `route_status = 'COMPLETED'`) within the date range '2025-04-01' to '2025-05-31' are included.
  * Implement non-null validation on `planned_route_start_time`, `planned_route_end_time`, `actual_route_start_time`, and `actual_route_end_time`.
  * Ensure chronological ordering checks are applied: `actual_route_end_time >= actual_route_start_time` and `planned_route_end_time >= planned_route_start_time`.
  * _Requirements: A1, A2_

- [x] T2: Formulation & Validation of OTH Metrics
  * Formulate standard SQL calculations for `oth_end_time_pct` and `oth_duration_pct` using standard `TIME_DIFF` and `SAFE_DIVIDE`.
  * Group metrics by planned end hour (hour of fin) using `EXTRACT(HOUR FROM planned_route_end_time)` to analyze hourly patterns.
  * Validate that the formulas produce correct outputs with no division-by-zero errors.
  * _Requirements: A3, A4_

- [x] T3: Identification of Underperforming Partners and Vehicles
  * Write the SQL query to aggregate OTH metrics by country, partner, and vehicle type.
  * Apply a `HAVING` clause or filter to identify all partner-vehicle-country combinations where either `oth_end_time_pct` or `oth_duration_pct` is strictly below 75%.
  * _Requirements: A6_

- [x] T4: Metric Gap & Departure Latency Analysis
  * Calculate `oth_metric_gap` by subtracting `oth_end_time_pct` from `oth_duration_pct`.
  * Formulate analysis explaining that a positive gap indicates carriers drive efficiently (on-time duration) but arrive late overall due to delayed route start times.
  * _Requirements: A5_

- [x] T5: Report Generation and Test Integration
  * Compile all queries and analytical findings into `Reports/Question_4_On_Time_Handling_Report.md`.
  * Author test assertions in `tests/test_on_time_handling.py` to programmatically verify OTH metrics in BigQuery.
  * Ensure all tests pass.
  * _Requirements: A1, A2, A3, A4, A5, A6, A7_

- [x] T6: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A7_

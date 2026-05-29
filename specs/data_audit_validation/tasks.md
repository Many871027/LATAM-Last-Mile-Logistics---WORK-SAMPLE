# Implementation Plan — LM-001 (Data Audit & Validation)

This document maps analytical requirements to discrete, testable work units to be executed sequentially.

- [x] T1: Verification of Date Formatting & Loading Integrity
  * Verify that date and timestamp fields are parsed in Python pandas to standard ISO-8601 representation.
  * Verify that no null values are generated in BigQuery on date columns (`status_change_timestamp`, `route_date`, etc.).
  * _Requirements: A1_

- [x] T2: Formulation of Dynamic Deduplication CTE
  * Develop the Common Table Expression (CTE) using `ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)` to isolate single shipments.
  * Validate that primary key duplication is reduced to 0% in deduplicated sets (from ~7.95% raw).
  * _Requirements: A2_

- [x] T3: Derivation of Event Hour from Timestamps
  * Formulate dynamic hourly aggregation queries bypassing `event_hour_utc` and deriving values directly from `event_timestamp`.
  * Validate that the hourly metrics are clean and reflect physical distribution hours.
  * _Requirements: A3_

- [x] T4: Formulation of Timezone Conversion Queries
  * Map `timezone_offset` from distribution centers to `event_timestamp` dynamically.
  * Compare UTC vs Local time distributions to verify the timezone shift.
  * _Requirements: A4_

- [x] T5: Chronology & Overlap Checks
  * Detect chronological violations (`actual_route_end_time < actual_route_start_time`).
  * Perform self-join on `routes_new` by partner/date to isolate route overlaps.
  * _Requirements: A5, A6_

- [x] T6: Orphaned Resource and Inactive Partner Auditing
  * Filter for deprecated contracts `active_flag = -1` in `partners`.
  * Check routes missing foreign keys `partner_id` or `vehicle_type_id`.
  * _Requirements: A7, A8_

- [x] T7: Unified SQL Audit Query Formulation & Execution
  * Combine primary key duplication checks, route chronological violations, log hour corruption, missing partners, and deprecated contracts into a single `UNION ALL` statement.
  * Verify that the query runs successfully on BigQuery Standard SQL and produces a tabular output.
  * Save and commit the finalized SQL query and the results into the audit report.
  * _Requirements: A9_

- [x] T8: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A9_

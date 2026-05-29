# Implementation Plan — LM-006 (Partner Consistency)

This document maps analytical requirements to discrete, testable work units to be executed sequentially.

- [x] T1: Stale Routes & Closure Rate Analysis
  * Formulate SQL logic to identify routes in `IN_PROGRESS` state whose `route_date` is in the past.
  * Compute the route closure rate using `SAFE_DIVIDE` on completed routes vs total routes.
  * _Requirements: A1, A2_

- [x] T2: GPS & Chronology Violation Audit
  * Detect chronological violations where `actual_route_end_time < actual_route_start_time`.
  * Detect missing timestamps for completed routes where start or end times are NULL.
  * Compute percentages of corrupted routes to establish data quality baselines.
  * _Requirements: A3, A4_

- [x] T3: Hub Overlap & Resource Double-Allocation Audit
  * Implement a self-join query on `routes_new` grouped by partner and date to find overlapping active route intervals.
  * Detect multi-hub overlaps where concurrent routes originate from different distribution centers.
  * Audit vehicle double-allocation where the same vehicle is assigned to overlapping concurrent routes across different hubs.
  * _Requirements: A5, A6_

- [x] T4: Contract Alignment and Compliance Profiling
  * Join `routes_new` and `partners` to identify routes scheduled after `contract_end_date` or while `active_flag = 0`.
  * Determine the date range and count of such invalid route allocations.
  * _Requirements: A7_

- [x] T5: Formulation of the Unified Partner Consistency Query & Policy Recommendation
  * Combine stale routes, chronological violations, GPS sync failures, multi-hub overlaps, and contract expirations into a single, unified SQL summary query.
  * Run the query in BigQuery to evaluate PT-014 (SaoPauloShip) against the 5% error threshold.
  * Draft a strategic recommendation on whether to include PT-014 in standard reporting based on the audit results.
  * _Requirements: A8, A9_

- [x] T6: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A9_


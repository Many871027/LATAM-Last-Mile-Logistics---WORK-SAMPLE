# Implementation Plan — LM-002 (Productivity - Route Utilization)

This document maps analytical requirements to discrete, testable work units to be executed sequentially.

- [x] T1: Verification of Route Filtering & Hub Association
  * Verify that only completed delivery routes (`route_type = 'DELIVERY'`, `route_status = 'COMPLETED'`) within the date range '2025-04-01' to '2025-05-31' are evaluated.
  * Verify that distribution center attributes (country) are successfully joined with route data.
  * _Requirements: A1, A2_

- [x] T2: Formulation of Dynamic Shipment Count Deduplication
  * Develop the window-partitioned CTE to deduplicate shipments dynamically.
  * Compare the deduplicated counts against raw counts to verify that duplicate shipments (~7.95% raw rate) do not inflate the volume metric.
  * _Requirements: A4_

- [x] T3: Calculation of Stops Efficiency and Capacity Utilization by Country
  * Write the SQL query to calculate country-level total completed routes, estimated stops, actual stops, stops efficiency, shipments carried, vehicle capacity, and capacity utilization.
  * Verify that all calculations handle zero denominators safely with `SAFE_DIVIDE`.
  * Validate output against the reference values: Colombia (stops efficiency: 91.34%, capacity utilization: 78.95%), Brazil (stops efficiency: 89.11%, capacity utilization: 64.08%), etc.
  * _Requirements: A3, A5_

- [x] T4: Analysis of Underperforming Routes
  * Formulate the query to count and calculate the percentage of underperforming routes (stops efficiency < 60%) for each country.
  * Verify that the results show underperforming route counts by country (e.g. Colombia: 10, Peru: 3, Argentina: 7, Mexico: 7, Brazil: 10, Chile: 1).
  * _Requirements: A6_

- [x] T5: Profiling the Worst Routes in Brazil
  * Implement the query to extract the top 5 worst-performing routes in Brazil.
  * Validate that the query outputs the expected routes, including details on carrier partners, vehicle types, stops, and utilization metrics.
  * Save the SQL queries and results to the official report.
  * _Requirements: A7_

- [x] T6: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A7_

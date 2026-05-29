# Analytical Requirements — LM-004 (OTH - On-Time Handling)

This document defines the analytical and data quality requirements for measuring last-mile route schedule performance (On-Time Handling). All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### Data Quality & Exclusions
* **A1: Chronological Validation Exclusion (Unwanted Behavior)**
  * **Undesired Condition**: IF a route contains a chronological violation where `actual_route_end_time < actual_route_start_time` OR `planned_route_end_time < planned_route_start_time`,
  * **System Response**: THEN the system SHALL exclude the route record from the On-Time Handling calculations to prevent corrupt durations from skewing metrics.

* **A2: Critical Value Null Exclusion (Unwanted Behavior)**
  * **Undesired Condition**: IF any critical time column (`planned_route_start_time`, `planned_route_end_time`, `actual_route_start_time`, or `actual_route_end_time`) contains a NULL value for a route,
  * **System Response**: THEN the system SHALL exclude the route record from On-Time Handling calculations.

### Core Metrics Formulation
* **A3: On-Time Handling by End Time (Ubiquitous)**
  * **System Response**: The analytical layer SHALL calculate On-Time Handling by End Time (`oth_end_time_pct`) using the `SAFE_DIVIDE` function over the count of completed delivery routes where `actual_route_end_time <= planned_route_end_time` and the total count of valid completed delivery routes, grouped at the country, partner, and vehicle type granularity.

* **A4: On-Time Handling by Duration (Ubiquitous)**
  * **System Response**: The analytical layer SHALL calculate On-Time Handling by Duration (`oth_duration_pct`) using the `SAFE_DIVIDE` function over the count of completed delivery routes where `TIME_DIFF(actual_route_end_time, actual_route_start_time, MINUTE) <= TIME_DIFF(planned_route_end_time, planned_route_start_time, MINUTE)` and the total count of valid completed delivery routes, grouped at the country, partner, and vehicle type granularity.

* **A5: Performance Metric Gap (Ubiquitous)**
  * **System Response**: The analytical layer SHALL calculate the OTH Metric Gap (`oth_metric_gap`) using the subtraction of `oth_end_time_pct` from `oth_duration_pct` for each country, partner, and vehicle type to measure the impact of departure latency on schedule adherence.

### Operational Alerting & Ingestion
* **A6: Underperforming Fleet Alerting (State-Driven)**
  * **State**: WHILE the `oth_end_time_pct` or `oth_duration_pct` of a partner or vehicle type combination in a country is strictly below 75%,
  * **AI Agent Response**: THEN the AI agent SHALL flag the partner and vehicle type combination as underperforming and generate a route dispatch optimization alert.

* **A7: Idempotent Daily Pipeline Execution (Event-Driven)**
  * **Trigger**: WHEN the daily scheduled analytical pipeline executes,
  * **System Response**: THEN the pipeline SHALL process the on-time handling data and update the target reporting table using a MERGE operation to prevent duplicate records.

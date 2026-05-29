# Analytical Requirements — LM-005 (Operational Patterns - Timezones)

This document defines the analytical and data quality requirements for investigating late-night deliveries and timezone offsets. All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### Scope & Filtering
* **A1: Completed Delivery Route & Event Filtering (State-Driven)**
  * **State**: WHILE calculating late-night delivery metrics for April-May 2025,
  * **System Response**: THEN the system shall filter for completed delivery routes (`route_type = 'DELIVERY'` and `route_status = 'COMPLETED'`) with a route date between '2025-04-01' and '2025-05-31', and only evaluate shipment events of type `'delivered'`.

* **A2: Regional Hub Timezone Association (State-Driven)**
  * **State**: WHILE adjusting event timestamps from UTC to local time,
  * **System Response**: THEN the system shall join the shipment events table with the routes table and the distribution centers table to associate each delivery event with the distribution center's local `timezone_offset`.

### Timezone Conversions & Calculations
* **A3: Dynamic Timezone Offset Conversion (Ubiquitous)**
  * **System Response**: The system shall dynamically compute the local event timestamp by adding the distribution center's `timezone_offset` (in hours) to the UTC `event_timestamp` via `TIMESTAMP_ADD`.

* **A4: Real vs. Apparent Late-Night Delivery Rate Calculation (Ubiquitous)**
  * **System Response**: The system shall compute both the apparent late-night delivery rate (using the UTC timestamp hour) and the real late-night delivery rate (using the local adjusted timestamp hour), defined as the percentage of deliveries occurring at or after 20:00 (20:00:00 to 23:59:59) relative to total deliveries, using `SAFE_DIVIDE` to prevent division-by-zero errors.

* **A5: Regional Comparison Analysis (State-Driven)**
  * **State**: WHILE comparing operational patterns across LATAM countries,
  * **System Response**: THEN the system shall group the total deliveries, apparent late-night deliveries (UTC), and real late-night deliveries (local) by country and timezone offset to identify which regions genuinely exhibit high rates of late-night operations.

### Data Quality & Corruption Detection
* **A6: Corrupt Hour Field Detection & Audit (Unwanted Behavior)**
  * **Undesired Condition**: IF the precalculated database column `event_hour_utc` contains zero (`0`) for events with a UTC `event_timestamp` hour between `20` and `23` inclusive (20:00 to 23:59 UTC),
  * **System Response**: THEN the analytical system shall flag these records as corrupt, exclude the precalculated `event_hour_utc` field from timezone analysis, and dynamically extract the hour directly from the UTC `event_timestamp` for reporting.

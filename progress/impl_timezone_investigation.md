# Implementation Report — LM-005 (Operational Patterns - Timezones)

## Goal
Investigate late-night deliveries in LATAM regions to determine if they are a timezone illusion (UTC vs local time) and perform a diagnostic audit of precalculated log hour corruption.

## Implementation Details

### Logic Implementation
The core logic has been implemented in `src/timezone_handler.py`. It includes two main functions:
- `calculate_timezone_metrics`: Implements timezone conversion and metrics calculation.
  - Joins `shipment_events_new`, `routes_new`, and `distribution_centers`.
  - Filters for completed delivery routes (`route_type = 'DELIVERY'`, `route_status = 'COMPLETED'`) with a route date between '2025-04-01' and '2025-05-31', and only evaluates shipment events of type `'delivered'`.
  - Dynamically converts event timestamps from UTC to local time using the center's `timezone_offset` (via `pd.to_timedelta` unit='h').
  - Calculates true UTC and local hours, and calculates apparent vs real late-night delivery rates (at or after 20:00) using safe division.
  - Groups results by country and timezone offset.
- `audit_logging_corruption`: Implements diagnostic audit of precalculated column `event_hour_utc` corruption.
  - Detects if `event_hour_utc` is 0 when the actual UTC hour extracted from `event_timestamp` is between 20:00 and 23:59 UTC.
  - Calculates corrupt record counts and percentage by true UTC hour.
  - Computes the overall count and percentage of corrupt rows in the table.

### Validation & Report Generation
The validation is implemented in `tests/test_timezone_investigation.py`, which provides:
- A local unit test (`test_local_timezone_calculations`) using mock DataFrames to verify filtering, joining, timezone conversion, rate calculation, and corruption detection.
- A live cloud test (`test_cloud_timezone_investigation`) querying BigQuery to validate results against reference values (e.g. CO: 3.12% local vs 0.47% UTC; MX: 5.64% local vs 0.55% UTC).
- Dynamic report generation, compiling findings, query results, and data audit counts directly from BigQuery into `Reports/Question_5_Timezone_Investigation_Report.md`.

---

## Traceability Mapping (R<n> -> Test)

| Req ID | Requirement Description | Implementation Location | Verification Test Method |
| :--- | :--- | :--- | :--- |
| **A1** | Completed Delivery Route & Event Filtering | `src/timezone_handler.py` lines 18-28 | `test_local_timezone_calculations` (verifies exclusion of pickup route types and incorrect dates) |
| **A2** | Regional Hub Timezone Association | `src/timezone_handler.py` lines 13-17 | `test_local_timezone_calculations` (verifies correct merge with routes and distribution centers) |
| **A3** | Dynamic Timezone Offset Conversion | `src/timezone_handler.py` lines 36-39 | `test_local_timezone_calculations` and `test_cloud_timezone_investigation` (verifies local time shift by offset) |
| **A4** | Real vs. Apparent Late-Night Delivery Rate Calculation | `src/timezone_handler.py` lines 41-55 | `test_local_timezone_calculations` (verifies percentages are calculated with safe division) |
| **A5** | Regional Comparison Analysis | `src/timezone_handler.py` lines 44-55 | `test_cloud_timezone_investigation` (verifies outputs match exact reference rates for all 6 countries) |
| **A6** | Corrupt Hour Field Detection & Audit | `src/timezone_handler.py` lines 58-86 | `test_local_timezone_calculations` (checks corruption logic) and `test_cloud_timezone_investigation` (verifies corruption rate and presence of 100% bug on BigQuery) |

---

## Files Created/Modified
- `src/timezone_handler.py`: Core logic for calculations and audit.
- `tests/test_timezone_investigation.py`: Verification tests and dynamic report generator.
- `Reports/Question_5_Timezone_Investigation_Report.md`: Markdown report outlining the findings.
- `progress/impl_timezone_investigation.md`: Traceability mapping and implementation report.
- `specs/timezone_investigation/tasks.md`: Checked completed tasks.

# Data Design — LM-004 (OTH - On-Time Handling)

This document describes the target schema, data quality exclusions, and SQL calculations designed to satisfy requirements `A1` through `A7`.

## 1. Target Schema & Associations (A1, A2)

To calculate On-Time Handling (OTH) metrics across different dimensions (partner, vehicle type, country), the operational tables are associated using the following relationships:
* `meli-last-mile-sql-assessment.LAstmile.routes_new` (`r`) — main route execution details (dates, status, type, and times).
* `meli-last-mile-sql-assessment.LAstmile.partners` (`p`) ON `r.partner_id = p.partner_id` — carrier names and attributes.
* `meli-last-mile-sql-assessment.LAstmile.vehicle_types` (`vt`) ON `r.vehicle_type_id = vt.vehicle_type_id` — vehicle capacity and types.
* `meli-last-mile-sql-assessment.LAstmile.distribution_centers` (`dc`) ON `r.center_id = dc.center_id` — regional center country mapping.

## 2. Chronological & Data Quality Sanitization (A1, A2)

To ensure the validity of time-difference calculations and prevent corrupt records from distorting metrics, routes must satisfy the following filter criteria:
* **Route Scope**: Completed delivery routes (`r.route_type = 'DELIVERY'` and `r.route_status = 'COMPLETED'`) in April-May 2025 (`r.route_date BETWEEN '2025-04-01' AND '2025-05-31'`).
* **Non-Null Constraint**: Exclusion of rows where any route time parameters (`planned_route_start_time`, `planned_route_end_time`, `actual_route_start_time`, `actual_route_end_time`) are NULL.
* **Chronological Order Constraint**: Validation that end times are chronologically equal to or after start times for both planned and actual values.

```sql
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  AND r.planned_route_start_time IS NOT NULL
  AND r.planned_route_end_time IS NOT NULL
  AND r.actual_route_start_time IS NOT NULL
  AND r.actual_route_end_time IS NOT NULL
  AND r.actual_route_end_time >= r.actual_route_start_time
  AND r.planned_route_end_time >= r.planned_route_start_time
```

## 3. OTH Metric Formulations (A3, A4, A5)

### OTH by End Time (Definition 1)
Measures the proportion of routes that finished on or before the planned end time.
* **Logic**: `actual_route_end_time <= planned_route_end_time`
* **SQL Formulation**:
```sql
ROUND(
  SAFE_DIVIDE(
    COUNTIF(r.actual_route_end_time <= r.planned_route_end_time),
    COUNT(r.route_id)
  ) * 100,
  2
) AS oth_end_time_pct
```

### OTH by Duration (Definition 2)
Measures the proportion of routes where the actual trip duration (in minutes) did not exceed the planned duration.
* **Logic**: `Actual Duration <= Planned Duration` where Duration is calculated using BigQuery standard SQL `TIME_DIFF(end_time, start_time, MINUTE)`.
* **SQL Formulation**:
```sql
ROUND(
  SAFE_DIVIDE(
    COUNTIF(
      TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= 
      TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)
    ),
    COUNT(r.route_id)
  ) * 100,
  2
) AS oth_duration_pct
```

### OTH Metric Gap
Measures the operational deviation between the duration-based efficiency and the final schedule commitment. A high positive gap implies that carriers drive efficiently but fail end-time commitments due to delayed departures.
* **SQL Formulation**:
```sql
ROUND(
  SAFE_DIVIDE(
    COUNTIF(
      TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= 
      TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)
    ),
    COUNT(r.route_id)
  ) * 100,
  2
) -
ROUND(
  SAFE_DIVIDE(
    COUNTIF(r.actual_route_end_time <= r.planned_route_end_time),
    COUNT(r.route_id)
  ) * 100,
  2
) AS oth_metric_gap
```

## 4. Query Designs

### A. Master Performance Query (by Country, Partner, Vehicle Type)
Generates the baseline metrics to analyze vehicle and partner schedule compliance.

```sql
SELECT 
  dc.country,
  r.partner_id,
  p.partner_name,
  vt.vehicle_type_name,
  COUNT(r.route_id) AS total_routes,
  ROUND(SAFE_DIVIDE(COUNTIF(r.actual_route_end_time <= r.planned_route_end_time), COUNT(r.route_id)) * 100, 2) AS oth_end_time_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)), COUNT(r.route_id)) * 100, 2) AS oth_duration_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)), COUNT(r.route_id)) * 100, 2) -
  ROUND(SAFE_DIVIDE(COUNTIF(r.actual_route_end_time <= r.planned_route_end_time), COUNT(r.route_id)) * 100, 2) AS oth_metric_gap
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
JOIN `meli-last-mile-sql-assessment.LAstmile.partners` p 
  ON r.partner_id = p.partner_id
JOIN `meli-last-mile-sql-assessment.LAstmile.vehicle_types` vt 
  ON r.vehicle_type_id = vt.vehicle_type_id
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc 
  ON r.center_id = dc.center_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  AND r.planned_route_start_time IS NOT NULL
  AND r.planned_route_end_time IS NOT NULL
  AND r.actual_route_start_time IS NOT NULL
  AND r.actual_route_end_time IS NOT NULL
  AND r.actual_route_end_time >= r.actual_route_start_time
  AND r.planned_route_end_time >= r.planned_route_start_time
GROUP BY dc.country, r.partner_id, p.partner_name, vt.vehicle_type_name
ORDER BY dc.country, total_routes DESC;
```

### B. OTH by Hour of Fin (Planned End Hour)
Isolates performance based on the route's planned completion hour of the day.

```sql
SELECT 
  EXTRACT(HOUR FROM r.planned_route_end_time) AS planned_end_hour,
  COUNT(r.route_id) AS total_routes,
  ROUND(SAFE_DIVIDE(COUNTIF(r.actual_route_end_time <= r.planned_route_end_time), COUNT(r.route_id)) * 100, 2) AS oth_end_time_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)), COUNT(r.route_id)) * 100, 2) AS oth_duration_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)), COUNT(r.route_id)) * 100, 2) -
  ROUND(SAFE_DIVIDE(COUNTIF(r.actual_route_end_time <= r.planned_route_end_time), COUNT(r.route_id)) * 100, 2) AS oth_metric_gap
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  AND r.planned_route_start_time IS NOT NULL
  AND r.planned_route_end_time IS NOT NULL
  AND r.actual_route_start_time IS NOT NULL
  AND r.actual_route_end_time IS NOT NULL
  AND r.actual_route_end_time >= r.actual_route_start_time
  AND r.planned_route_end_time >= r.planned_route_start_time
GROUP BY planned_end_hour
ORDER BY planned_end_hour ASC;
```

### C. Underperforming Carriers & Fleet Identification (A6)
Retrieves partner/vehicle-type groupings with OTH metrics strictly below 75%.

```sql
SELECT 
  dc.country,
  p.partner_name,
  vt.vehicle_type_name,
  COUNT(r.route_id) AS total_routes,
  ROUND(SAFE_DIVIDE(COUNTIF(r.actual_route_end_time <= r.planned_route_end_time), COUNT(r.route_id)) * 100, 2) AS oth_end_time_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(TIME_DIFF(r.actual_route_end_time, r.actual_route_start_time, MINUTE) <= TIME_DIFF(r.planned_route_end_time, r.planned_route_start_time, MINUTE)), COUNT(r.route_id)) * 100, 2) AS oth_duration_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
JOIN `meli-last-mile-sql-assessment.LAstmile.partners` p 
  ON r.partner_id = p.partner_id
JOIN `meli-last-mile-sql-assessment.LAstmile.vehicle_types` vt 
  ON r.vehicle_type_id = vt.vehicle_type_id
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc 
  ON r.center_id = dc.center_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  AND r.planned_route_start_time IS NOT NULL
  AND r.planned_route_end_time IS NOT NULL
  AND r.actual_route_start_time IS NOT NULL
  AND r.actual_route_end_time IS NOT NULL
  AND r.actual_route_end_time >= r.actual_route_start_time
  AND r.planned_route_end_time >= r.planned_route_start_time
GROUP BY dc.country, p.partner_name, vt.vehicle_type_name
HAVING oth_end_time_pct < 75.0 OR oth_duration_pct < 75.0
ORDER BY oth_end_time_pct ASC;
```

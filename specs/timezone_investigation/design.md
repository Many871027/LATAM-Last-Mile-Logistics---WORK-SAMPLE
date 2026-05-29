# Data Design — LM-005 (Operational Patterns - Timezones)

This document describes the design patterns, SQL structures, and data validation strategies designed to satisfy requirements `A1` through `A6` for the timezone investigation.

## 1. Target Schema & Associations (A1, A2)

To analyze operational patterns and adjust timestamps, the database design associates shipment event logs with routes and regional distribution centers:
* `meli-last-mile-sql-assessment.LAstmile.shipment_events_new` (`se`) — contains raw timestamp logs for shipment lifecycle events (e.g. `'delivered'`).
* `meli-last-mile-sql-assessment.LAstmile.routes_new` (`r`) — maps events to specific routes, containing route dates, types, and statuses.
* `meli-last-mile-sql-assessment.LAstmile.distribution_centers` (`dc`) — contains geographic mapping and the local `timezone_offset` for each center.

Key relationships:
* `se.route_id = r.route_id`
* `r.center_id = dc.center_id`

## 2. Dynamic Timezone Adjustment (A3)

Shipment event timestamps are recorded in UTC-0 (`se.event_timestamp`). To recover the actual local time of the delivery, the system adds the center's `timezone_offset` (an integer indicating hours relative to UTC-0, e.g. `-3` for Brazil, `-5` for Colombia) to the timestamp.

### SQL Expression for Local Time Conversion
```sql
TIMESTAMP_ADD(se.event_timestamp, INTERVAL dc.timezone_offset HOUR)
```

To extract the hour of the event in local time:
```sql
EXTRACT(HOUR FROM TIMESTAMP_ADD(se.event_timestamp, INTERVAL dc.timezone_offset HOUR)) as hour_local
```

And for the true UTC hour (calculated dynamically rather than trusting precalculated fields):
```sql
EXTRACT(HOUR FROM se.event_timestamp) as hour_utc
```

## 3. Real vs. Apparent Late-Night Delivery Metrics (A4, A5)

A "late-night delivery" is defined as any delivery event where the hour is at or after 20:00 (i.e. `hour >= 20`).
* **Apparent Late-Night Delivery Rate (UTC)**: Calculated using `hour_utc`.
* **Real Late-Night Delivery Rate (Local)**: Calculated using `hour_local`.

### Metric Formulations
Using `SAFE_DIVIDE` ensures that countries or centers with zero deliveries do not throw division-by-zero errors.

* **Apparent Late-Night % (UTC)**:
  ```sql
  ROUND(SAFE_DIVIDE(COUNTIF(EXTRACT(HOUR FROM se.event_timestamp) >= 20), COUNT(*)) * 100, 2)
  ```
* **Real Late-Night % (Local)**:
  ```sql
  ROUND(SAFE_DIVIDE(COUNTIF(EXTRACT(HOUR FROM TIMESTAMP_ADD(se.event_timestamp, INTERVAL dc.timezone_offset HOUR)) >= 20), COUNT(*)) * 100, 2)
  ```

### Core Comparison Query
The query to generate the country-level timezone comparison is structured as follows:

```sql
-- Use Legacy SQL: False
WITH delivery_events AS (
  SELECT 
    dc.country,
    dc.timezone_offset,
    se.event_timestamp,
    EXTRACT(HOUR FROM se.event_timestamp) as hour_utc,
    EXTRACT(HOUR FROM TIMESTAMP_ADD(se.event_timestamp, INTERVAL dc.timezone_offset HOUR)) as hour_local
  FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new` se
  JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` r
    ON se.route_id = r.route_id
  JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc
    ON r.center_id = dc.center_id
  WHERE se.event_type = 'delivered'
    AND r.route_type = 'DELIVERY'
    AND r.route_status = 'COMPLETED'
    AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
)

SELECT 
  country,
  timezone_offset,
  COUNT(*) as total_deliveries,
  
  -- Apparent late-night deliveries (UTC)
  COUNTIF(hour_utc >= 20) as deliveries_utc_after_20,
  ROUND(SAFE_DIVIDE(COUNTIF(hour_utc >= 20), COUNT(*)) * 100, 2) as pct_utc_after_20,
  
  -- Real late-night deliveries (Local)
  COUNTIF(hour_local >= 20) as deliveries_local_after_20,
  ROUND(SAFE_DIVIDE(COUNTIF(hour_local >= 20), COUNT(*)) * 100, 2) as pct_local_after_20
FROM delivery_events
GROUP BY country, timezone_offset
ORDER BY country;
```

## 4. Log Corruption Auditing (A6)

Our data quality audit revealed that the precalculated column `event_hour_utc` in `shipment_events_new` is corrupt. It is truncated to `0` whenever the actual event timestamp hour is between 20:00 and 23:59 UTC. This causes standard aggregations relying on `event_hour_utc` to show zero late-night deliveries.

To prove and document this corruption, we design a diagnostic audit query to evaluate the entire `shipment_events_new` table.

### Corruption Verification Query
This query compares the true hour extracted from the timestamp with the precalculated logged hour for all events:

```sql
-- Use Legacy SQL: False
SELECT 
  EXTRACT(HOUR FROM event_timestamp) AS true_hour_utc,
  event_hour_utc AS logged_hour_utc,
  COUNT(*) AS total_events,
  COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20) AS corrupt_records,
  ROUND(SAFE_DIVIDE(COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20), COUNT(*)) * 100, 2) AS corruption_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`
GROUP BY true_hour_utc, logged_hour_utc
ORDER BY true_hour_utc;
```

### Overall Corruption Rate Calculation
To find the exact percentage of rows in the table where the bug occurs:

```sql
-- Use Legacy SQL: False
SELECT 
  COUNT(*) as total_rows,
  COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20) as total_corrupt_rows,
  ROUND(SAFE_DIVIDE(COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20), COUNT(*)) * 100, 2) as overall_corruption_pct
FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`;
```

# Data Design — LM-002 (Productivity - Route Utilization)

This document describes the design patterns, SQL structures, and mitigation strategies designed to satisfy requirements `A1` through `A7`.

## 1. Target Schema & Associations (A1, A2)

To compute route productivity by country, the database design associates operational tables through key relationships:
* `meli-last-mile-sql-assessment.LAstmile.routes_new` (`r`)
* `meli-last-mile-sql-assessment.LAstmile.distribution_centers` (`dc`) ON `r.center_id = dc.center_id`
* `meli-last-mile-sql-assessment.LAstmile.vehicle_types` (`vt`) ON `r.vehicle_type_id = vt.vehicle_type_id`

## 2. Dynamic Deduplication Logic (A4)

Duplicate shipment IDs within the raw `shipments_new` table (~7.95% duplication rate) will skew capacity utilization metrics if not mitigated. Before joining shipments with routes, a Common Table Expression (CTE) deduplicates the records dynamically:

```sql
WITH deduped_shipments AS (
  SELECT 
    shipment_id,
    route_id
  FROM (
    SELECT 
      shipment_id,
      route_id,
      ROW_NUMBER() OVER(
        PARTITION BY shipment_id 
        ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC
      ) AS rn
    FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`
  )
  WHERE rn = 1
),
```

Then, the deduplicated counts per route are compiled in an intermediate CTE:

```sql
route_shipment_counts AS (
  SELECT 
    route_id, 
    COUNT(shipment_id) AS shipment_count
  FROM deduped_shipments
  GROUP BY route_id
)
```

## 3. Productivity Metric Formulations (A3, A5)

### Stops Efficiency
Calculated at the country level using `SAFE_DIVIDE` to avoid division-by-zero errors in case of missing or zero estimated stops:
```sql
ROUND(SAFE_DIVIDE(SUM(r.actual_stops), SUM(r.estimated_stops)) * 100, 2) AS stops_efficiency_pct
```

### Capacity Utilization
Measures the physical volume of packages carried relative to the maximum vehicle load limits:
```sql
ROUND(SAFE_DIVIDE(SUM(s.shipment_count), SUM(vt.max_capacity_units)) * 100, 2) AS capacity_utilization_pct
```

### Core Aggregation Query
The query to generate the country-level productivity metrics is structured as follows:

```sql
SELECT 
  dc.country,
  COUNT(DISTINCT r.route_id) AS total_completed_routes,
  SUM(r.estimated_stops) AS total_estimated_stops,
  SUM(r.actual_stops) AS total_actual_stops,
  ROUND(SAFE_DIVIDE(SUM(r.actual_stops), SUM(r.estimated_stops)) * 100, 2) AS stops_efficiency_pct,
  SUM(s.shipment_count) AS total_shipments_carried,
  SUM(vt.max_capacity_units) AS total_max_capacity,
  ROUND(SAFE_DIVIDE(SUM(s.shipment_count), SUM(vt.max_capacity_units)) * 100, 2) AS capacity_utilization_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc 
  ON r.center_id = dc.center_id
JOIN `meli-last-mile-sql-assessment.LAstmile.vehicle_types` vt 
  ON r.vehicle_type_id = vt.vehicle_type_id
LEFT JOIN route_shipment_counts s 
  ON r.route_id = s.route_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
GROUP BY dc.country
ORDER BY stops_efficiency_pct DESC;
```

## 4. Underperforming Route Analysis (A6)

Underperforming routes are defined as routes where the stops efficiency is strictly less than 60%. The query below compiles the total count and proportion of underperforming routes by country:

```sql
SELECT
  dc.country,
  COUNT(DISTINCT r.route_id) AS total_completed_routes,
  COUNTIF(SAFE_DIVIDE(r.actual_stops, r.estimated_stops) < 0.60) AS underperforming_routes_count,
  ROUND(COUNTIF(SAFE_DIVIDE(r.actual_stops, r.estimated_stops) < 0.60) / COUNT(DISTINCT r.route_id) * 100, 2) AS underperforming_pct
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc
  ON r.center_id = dc.center_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
GROUP BY dc.country
ORDER BY underperforming_pct DESC;
```

## 5. Brazil Outliers Zoom (A7)

For the detailed analysis of the worst-performing routes in Brazil (where the bulk of volume and potential inefficency exists), we isolate individual completed delivery routes with a stops efficiency below 60%, ordered ascending:

```sql
SELECT 
  r.route_id,
  p.partner_name,
  vt.vehicle_type_name,
  r.estimated_stops,
  r.actual_stops,
  ROUND(SAFE_DIVIDE(r.actual_stops, r.estimated_stops) * 100, 2) AS stops_efficiency_pct,
  COALESCE(s.shipment_count, 0) AS shipments_carried,
  vt.max_capacity_units AS vehicle_capacity
FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` r
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc 
  ON r.center_id = dc.center_id
JOIN `meli-last-mile-sql-assessment.LAstmile.vehicle_types` vt 
  ON r.vehicle_type_id = vt.vehicle_type_id
LEFT JOIN `meli-last-mile-sql-assessment.LAstmile.partners` p
  ON r.partner_id = p.partner_id
LEFT JOIN route_shipment_counts s 
  ON r.route_id = s.route_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND dc.country = 'BR'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  AND SAFE_DIVIDE(r.actual_stops, r.estimated_stops) < 0.60
ORDER BY stops_efficiency_pct ASC, r.estimated_stops DESC
LIMIT 5;
```

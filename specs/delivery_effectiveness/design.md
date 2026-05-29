# Data Design — LM-003 (Effectiveness - Delivery Rate)

This document describes the design patterns, SQL structures, and statistical mitigation strategies designed to satisfy requirements `A1` through `A6`.

## 1. Target Schema & Associations (A1, A2)

To analyze last-mile delivery effectiveness, the database design associates shipment logs with routes and master metadata tables:
* `meli-last-mile-sql-assessment.LAstmile.shipments_new` (`s`) — contains individual package status information.
* `meli-last-mile-sql-assessment.LAstmile.routes_new` (`r`) — contains route dates, status, types, and links shipments to hubs.
* `meli-last-mile-sql-assessment.LAstmile.distribution_centers` (`dc`) — contains geographic mapping (country code).
* `meli-last-mile-sql-assessment.LAstmile.partners` (`p`) — contains carrier names.

Key relationships:
* `s.route_id = r.route_id`
* `r.center_id = dc.center_id`
* `r.partner_id = p.partner_id`

## 2. Dynamic Deduplication Logic (A3)

Due to a ~7.95% duplication rate in `shipments_new` (where multiple status updates result in duplicate `shipment_id` primary keys), counting raw records directly will distort effectiveness metrics. We isolate the latest status for each package using a window-partitioned CTE:

```sql
WITH deduped_shipments AS (
  SELECT 
    shipment_id, 
    route_id,
    last_status_detail
  FROM (
    SELECT 
      shipment_id, 
      route_id,
      last_status_detail,
      ROW_NUMBER() OVER(
        PARTITION BY shipment_id 
        ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC
      ) as rn
    FROM `meli-last-mile-sql-assessment.LAstmile.shipments_new`
  )
  WHERE rn = 1
)
```

## 3. Effectiveness Metric Formulation (A4)

Delivery success rate represents the proportion of dispatched packages that reach a final status of `'delivered'`.

### Mathematical Formulation
$$SuccessRate = \frac{\sum [last\_status\_detail = 'delivered']}{TotalDeduplicatedShipments} \times 100$$

### SQL Expression
Using `SAFE_DIVIDE` ensures that routes or partners with zero shipments do not cause division-by-zero run-time errors:
```sql
ROUND(
  SAFE_DIVIDE(
    COUNT(CASE WHEN s.last_status_detail = 'delivered' THEN 1 END), 
    COUNT(s.shipment_id)
  ) * 100, 
  2
) AS success_rate_pct
```

## 4. Partner Effectiveness Aggregation Query

The query compiles shipment volumes and success rates grouped by country and partner:

```sql
SELECT 
  dc.country,
  r.partner_id,
  p.partner_name,
  COUNT(s.shipment_id) as total_shipments,
  COUNT(CASE WHEN s.last_status_detail = 'delivered' THEN 1 END) as delivered_shipments,
  ROUND(
    SAFE_DIVIDE(
      COUNT(CASE WHEN s.last_status_detail = 'delivered' THEN 1 END), 
      COUNT(s.shipment_id)
    ) * 100, 
    2
  ) as success_rate_pct
FROM deduped_shipments s
JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` r
  ON s.route_id = r.route_id
JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc
  ON r.center_id = dc.center_id
JOIN `meli-last-mile-sql-assessment.LAstmile.partners` p
  ON r.partner_id = p.partner_id
WHERE r.route_type = 'DELIVERY'
  AND r.route_status = 'COMPLETED'
  AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
GROUP BY dc.country, r.partner_id, p.partner_name
ORDER BY dc.country, success_rate_pct DESC;
```

## 5. Statistical Diagnostics & Mitigations (A5, A6)

### A. Synthetic Homogeneity Diagnosis (A5)
The network-wide success rate is ~80.8% across all countries. In a real-world supply chain, country-level delivery success rates vary significantly due to local infrastructure, customs, weather, geography, and urban density. 
* **Design Strategy**: Compare country-level aggregates using a unified SQL query. If every country has a success rate within $\pm 0.5\%$ of 80.8%, this uniform probability distribution confirms a synthetic data signature rather than organic operations.

### B. Sample Size Variance Analysis (A6)
Some carriers might report outlier success rates (e.g., exactly 100.0% or < 60.0%). 
* **Anomalous Outlier Handling**: To prevent penalizing or praising carriers incorrectly, we flag low-volume partners. If a partner has a low shipment count (e.g., $N < 100$ shipments), any deviation is likely a statistical artifact (law of small numbers) rather than operational failure or excellence.
* **SQL Diagnostic Query for Outliers**:
  ```sql
  SELECT 
    dc.country,
    p.partner_name,
    COUNT(s.shipment_id) as total_shipments,
    ROUND(
      SAFE_DIVIDE(
        COUNT(CASE WHEN s.last_status_detail = 'delivered' THEN 1 END), 
        COUNT(s.shipment_id)
      ) * 100, 
      2
    ) as success_rate_pct
  FROM deduped_shipments s
  JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` r
    ON s.route_id = r.route_id
  JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc
    ON r.center_id = dc.center_id
  JOIN `meli-last-mile-sql-assessment.LAstmile.partners` p
    ON r.partner_id = p.partner_id
  WHERE r.route_type = 'DELIVERY'
    AND r.route_status = 'COMPLETED'
    AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
  GROUP BY dc.country, p.partner_name
  HAVING total_shipments < 100 OR success_rate_pct > 95.0 OR success_rate_pct < 70.0
  ORDER BY total_shipments ASC;
  ```

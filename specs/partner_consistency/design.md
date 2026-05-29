# Data Design — LM-006 (Partner Consistency)

This document describes the design patterns, SQL structures, and mitigation strategies designed to satisfy requirements `A1` through `A9` for auditing partner `PT-014` (SaoPauloShip).

## 1. Stale Route and Closure Metrics (A1, A2)
* **Rationale**: In-progress routes with old dates distort delivery cycle-time averages and SLA calculations. Since they lack an actual end time, they must be separated from travel duration analysis.
* **SQL Design**:
  We calculate the route status distribution and closure rate for `PT-014`:
  ```sql
  WITH partner_routes AS (
    SELECT
      r.route_id,
      r.partner_id,
      r.route_status,
      r.route_date
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r
    WHERE r.partner_id = 'PT-014'
  )
  SELECT
    pr.partner_id,
    COUNT(pr.route_id) AS total_routes,
    COUNTIF(pr.route_status = 'IN_PROGRESS') AS stale_routes_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'IN_PROGRESS'), COUNT(pr.route_id)) * 100, 2) AS stale_routes_pct,
    COUNTIF(pr.route_status = 'COMPLETED') AS completed_routes_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'COMPLETED'), COUNT(pr.route_id)) * 100, 2) AS route_closure_rate
  FROM partner_routes AS pr
  GROUP BY pr.partner_id;
  ```

## 2. GPS & Chronological Integrity Checks (A3, A4)
* **Rationale**: Routes where the actual end time is before the start time represent severe data corruption. Similarly, completed routes missing physical start or end times denote GPS failures.
* **SQL Design**:
  We profile the rate of chronological violations and missing timestamps for completed routes:
  ```sql
  WITH partner_routes AS (
    SELECT
      r.route_id,
      r.partner_id,
      r.route_status,
      r.actual_route_start_time,
      r.actual_route_end_time
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r
    WHERE r.partner_id = 'PT-014'
  )
  SELECT
    pr.partner_id,
    COUNT(pr.route_id) AS total_routes,
    COUNTIF(pr.route_status = 'COMPLETED') AS completed_routes,
    COUNTIF(pr.route_status = 'COMPLETED' AND pr.actual_route_end_time < pr.actual_route_start_time) AS chrono_violations_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'COMPLETED' AND pr.actual_route_end_time < pr.actual_route_start_time), COUNTIF(pr.route_status = 'COMPLETED')) * 100, 2) AS chrono_violations_pct,
    COUNTIF(pr.route_status = 'COMPLETED' AND (pr.actual_route_start_time IS NULL OR pr.actual_route_end_time IS NULL)) AS gps_sync_failures_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'COMPLETED' AND (pr.actual_route_start_time IS NULL OR pr.actual_route_end_time IS NULL)), COUNTIF(pr.route_status = 'COMPLETED')) * 100, 2) AS gps_sync_failures_pct
  FROM partner_routes AS pr
  GROUP BY pr.partner_id;
  ```

## 3. Multi-Hub Overlap and Vehicle Allocation Logic (A5, A6)
* **Rationale**: A regional carrier or single vehicle cannot operate simultaneously across different distribution hubs that are geographically separated. Identifying these overlaps reveals whether logs are synthetic or credentials are being shared.
* **SQL Design**:
  We self-join `routes_new` on `partner_id` and `route_date` to find overlapping active intervals:
  ```sql
  WITH overlapping_routes AS (
    SELECT
      r1.partner_id,
      r1.route_date,
      r1.route_id AS route_a_id,
      r2.route_id AS route_b_id,
      r1.center_id AS hub_a,
      r2.center_id AS hub_b,
      r1.vehicle_type_id AS vehicle_a,
      r2.vehicle_type_id AS vehicle_b,
      r1.actual_route_start_time AS start_a,
      r1.actual_route_end_time AS end_a,
      r2.actual_route_start_time AS start_b,
      r2.actual_route_end_time AS end_b
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r1
    INNER JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r2
      ON r1.partner_id = r2.partner_id
      AND r1.route_date = r2.route_date
      AND r1.route_id < r2.route_id
    WHERE r1.partner_id = 'PT-014'
      AND r1.actual_route_start_time IS NOT NULL
      AND r1.actual_route_end_time IS NOT NULL
      AND r2.actual_route_start_time IS NOT NULL
      AND r2.actual_route_end_time IS NOT NULL
      AND r2.actual_route_start_time < r1.actual_route_end_time
      AND r2.actual_route_end_time > r1.actual_route_start_time
  )
  SELECT
    ol.partner_id,
    COUNT(DISTINCT ol.route_a_id) + COUNT(DISTINCT ol.route_b_id) AS total_overlapping_routes_estimate,
    COUNTIF(ol.hub_a != ol.hub_b) AS multi_hub_overlaps_count,
    COUNTIF(ol.vehicle_a = ol.vehicle_b AND ol.hub_a != ol.hub_b) AS impossible_vehicle_allocations_count
  FROM overlapping_routes AS ol
  GROUP BY ol.partner_id;
  ```

## 4. Contract Expiration Integrity Check (A7)
* **Rationale**: Analyzing routes operated by contractors with expired agreements or deactivated contract flags ensures compliance with procurement governance and prevents billing leakage.
* **SQL Design**:
  ```sql
  WITH expired_allocations AS (
    SELECT
      r.route_id,
      r.partner_id,
      r.route_date,
      p.partner_name,
      p.active_flag,
      p.contract_end_date
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r
    INNER JOIN `meli-last-mile-sql-assessment.LAstmile.partners` AS p
      ON r.partner_id = p.partner_id
    WHERE r.partner_id = 'PT-014'
      AND (r.route_date > p.contract_end_date OR p.active_flag = 0)
  )
  SELECT
    ea.partner_id,
    ea.partner_name,
    COUNT(ea.route_id) AS routes_after_expiration_count,
    MIN(ea.route_date) AS earliest_violation_date,
    MAX(ea.route_date) AS latest_violation_date
  FROM expired_allocations AS ea
  GROUP BY ea.partner_id, ea.partner_name;
  ```

## 5. Unified Audit Query for PT-014 Consistency Profiling (A8, A9)
* **Rationale**: Combines all data quality metrics into a single row to formulate a definitive recommendation for reporting governance.
* **SQL Design**:
  ```sql
  WITH partner_routes AS (
    SELECT
      r.route_id,
      r.partner_id,
      r.route_status,
      r.route_date,
      r.center_id,
      r.vehicle_type_id,
      r.actual_route_start_time,
      r.actual_route_end_time,
      p.partner_name,
      p.active_flag,
      p.contract_end_date
    FROM `meli-last-mile-sql-assessment.LAstmile.routes_new` AS r
    INNER JOIN `meli-last-mile-sql-assessment.LAstmile.partners` AS p
      ON r.partner_id = p.partner_id
    WHERE r.partner_id = 'PT-014'
  ),
  overlapping_routes AS (
    SELECT
      r1.route_id AS route_a_id,
      r2.route_id AS route_b_id,
      r1.center_id AS hub_a,
      r2.center_id AS hub_b,
      r1.vehicle_type_id AS vehicle_a,
      r2.vehicle_type_id AS vehicle_b
    FROM partner_routes AS r1
    INNER JOIN partner_routes AS r2
      ON r1.route_date = r2.route_date
      AND r1.route_id < r2.route_id
    WHERE r1.actual_route_start_time IS NOT NULL
      AND r1.actual_route_end_time IS NOT NULL
      AND r2.actual_route_start_time IS NOT NULL
      AND r2.actual_route_end_time IS NOT NULL
      AND r2.actual_route_start_time < r1.actual_route_end_time
      AND r2.actual_route_end_time > r1.actual_route_start_time
  )
  SELECT
    pr.partner_id,
    pr.partner_name,
    COUNT(DISTINCT pr.route_id) AS total_routes_assigned,
    COUNTIF(pr.route_status = 'IN_PROGRESS') AS stale_in_progress_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'IN_PROGRESS'), COUNT(DISTINCT pr.route_id)) * 100, 2) AS stale_in_progress_pct,
    COUNTIF(pr.route_status = 'COMPLETED') AS completed_routes_count,
    COUNTIF(pr.route_status = 'COMPLETED' AND pr.actual_route_end_time < pr.actual_route_start_time) AS chrono_violations_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'COMPLETED' AND pr.actual_route_end_time < pr.actual_route_start_time), COUNTIF(pr.route_status = 'COMPLETED')) * 100, 2) AS chrono_violations_pct,
    COUNTIF(pr.route_status = 'COMPLETED' AND (pr.actual_route_start_time IS NULL OR pr.actual_route_end_time IS NULL)) AS gps_sync_failures_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_status = 'COMPLETED' AND (pr.actual_route_start_time IS NULL OR pr.actual_route_end_time IS NULL)), COUNTIF(pr.route_status = 'COMPLETED')) * 100, 2) AS gps_sync_failures_pct,
    (SELECT COUNT(DISTINCT route_a_id) + COUNT(DISTINCT route_b_id) FROM overlapping_routes) AS overlapping_routes_estimate,
    (SELECT COUNTIF(hub_a != hub_b) FROM overlapping_routes) AS multi_hub_overlaps_count,
    (SELECT COUNTIF(vehicle_a = vehicle_b AND hub_a != hub_b) FROM overlapping_routes) AS impossible_vehicle_allocations_count,
    COUNTIF(pr.route_date > pr.contract_end_date OR pr.active_flag = 0) AS contract_expired_routes_count,
    ROUND(SAFE_DIVIDE(COUNTIF(pr.route_date > pr.contract_end_date OR pr.active_flag = 0), COUNT(DISTINCT pr.route_id)) * 100, 2) AS contract_expired_routes_pct
  FROM partner_routes AS pr
  GROUP BY pr.partner_id, pr.partner_name;
  ```

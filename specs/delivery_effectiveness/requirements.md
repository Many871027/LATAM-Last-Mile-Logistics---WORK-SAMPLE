# Analytical Requirements — LM-003 (Effectiveness - Delivery Rate)

This document defines the analytical and data quality requirements for measuring last-mile delivery effectiveness. All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### Scope & Filtering
* **A1: Completed Delivery Route Filtering (State-Driven)**
  * **State**: WHILE calculating delivery effectiveness metrics for April-May 2025,
  * **System Response**: THEN the system shall filter for completed delivery routes (`route_type = 'DELIVERY'` and `route_status = 'COMPLETED'`) with a route date between '2025-04-01' and '2025-05-31'.

* **A2: Regional & Partner Association (State-Driven)**
  * **State**: WHILE calculating effectiveness metrics by partner and country,
  * **System Response**: THEN the system shall join the shipments table with the routes table, the distribution centers table, and the partners table to associate each shipment with its corresponding country and carrier partner.

### Data Quality & Deduplication
* **A3: Dynamic Shipment Deduplication (Unwanted Behavior)**
  * **Undesired Condition**: IF the shipments table contains duplicate records for the same `shipment_id`,
  * **System Response**: THEN the analytical query shall dynamically deduplicate shipments using a row number window function partition (`ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)`) before joining, ensuring each unique shipment is evaluated at most once.

### Effectiveness Calculations
* **A4: Success Rate Calculation (Ubiquitous)**
  * **System Response**: The system shall compute the Delivery Success Rate (`success_rate_pct`) by dividing the sum of shipments with `last_status_detail = 'delivered'` by the total count of deduplicated shipments, utilizing `SAFE_DIVIDE` to prevent division-by-zero errors.

### Operational & Statistical Auditing
* **A5: Synthetic Homogeneity Detection (Ubiquitous)**
  * **System Response**: The system shall analyze country-level and partner-level success rates to evaluate if they cluster unnaturally close to the network baseline (~80.8%), flagging this uniformity as evidence of a synthetic data footprint.

* **A6: Sample Size Variance Verification (Unwanted Behavior)**
  * **Undesired Condition**: IF a carrier partner exhibits a success rate that deviates significantly from the network baseline (e.g., 100% or < 70%),
  * **System Response**: THEN the system shall retrieve and display the partner's total shipment volume (sample size) to determine if the deviation is a statistical artifact caused by a low volume of packages.

# Analytical Requirements — LM-002 (Productivity - Route Utilization)

This document defines the analytical and data quality requirements for measuring route utilization efficiency. All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### Route Isolation & Filtering
* **A1: Completed Delivery Route Filtering (State-Driven)**
  * **State**: WHILE calculating route productivity metrics for April-May 2025,
  * **System Response**: THEN the system shall filter for completed delivery routes (`route_type = 'DELIVERY'` and `route_status = 'COMPLETED'`) with a route date between '2025-04-01' and '2025-05-31'.

* **A2: Regional Hub Association (State-Driven)**
  * **State**: WHILE calculating metrics by country,
  * **System Response**: THEN the system shall join the routes table with the distribution centers table to associate each route with its corresponding country.

### Performance Metric Calculations
* **A3: Stops Efficiency Calculation (Ubiquitous)**
  * **System Response**: The system shall compute regional Stops Efficiency by dividing the sum of actual stops by the sum of estimated stops, using `SAFE_DIVIDE` to prevent division-by-zero errors.

* **A4: Dynamic Shipment Count Deduplication (Unwanted Behavior)**
  * **Undesired Condition**: IF the shipments table contains duplicate records for the same `shipment_id`,
  * **System Response**: THEN the system shall dynamically deduplicate shipments using a row number window function partition before joining, ensuring each unique shipment is counted at most once per route.

* **A5: Capacity Utilization Calculation (Ubiquitous)**
  * **System Response**: The system shall compute Capacity Utilization by dividing the sum of deduplicated shipment counts by the sum of maximum capacity units from the vehicle types table, using `SAFE_DIVIDE`.

### Underperformance Analysis
* **A6: Underperforming Route Identification (State-Driven)**
  * **State**: WHILE identifying underperforming routes,
  * **System Response**: THEN the system shall filter for completed delivery routes where the ratio of actual stops to estimated stops is strictly less than 60%.

* **A7: Worst Route Profiling (Event-Driven)**
  * **Trigger**: WHEN generating detailed reports for underperforming routes in Brazil,
  * **System Response**: THEN the system shall retrieve and display the worst performing routes by stops efficiency, including their route ID, partner name, vehicle type, planned stops, actual stops, stops efficiency, shipments carried, and vehicle capacity.

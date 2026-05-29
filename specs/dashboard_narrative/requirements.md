# Analytical Requirements — LM-007 (Dashboard & Strategic Narrative)

This document defines the analytical, visualization, and strategic reporting requirements for synthesizing the last-mile operational findings from Q1 through Q6. All requirements are drafted using strict EARS-BI (Easy Approach to Requirements Syntax for Business Intelligence) notation.

## Requirements Specification

### 1. Narrative Synthesizing & Localization
* **A1: Narrative Synthesis and Language (Ubiquitous)**
  * **System Response**: The strategic narrative SHALL synthesize the operational insights and data quality findings from Q1 through Q6 into a professional document written in Spanish, saved under `Reports/Question_7_Dashboard_Strategic_Narrative.md`.

* **A2: Narrative Length and Depth (Ubiquitous)**
  * **System Response**: The strategic narrative document SHALL contain sufficient operational depth to span approximately 2 to 3 pages (approximately 1,000 to 1,500 words of technical and logistical analysis).

* **A3: Operational Story Structure (Ubiquitous)**
  * **System Response**: The narrative document SHALL follow a structured "Problem -> Evidence -> Action" (Problema -> Evidencia -> Acción) format for each operational issue described.

### 2. Dashboard Mockups & ASCII Wireframes
* **A4: Dashboard Visual Mockups (Ubiquitous)**
  * **System Response**: The dashboard specification SHALL include ASCII wireframe layouts representing a professional BI dashboard interface for logistics monitoring.

* **A5: Operational KPI Representation (Ubiquitous)**
  * **System Response**: The dashboard wireframes SHALL display key operational performance indicators, specifically Stops Efficiency, Capacity Utilization, Delivery Success Rate, OTH (On-Time Handling) by End Time, OTH by Duration, OTH Gap, and Carrier Error Rates.

### 3. Timezone & Telemetry Quality reporting
* **A6: Timezone Illusion Clarification (State-Driven)**
  * **State**: WHILE reporting on late-night delivery risks and operational schedules,
  * **System Response**: THEN the narrative and dashboard SHALL explain the UTC-to-local offset correction (using `TIMESTAMP_ADD`) and display the corrected local late-night delivery rates (0.73% for BR, 3.12% for CO, 5.64% for MX, 3.94% for PE) to prevent false operational alarms.

* **A7: Event Hour Telemetry Corruption Disclosure (State-Driven)**
  * **State**: WHILE documenting telemetry and log data quality issues,
  * **System Response**: THEN the narrative SHALL disclose the ETL truncation corruption in the precalculated `event_hour_utc` column (where hours >= 20 UTC are truncated to 0) and mandate using dynamic timestamp extraction.

### 4. Carrier Consistency & Governance Reporting
* **A8: Carrier Exclusion and Governance (State-Driven)**
  * **State**: WHILE evaluating carrier performance and reporting SLA compliance,
  * **System Response**: THEN the narrative and dashboard SHALL justify the analytical exclusion of partner PT-014 (SaoPauloShip) based on the 5% error threshold (PT-014 error rate is 51.85%) and highlight the 100% post-expiration operations (378 routes).

### 5. Strategic Recommendations Action Plan
* **A9: Fleet Capacity Optimization Recommendation (Ubiquitous)**
  * **System Response**: The narrative SHALL recommend a fleet reallocation action plan for the Cono Sur based on the low capacity utilization in Argentina (48.23%) and Chile (51.19%) despite their high stops efficiency (>90%).

* **A10: Warehouse Departure Audits Recommendation (Ubiquitous)**
  * **System Response**: The narrative SHALL recommend warehouse dispatch audits based on the positive OTH gap (e.g., Rio Express Van Large with +12.34 p.p. gap) to mitigate departure latency.

* **A11: API Integrations and Data Validation Rules (Ubiquitous)**
  * **System Response**: The narrative SHALL recommend API integrations and real-time TMS validation rules to prevent future occurrences of chronological violations, GPS synchronization issues, and routes operated post contract expiration.

### 6. Looker Studio & BigQuery MCP Toolbox Integration
* **A12: Looker Studio MCP Toolbox Secure Data Layer (Ubiquitous)**
  * **System Response**: The last-mile dashboard architecture SHALL mandate that all KPI data is retrieved securely through parameterized database tools defined in a `tools.yaml` configuration file served by the `toolbox.exe` executable.

* **A13: Query Restrictions and Parameter Validation (State-Driven)**
  * **State**: WHILE dashboard clients are querying last-mile operational metrics (Route Productivity, Delivery Effectiveness, OTH schedule metrics, Timezone/log corruption metrics, and Carrier consistency metrics),
  * **System Response**: THEN the MCP Toolbox middleware (`toolbox.exe`) SHALL restrict queries to the pre-registered database tools defined in `tools.yaml` and validate that all input parameters match the declared schemas.


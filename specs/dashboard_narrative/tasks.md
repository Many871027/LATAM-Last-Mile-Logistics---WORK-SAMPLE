# Implementation Plan — LM-007 (Dashboard & Strategic Narrative)

This document maps the analytical requirements to discrete, testable work units to be executed sequentially under `specs/dashboard_narrative/`.

- [x] T1: Setup Narrative Structure & Spanish Language Baseline
  * Initialize the markdown report file under `Reports/Question_7_Dashboard_Strategic_Narrative.md` in Spanish.
  * Formulate titles, subtitles, versioning metadata, and the Executive Summary section.
  * _Requirements: A1, A2, A3_

- [x] T2: Formulate Dashboard Visual Mockup Layouts (ASCII Wireframes)
  * Design and document the main Tab 1 layout (Operational KPIs & Regional Performance Table).
  * Design and document Tab 2 layout (Timezone Illusion Table & dynamic log hour corruption table).
  * Design and document Tab 3 layout (OTH Gap Analysis and departure latency tables).
  * Design and document Tab 4 layout (PT-014 SaoPauloShip consistency audit & exclusion indicators).
  * _Requirements: A4, A5_

- [x] T3: Section 2 Story A (Cono Sur Capacity Utilization Audit)
  * Draft the operational story for Argentina (48.23% capacity utilization) and Chile (51.19% capacity utilization) detailing fleet size imbalance.
  * Explain the 1:1 packet-to-stop ratio constraint and recommend vehicle resizing and route consolidation.
  * _Requirements: A3, A8_

- [x] T4: Section 2 Story B (OTH Gap Analysis & Dispatch Latency)
  * Draft the OTH gap analysis story, detailing the differences between OTH by Duration and OTH by End Time (ranging up to +12.34 p.p.).
  * Document the performance drop during peak hours (11:00-18:00) vs. night-time improvement.
  * Propose warehouse staging audits and SLA penalties.
  * _Requirements: A3, A9_

- [x] T5: Section 2 Story C (Timezone Illusion and event_hour_utc Bug)
  * Draft the timezone illusion story, adjusting UTC delivery logs to local time offsets.
  * Reference the local delivery rates (0.73% for BR/AR vs. 5.64% for MX).
  * Detail the ETL truncation bug (100% corruption of event hours >= 20 UTC).
  * Propose ETL correction and timezone-aware semantical layers.
  * _Requirements: A6, A7_

- [x] T6: Section 2 Story D (PT-014 Governance Audit & Exclusion)
  * Draft the compliance and consistency story for partner PT-014.
  * Report the 100% post-expiration operation (378 routes) and the 51.85% telemetry/GPS error rate.
  * Implement the 5% error rule justification to exclude the carrier from BI reporting.
  * Propose TMS contract validations and procurement audits.
  * _Requirements: A8_

- [x] T7: Finalization of Strategic Recommendations Matrix & Metric Validation
  * Compile a comprehensive recommendations table synthesizing operational actions, target KPIs, and priority levels.
  * Verify all numerical references across the narrative against the official reports of Q1-Q6 to ensure 100% consistency.
  * _Requirements: A10, A11_

- [x] T8: Design and Generate tools.yaml Configuration File
  * Create the `tools.yaml` configuration file in the workspace root.
  * Define the five tools (`get_route_productivity`, `get_delivery_effectiveness`, `get_oth_schedule_metrics`, `get_timezone_log_corruption_metrics`, and `get_carrier_consistency_metrics`) with exact descriptions, parameters, and fully capitalized SQL template queries.
  * _Requirements: A12_

- [x] T9: Verify MCP Toolbox Configuration and Execution
  * Inspect the syntax and structure of `tools.yaml` to ensure it is valid YAML.
  * Propose and run the `toolbox.exe` executable using the config flag (`.\toolbox.exe --config tools.yaml`) to verify the local MCP server starts and parses the configurations successfully.
  * _Requirements: A12, A13_

- [x] T10: Create a Single Unified Python Script for Spec Execution
  * Create a single, unified Python script (e.g. test suite integration or separate execution script) that aggregates and executes all operations, queries, and report generation procedures defined in the preceding tasks of this specification.
  * _Requirements: A12, A13_


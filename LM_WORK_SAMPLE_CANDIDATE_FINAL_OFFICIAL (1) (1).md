# LAST MILE OPERATIONS - SQL WORK SAMPLE

**Duration:** 90-120 minutes  
**Language:** English  
**Level:** Senior BI Analyst / SQL Operations  
**Scope:** Logistics & Last Mile Analysis (LATAM)

---

## ⚠️ CRITICAL PRINCIPLE: Understanding Unfamiliar Data

**This assessment tests a critical senior analyst skill:** The ability to work confidently with data systems you did not create and may not fully understand at first glance.

In real-world analytics, you will rarely own the data. You'll inherit tables from legacy systems, work with datasets designed by other teams, and analyze business domains you're learning. The ability to:
- **Explore** tables systematically
- **Audit** data quality before making claims
- **Understand** the business meaning behind data
- **Question** assumptions and validate metrics

...is what separates junior analysts from senior operators.

**Do not assume the data is clean.** Many production datasets have:
- Duplicate or inconsistent naming
- NULL values in unexpected places
- Broken foreign key relationships
- Fields with complex logic (flags with undocumented values, timestamps in different timezones)
- Metrics that conflict with each other

Your job is to discover these issues, document them, and make defensible decisions about how to proceed.

---

## 📋 CONTEXT

You're analyzing Last Mile (LM) operations for a logistics company across Latin America (Mexico, Brazil, Argentina, Colombia, Chile, Peru). Your role is to audit data quality, identify operational inefficiencies, calculate key performance metrics, and synthesize findings into strategic insights.

**Key Performance Indicators (KPIs):**
- **Productivity:** How efficiently are routes being utilized?
- **Effectiveness:** What % of shipments dispatched actually get delivered?
- **OTH (On-Time Handling):** Are routes completing within planned hours?
- **SPR (Shipments Per Route):** Average packages handled per route

---

## 📊 DATA MODEL

### TABLE 1: `distribution_centers`
Regional distribution hubs (delivery and pickup centers).

| Column | Type | Description |
|--------|------|-------------|
| center_id | STRING | Unique identifier |
| center_name | STRING | Name of hub |
| country | STRING | 2-letter country code (MX, BR, AR, CO, CL, PE) |
| region | STRING | Regional name |
| center_type | STRING | 'DELIVERY' or 'PICKUP' |
| active_flag | INT64 | 1=active, 0=inactive |
| operational_hours_start | INT64 | Start hour (0-23) |
| operational_hours_end | INT64 | End hour (0-23) |
| max_daily_capacity_units | INT64 | Max shipments/day |
| established_date | DATE | When center opened |
| timezone_offset | INT64 | Offset from UTC-0 (e.g., -6 for Mexico, -3 for Brazil) |

---

### TABLE 2: `partners`
Delivery companies/contractors.

| Column | Type | Description |
|--------|------|-------------|
| partner_id | STRING | Unique ID |
| partner_name | STRING | Company name |
| partner_type | STRING | 'CONTRACTOR', 'CARRIER', 'THIRD_PARTY' |
| country | STRING | Operational country |
| active_flag | INT64 | 1=active, 0=inactive, -1=invalid |
| contract_start_date | DATE | When contract began |
| contract_end_date | DATE | When contract ends (NULL if ongoing) |
| average_delivery_time_hours | FLOAT64 | Historical avg |
| sla_compliance_pct | FLOAT64 | Historical SLA % |

---

### TABLE 3: `vehicle_types`
Vehicle classifications.

| Column | Type | Description |
|--------|------|-------------|
| vehicle_type_id | STRING | Unique ID |
| vehicle_type_name | STRING | Name (motorcycle, van, truck, etc.) |
| max_capacity_units | INT64 | Max shipments per vehicle |
| fuel_type | STRING | FUEL, ELECTRIC, HUMAN |
| active_flag | INT64 | 1=active, 0=inactive |

---

### TABLE 4: `routes`
Daily route assignments (partner + vehicle + center).

| Column | Type | Description |
|--------|------|-------------|
| route_id | STRING | Unique ID |
| partner_id | STRING | Which partner operated |
| vehicle_type_id | STRING | Which vehicle used |
| center_id | STRING | Which distribution center |
| route_date | DATE | Date of route |
| route_type | STRING | 'DELIVERY' OR 'PICKUP' |
| route_status | STRING | 'COMPLETED', 'IN_PROGRESS', 'CANCELLED' |
| planned_route_start_time | TIME | Planned start |
| planned_route_end_time | TIME | Planned end |
| actual_route_start_time | TIME | Actual start (NULL if cancelled) |
| actual_route_end_time | TIME | Actual end (NULL if not completed) |
| route_distance_km | FLOAT64 | Distance traveled |
| estimated_stops | INT64 | Planned deliveries |
| actual_stops | INT64 | Actual deliveries |

---

### TABLE 5: `shipments`
Packages with status history.

| Column | Type | Description |
|--------|------|-------------|
| shipment_id | STRING | Unique ID |
| route_id | STRING | Which route carried it |
| partner_id | STRING | Partner that handled it |
| shipment_date | DATE | Dispatch date |
| shipment_status | STRING | 'DELIVERED', 'IN_TRANSIT', 'PROBLEM', 'CANCELLED' |
| status_change_timestamp | TIMESTAMP | When status changed |
| delivery_attempt_count | INT64 | Number of attempts |
| last_status_detail | STRING | Reason (success, vehicle breakdown, etc.) |

---

### TABLE 6: `shipment_events`
Event log for each shipment (granular tracking).

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event ID |
| shipment_id | STRING | Which shipment |
| center_id | STRING | Which distribution center |
| event_type | STRING | 'picked_up', 'in_transit', 'delivery_attempt', 'delivered' |
| event_timestamp | TIMESTAMP | When event occurred (UTC-0 / GMT) |
| event_hour_utc | INT64 | Hour of event in UTC-0 (0-23) |

---

## ❓ QUESTIONS

### QUESTION 1: Data Audit & Validation
**Objective:** Before analyzing operations, understand the data quality.

**Your task:**
Audit the `routes` and `shipments` tables comprehensively. Identify the main data quality issues that would affect your analysis, explain how you discovered them, and document how you'll handle each issue in subsequent questions. Prioritize by impact.

**Submit:**
- Your audit findings (organized by issue type)
- How you discovered each issue
- Your handling strategy for each issue
- Any concerns or risks you've identified

---

### QUESTION 2: Productivity - Route Utilization
**Objective:** Measure how efficiently routes are being utilized.

**Your task:**
For DELIVERY routes completed in April-May 2025, measure route utilization efficiency. Calculate key metrics by country, identify which routes are significantly underperforming, and explain any data quality decisions you made.

**Submit:**
- Efficiency metrics by country
- Underperforming routes analysis
- Explanation of your approach and data handling

---

### QUESTION 3: Effectiveness - Delivery Rate
**Objective:** Understand delivery success across the network.

**Your task:**
Calculate the delivery effectiveness rate for April-May 2025. Break it down by partner country and identify which partners show unusual effectiveness levels (either exceptionally high or low). What might explain the anomalies?

**Submit:**
- Effectiveness metrics by partner country
- Partners with unusual performance
- Your analysis of what might explain the anomalies

---

### QUESTION 4: OTH - On-Time Handling
**Objective:** Evaluate schedule performance across the network.

**Your task:**
Evaluate on-time delivery performance across partners and vehicle types for completed DELIVERY routes in April-May 2025. Identify which partners/vehicles consistently struggle to meet schedules. Support your findings with metrics.

**Submit:**
- On-time performance by partner and vehicle type
- Partners and vehicles with performance issues
- Supporting analysis

---

### QUESTION 5: Operational Patterns Investigation
**Objective:** Investigate a puzzling operational pattern.

**Your task:**
Leadership is concerned: Brazil and Colombia show significantly more deliveries after 20:00 compared to Mexico or Chile—even though all regions operate similarly. Are these regions really working dangerously long hours, or is something else happening? Investigate and explain what you find.

**Submit:**
- Your investigation findings
- The explanation for the pattern
- Supporting data and analysis

---

### QUESTION 6: Partner Consistency Investigation
**Objective:** Deep-dive into an inconsistent partner.

**Your task:**
PT-014 (SaoPauloShip) shows inconsistent performance metrics across reports. Investigate why this partner's metrics are unstable. Should this partner be included in performance reporting? Support your recommendation with data.

**Submit:**
- Your investigation findings
- Root cause analysis
- Data-backed recommendation on whether to include/exclude PT-014
- Any systemic issues you discovered

---

### QUESTION 7: Operational Dashboard & Strategic Narrative
**Objective:** Synthesize your analysis into a visual story.

**Your task:**
Using the data and findings from your previous analyses (Q1-Q6), create a dashboard that tells a coherent operational story about Last Mile performance in LATAM.

Your dashboard should:
1. Clearly communicate the main operational challenges you discovered
2. Support your findings with visualizations (not just raw numbers)
3. Guide the viewer toward a specific recommendation
4. Have a narrative arc: Problem → Evidence → Action

**Tool options:**
You can use any visualization platform you're comfortable with:
- Looker Studio (free, Google-based)
- Power BI
- Tableau
- Google Sheets with charts
- HTML/CSS/JavaScript
- Any other visualization tool

**Your submission should include:**

1. **The Dashboard** (as screenshot, link, or export file)
   - Multiple visualizations working together to tell one story
   - Clear titles and labels
   - Professional design that guides the eye

2. **Narrative Document** (2-3 pages explaining):
   - What story your dashboard tells
   - Why you structured it this way
   - What specific action you're recommending
   - How the dashboard guides someone to that conclusion

**Example narrative structures (pick one or create your own):**
- **"The Brazil Crisis":** PT-003 and PT-014 underperformance, root causes, action needed
- **"Vehicle Optimization":** Van (Large) excellence vs Truck struggles, cost-benefit, reallocation strategy
- **"The Timezone Illusion":** Apparent late-night deliveries explained, false alarm debunked
- **"Partner Performance Tiers":** Elite vs Poor operators, capability gaps, recommendations

---

## 📝 SUBMISSION FORMAT

**Submit as a SINGLE DOCUMENT PACKAGE containing:**

### Part 1: Analysis Document (Q1-6)
One comprehensive document (Google Doc, PDF, or Word) with:

1. **For Each Question (1-6):**
   - ✓ Your findings and analysis
   - ✓ SQL code (executable in BigQuery with `--use_legacy_sql=false`)
   - ✓ Explanation of your approach
   - ✓ Data quality decisions you made
   - ✓ Your reasoning (not just the answers)

### Part 2: Dashboard & Narrative (Q7)
Two items:

1. **The Dashboard**
   - Visual file (screenshot, link, or exported dashboard)
   - Professional, clear, and compelling

2. **Narrative Document** (2-3 pages)
   - Story explanation
   - Design rationale
   - Recommendation
   - How visualizations support the narrative

### Recommended Overall Structure:
```
# [Your Name] - Last Mile SQL Assessment

## ANALYSIS SECTION (Q1-6)

### Question 1: Data Audit & Validation
[Your findings, approach, SQL, handling strategy]

### Question 2: Productivity - Route Utilization
[Your analysis, metrics, SQL]

...continue for Q3-6...

## STRATEGIC SECTION (Q7)

### Dashboard & Narrative
[Your 2-3 page narrative explaining the story]

### Appendix: Dashboard Visualization
[Screenshot or link to your dashboard]
```

---

## 🌟 BONUS: Going Above and Beyond

This is a real-world assessment. Senior analysts don't just answer the questions asked—they ask the right questions too.

If during your analysis you discover:
- Additional data quality issues worth documenting
- Cross-metric patterns that suggest deeper operational insights
- Alternative hypotheses or explanations you want to explore
- Recommendations for operational improvements
- Better ways to structure or present the data

...include them in your submission. This is where senior thinking shines.

Quality over quantity—one brilliant insight is worth more than five obvious ones.

---

## 🚀 GETTING STARTED

1. Load the 6 CSV tables into BigQuery
2. Start with Question 1 to understand your data
3. Work through Questions 2-6 systematically
4. Create your dashboard and narrative for Question 7
5. Submit your complete analysis package

**This assessment is a real-world simulation.** Senior analysts deal with imperfect data, conflicting metrics, and the need to move from verification to strategy. Show us you can do all three.

Good luck!

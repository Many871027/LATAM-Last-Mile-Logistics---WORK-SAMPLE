import pandas as pd
import numpy as np

print("Loading routes...")
df_routes = pd.read_csv("DB/routes_new.csv")
print("Loading shipments...")
df_shipments = pd.read_csv("DB/shipments_new.csv")
print("Loading distribution centers...")
df_dc = pd.read_csv("DB/distribution_centers.csv")
print("Loading partners...")
df_partners = pd.read_csv("DB/partners.csv")

# 1. Deduplicate shipments
print("Deduplicating shipments...")
# Sort by status_change_timestamp desc, delivery_attempt_count desc
# In case status_change_timestamp is string, we should convert or just sort.
# Let's convert to datetime
df_shipments['status_change_timestamp'] = pd.to_datetime(df_shipments['status_change_timestamp'])
df_shipments = df_shipments.sort_values(
    by=['shipment_id', 'status_change_timestamp', 'delivery_attempt_count'], 
    ascending=[True, False, False]
)
df_shipments_dedup = df_shipments.drop_duplicates(subset=['shipment_id'], keep='first')

# 2. Filter completed delivery routes in April-May 2025
print("Filtering routes...")
df_routes['route_date'] = pd.to_datetime(df_routes['route_date'])
df_routes_filtered = df_routes[
    (df_routes['route_type'] == 'DELIVERY') & 
    (df_routes['route_status'] == 'COMPLETED') & 
    (df_routes['route_date'] >= '2025-04-01') & 
    (df_routes['route_date'] <= '2025-05-31')
]

# 3. Joins
print("Performing joins...")
# Join shipments and routes
df_joined = pd.merge(df_shipments_dedup, df_routes_filtered, on='route_id', how='inner')
# Join with distribution centers to get country
df_joined = pd.merge(df_joined, df_dc, on='center_id', how='inner')
# Join with partners
df_joined = pd.merge(df_joined, df_partners, on='partner_id', how='inner')

# 4. Country aggregates
print("Calculating country aggregates...")
country_summary = df_joined.groupby('country_y').agg(
    total_shipments=('shipment_id', 'count'),
    delivered_shipments=('last_status_detail', lambda x: (x == 'delivered').sum())
).reset_index()
country_summary['success_rate_pct'] = (country_summary['delivered_shipments'] / country_summary['total_shipments'] * 100).round(2)
country_summary = country_summary.sort_values(by='success_rate_pct', ascending=False)
print("\nCountry Summary:")
print(country_summary)

# 5. Partner aggregates
print("Calculating partner aggregates...")
partner_summary = df_joined.groupby(['country_y', 'partner_id', 'partner_name']).agg(
    total_shipments=('shipment_id', 'count'),
    delivered_shipments=('last_status_detail', lambda x: (x == 'delivered').sum())
).reset_index()
partner_summary['success_rate_pct'] = (partner_summary['delivered_shipments'] / partner_summary['total_shipments'] * 100).round(2)
partner_summary = partner_summary.sort_values(by=['country_y', 'success_rate_pct'], ascending=[True, False])
print("\nTop/Bottom Partners:")
# Colombia top
print("\nColombia Top Partners:")
print(partner_summary[partner_summary['country_y'] == 'CO'].head(3))
# Peru bottom
print("\nPeru Bottom Partners:")
print(partner_summary[partner_summary['country_y'] == 'PE'].tail(3))

# Write to file
with open("progress/calculated_metrics_output.txt", "w") as f:
    f.write("Country Summary:\n")
    f.write(country_summary.to_string())
    f.write("\n\nPartner Summary:\n")
    f.write(partner_summary.to_string())
print("Saved to progress/calculated_metrics_output.txt")

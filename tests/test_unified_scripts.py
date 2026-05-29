import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Mock side effect function to return correct data schemas for each BigQuery query
def mock_query_side_effect(query):
    query_lower = query.lower()
    
    class MockJob:
        def __init__(self, df):
            self.df = df
        def to_dataframe(self):
            return self.df
            
    if 'shipments_new pk duplication' in query_lower:
        df = pd.DataFrame([{
            'audit_check': 'shipments_new PK Duplication',
            'total_records': 1000,
            'error_count': 80,
            'error_pct': 8.0
        }, {
            'audit_check': 'routes_new Chrono Violations',
            'total_records': 500,
            'error_count': 50,
            'error_pct': 10.0
        }, {
            'audit_check': 'shipment_events_new Hour Corruption',
            'total_records': 2000,
            'error_count': 1700,
            'error_pct': 85.0
        }, {
            'audit_check': 'routes_new Missing Partners',
            'total_records': 500,
            'error_count': 10,
            'error_pct': 2.0
        }, {
            'audit_check': 'partners Deprecated Contracts',
            'total_records': 55,
            'error_count': 1,
            'error_pct': 1.82
        }])
        return MockJob(df)
        
    elif 'limit 5' in query_lower:
        df = pd.DataFrame([{
            'route_id': f'R{i}',
            'partner_name': f'Partner {i}',
            'vehicle_type_name': 'Van',
            'estimated_stops': 10,
            'actual_stops': 3,
            'stops_efficiency_pct': 30.0,
            'shipments_carried': 5,
            'vehicle_capacity': 10
        } for i in range(1, 6)])
        return MockJob(df)
        
    elif 'vt.max_capacity_units' in query_lower:
        df = pd.DataFrame([{
            'country': 'BR',
            'total_completed_routes': 100,
            'total_estimated_stops': 1000,
            'total_actual_stops': 900,
            'stops_efficiency_pct': 90.0,
            'total_shipments_carried': 650,
            'total_max_capacity': 1000,
            'capacity_utilization_pct': 65.0
        }, {
            'country': 'AR',
            'total_completed_routes': 50,
            'total_estimated_stops': 500,
            'total_actual_stops': 450,
            'stops_efficiency_pct': 90.0,
            'total_shipments_carried': 240,
            'total_max_capacity': 500,
            'capacity_utilization_pct': 48.0
        }])
        return MockJob(df)
        
    elif 'underperforming_routes_count' in query_lower:
        df = pd.DataFrame([{
            'country': 'BR',
            'total_completed_routes': 100,
            'underperforming_routes_count': 15,
            'underperforming_pct': 15.0
        }, {
            'country': 'AR',
            'total_completed_routes': 50,
            'underperforming_routes_count': 10,
            'underperforming_pct': 20.0
        }])
        return MockJob(df)
        
    elif 'delivered_shipments' in query_lower and 'partner_id' in query_lower and 'having' in query_lower:
        df = pd.DataFrame([{
            'country': 'BR',
            'partner_id': 'PT-999',
            'partner_name': 'Outlier Partner',
            'total_shipments': 50,
            'delivered_shipments': 49,
            'success_rate_pct': 98.0
        }])
        return MockJob(df)
        
    elif 'delivered_shipments' in query_lower and 'partner_id' in query_lower:
        df = pd.DataFrame([{
            'country': 'CO',
            'partner_id': 'PT-040',
            'partner_name': 'Partner CO',
            'total_shipments': 200,
            'delivered_shipments': 160,
            'success_rate_pct': 80.0
        }, {
            'country': 'PE',
            'partner_id': 'PT-051',
            'partner_name': 'Partner PE',
            'total_shipments': 150,
            'delivered_shipments': 120,
            'success_rate_pct': 80.0
        }, {
            'country': 'BR',
            'partner_id': 'PT-014',
            'partner_name': 'SaoPauloShip',
            'total_shipments': 100,
            'delivered_shipments': 80,
            'success_rate_pct': 80.0
        }])
        return MockJob(df)
        
    elif 'delivered_shipments' in query_lower:
        df = pd.DataFrame([{
            'country': 'BR',
            'total_shipments': 1000,
            'delivered_shipments': 800,
            'success_rate_pct': 80.0
        }, {
            'country': 'CO',
            'total_shipments': 500,
            'delivered_shipments': 400,
            'success_rate_pct': 80.0
        }])
        return MockJob(df)
        
    elif 'oth_end_time_pct' in query_lower and 'planned_end_hour' in query_lower:
        df = pd.DataFrame([{
            'planned_end_hour': hour,
            'total_routes': 100,
            'oth_end_time_pct': 50.0,
            'oth_duration_pct': 55.0,
            'oth_metric_gap': 5.0
        } for hour in [11, 12, 15, 18, 20, 22]])
        return MockJob(df)
        
    elif 'oth_end_time_pct' in query_lower:
        df = pd.DataFrame([{
            'country': 'BR',
            'partner_id': 'PT-014',
            'partner_name': 'SaoPauloShip',
            'vehicle_type_name': 'Van (Large)',
            'total_routes': 81,
            'oth_end_time_pct': 64.20,
            'oth_duration_pct': 76.54,
            'oth_metric_gap': 12.34
        }, {
            'country': 'CL',
            'partner_id': 'PT-020',
            'partner_name': 'Chile Express',
            'vehicle_type_name': 'Van (Medium)',
            'total_routes': 54,
            'oth_end_time_pct': 33.33,
            'oth_duration_pct': 46.30,
            'oth_metric_gap': 12.97
        }, {
            'country': 'AR',
            'partner_id': 'PT-030',
            'partner_name': 'RosarioShip',
            'vehicle_type_name': 'Van (Large)',
            'total_routes': 217,
            'oth_end_time_pct': 49.31,
            'oth_duration_pct': 57.60,
            'oth_metric_gap': 8.29
        }])
        return MockJob(df)
        
    elif 'deliveries_utc_after_20' in query_lower:
        df = pd.DataFrame([{
            'country': c,
            'timezone_offset': offset,
            'total_deliveries': 1000,
            'deliveries_utc_after_20': 5,
            'pct_utc_after_20': utc_rate,
            'deliveries_local_after_20': 10,
            'pct_local_after_20': local_rate
        } for c, offset, utc_rate, local_rate in [
            ('BR', -3, 0.51, 0.73),
            ('CO', -5, 0.47, 3.12),
            ('MX', -6, 0.55, 5.64),
            ('PE', -5, 0.64, 3.94),
            ('AR', -3, 0.57, 0.73),
            ('CL', -4, 0.61, 1.13)
        ]])
        return MockJob(df)
        
    elif 'true_hour_utc' in query_lower:
        df = pd.DataFrame([{
            'true_hour_utc': hour,
            'logged_hour_utc': 0 if hour >= 20 else hour,
            'total_events': 1000,
            'corrupt_records': 1000 if hour >= 20 else 0,
            'corruption_pct': 100.0 if hour >= 20 else 0.0
        } for hour in range(18, 24)])
        return MockJob(df)
        
    elif 'total_corrupt_rows' in query_lower:
        df = pd.DataFrame([{
            'total_rows': 7300000,
            'total_corrupt_rows': 38928,
            'overall_corruption_pct': 0.53
        }])
        return MockJob(df)
        
    elif 'stale_routes_count' in query_lower:
        df = pd.DataFrame([{
            'partner_id': 'PT-014',
            'total_routes': 378,
            'stale_routes_count': 29,
            'stale_routes_pct': 7.67,
            'completed_routes_count': 349,
            'route_closure_rate': 92.33
        }])
        return MockJob(df)
        
    elif 'total_routes_assigned' in query_lower:
        df = pd.DataFrame([{
            'partner_id': 'PT-014',
            'partner_name': 'SaoPauloShip',
            'total_routes_assigned': 378,
            'stale_in_progress_count': 29,
            'stale_in_progress_pct': 7.67,
            'completed_routes_count': 349,
            'chrono_violations_count': 152,
            'chrono_violations_pct': 43.55,
            'gps_sync_failures_count': 61,
            'gps_sync_failures_pct': 17.48,
            'overlapping_routes_estimate': 38,
            'multi_hub_overlaps_count': 38,
            'impossible_vehicle_allocations_count': 15,
            'contract_end_date': pd.Timestamp('2024-10-31'),
            'routes_after_expiration_count': 378,
            'contract_expired_routes_count': 378,
            'contract_expired_routes_pct': 100.0
        }])
        return MockJob(df)

    elif 'chrono_violations_count' in query_lower and 'overlapping_routes' not in query_lower:
        df = pd.DataFrame([{
            'partner_id': 'PT-014',
            'total_routes': 378,
            'completed_routes': 349,
            'chrono_violations_count': 152,
            'chrono_violations_pct': 43.55,
            'gps_sync_failures_count': 61,
            'gps_sync_failures_pct': 17.48
        }])
        return MockJob(df)
        
    elif 'impossible_vehicle_allocations_count' in query_lower:
        df = pd.DataFrame([{
            'partner_id': 'PT-014',
            'total_overlapping_routes_estimate': 38,
            'multi_hub_overlaps_count': 38,
            'impossible_vehicle_allocations_count': 15
        }])
        return MockJob(df)
        
    elif 'contract_end_date' in query_lower and 'overlapping_routes' not in query_lower:
        df = pd.DataFrame([{
            'partner_id': 'PT-014',
            'partner_name': 'SaoPauloShip',
            'contract_end_date': pd.Timestamp('2024-10-31'),
            'routes_after_expiration_count': 378,
            'earliest_violation_date': pd.Timestamp('2025-04-01'),
            'latest_violation_date': pd.Timestamp('2025-05-31')
        }])
        return MockJob(df)
        
    else:
        return MockJob(pd.DataFrame([{'dummy': 1}]))

class TestUnifiedScripts(unittest.TestCase):

    def setUp(self):
        # Setup mocks for pydata_google_auth and google.cloud.bigquery
        self.auth_patcher = patch('pydata_google_auth.get_user_credentials')
        self.bq_patcher = patch('google.cloud.bigquery.Client')
        
        self.mock_auth = self.auth_patcher.start()
        self.mock_bq = self.bq_patcher.start()
        
        # Setup mock client behavior
        self.mock_client = MagicMock()
        self.mock_bq.return_value = self.mock_client
        self.mock_client.query.side_effect = mock_query_side_effect
        
    def tearDown(self):
        self.auth_patcher.stop()
        self.bq_patcher.stop()

    def test_data_audit_validation(self):
        """Test execution of data_audit_validation.py main entrypoint."""
        from src.data_audit_validation import run_audit
        try:
            run_audit()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_audit raised unexpected exception: {e}")

    def test_route_productivity(self):
        """Test execution of route_productivity.py main entrypoint."""
        from src.route_productivity import run_route_productivity
        try:
            run_route_productivity()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_route_productivity raised unexpected exception: {e}")

    def test_delivery_effectiveness(self):
        """Test execution of delivery_effectiveness.py main entrypoint."""
        from src.delivery_effectiveness import run_delivery_effectiveness
        try:
            run_delivery_effectiveness()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_delivery_effectiveness raised unexpected exception: {e}")

    def test_on_time_handling(self):
        """Test execution of on_time_handling.py main entrypoint."""
        from src.on_time_handling import run_on_time_handling
        try:
            run_on_time_handling()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_on_time_handling raised unexpected exception: {e}")

    def test_timezone_investigation(self):
        """Test execution of timezone_investigation.py main entrypoint."""
        from src.timezone_investigation import run_timezone_investigation
        try:
            run_timezone_investigation()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_timezone_investigation raised unexpected exception: {e}")

    def test_partner_consistency(self):
        """Test execution of partner_consistency.py main entrypoint."""
        from src.partner_consistency import run_partner_consistency
        try:
            run_partner_consistency()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_partner_consistency raised unexpected exception: {e}")

    def test_dashboard_narrative(self):
        """Test execution of dashboard_narrative.py main entrypoint."""
        from src.dashboard_narrative import run_dashboard_narrative
        try:
            run_dashboard_narrative()
        except SystemExit as e:
            self.assertEqual(e.code, 0, "Script exited with non-zero status code")
        except Exception as e:
            self.fail(f"run_dashboard_narrative raised unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()

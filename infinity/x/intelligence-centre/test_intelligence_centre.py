import unittest
import tempfile
import json
from pathlib import Path
import engine as e

class Tests(unittest.TestCase):

    def test_locks(self):
        e.locks()

    def test_services(self):
        self.assertEqual(len(e.aggregate()["services"]),5)

    def test_mode(self):
        self.assertEqual(
            e.aggregate()["mode"],
            "LOCAL_REPORT_AGGREGATION"
        )

    def test_no_live_monitoring(self):
        self.assertFalse(
            e.aggregate()["liveMonitoringEnabled"]
        )

    def test_no_child_data(self):
        self.assertFalse(e.aggregate()["childDataIncluded"])

    def test_no_revenue(self):
        self.assertEqual(e.aggregate()["actualRevenueZAR"],0)

    def test_no_expenditure(self):
        self.assertEqual(e.aggregate()["actualExpenditureZAR"],0)

    def test_no_finance(self):
        self.assertFalse(
            e.aggregate()["financialOperationsEnabled"]
        )

    def test_no_go(self):
        self.assertEqual(
            e.aggregate()["productionReadiness"],"NO_GO"
        )

    def test_missing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=e.aggregate(tmp)
            self.assertEqual(result["regressionTests"],0)
            self.assertTrue(all(
                s["checkpoint"]=="UNVERIFIED"
                for s in result["services"]
            ))

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,"pixelpunk.json").write_text("invalid")
            self.assertEqual(
                e.read_report("pixelpunk.json",tmp),{}
            )

    def test_invalid_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,"pixelpunk.json").write_text("[]")
            self.assertEqual(
                e.read_report("pixelpunk.json",tmp),{}
            )

    def test_path_traversal(self):
        with self.assertRaises(PermissionError):
            e.read_report("../../secret.json")

    def test_report_allowlist(self):
        with self.assertRaises(PermissionError):
            e.read_report("wallet.json")

    def test_stale_health_not_live(self):
        self.assertTrue(all(
            not s["currentLiveHealthVerified"]
            for s in e.aggregate()["services"]
        ))

    def test_forecast_zero(self):
        self.assertEqual(e.forecast({})["monthlyGrossCents"],0)

    def test_forecast_basic(self):
        self.assertEqual(
            e.forecast({"BUSINESS_BASIC":100})["monthlyGrossCents"],
            990000
        )

    def test_forecast_annual(self):
        self.assertEqual(
            e.forecast({"BUSINESS_BASIC":100})["annualizedGrossCents"],
            11880000
        )

    def test_forecast_combined(self):
        self.assertEqual(
            e.forecast({
                "BUSINESS_BASIC":100,
                "BUSINESS_PRO":50
            })["monthlyGrossCents"],
            2485000
        )

    def test_forecast_overhead(self):
        self.assertEqual(
            e.forecast({},3500000)["balanceBeforeOtherCostsCents"],
            -3500000
        )

    def test_negative_count(self):
        with self.assertRaises(ValueError):
            e.forecast({"BUSINESS_BASIC":-1})

    def test_boolean_count(self):
        with self.assertRaises(ValueError):
            e.forecast({"BUSINESS_BASIC":True})

    def test_unknown_product(self):
        with self.assertRaises(ValueError):
            e.forecast({"UNKNOWN":1})

    def test_non_subscription(self):
        with self.assertRaises(ValueError):
            e.forecast({"SOFTWARE_LICENSE":1})

    def test_invalid_overhead(self):
        with self.assertRaises(ValueError):
            e.forecast({},-1)

    def test_no_guarantees(self):
        self.assertFalse(e.forecast({})["guaranteedReturns"])

    def test_finance_blocked(self):
        with self.assertRaises(PermissionError):
            e.activate_finance()

    def test_child_export_blocked(self):
        with self.assertRaises(PermissionError):
            e.export_child_data()

    def test_provider_modification_blocked(self):
        with self.assertRaises(PermissionError):
            e.modify_provider()

    def test_forecast_no_actual_sales(self):
        self.assertEqual(
            e.forecast({"BUSINESS_PRO":100})["actualRevenueCents"],
            0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)

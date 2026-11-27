import unittest
import gpu

class Tests(unittest.TestCase):

    def test_locks(self):
        gpu.locks()

    def test_service_count(self):
        self.assertEqual(len(gpu.SERVICES),8)

    def test_all_services(self):
        for service in gpu.SERVICES:
            result=gpu.draft(30,service,10,10000)
            self.assertEqual(result["status"],"LOCAL_DRAFT")

    def test_child_denied(self):
        with self.assertRaises(PermissionError):
            gpu.draft(17,"GPU_RENTAL",10,10000)

    def test_adult_boundary(self):
        result=gpu.draft(18,"GPU_RENTAL",1,0)
        self.assertEqual(result["domain"],"ADULT")

    def test_invalid_age(self):
        for age in (True,"30",-1,121):
            with self.assertRaises(PermissionError):
                gpu.draft(age,"GPU_RENTAL",10,10000)

    def test_invalid_service(self):
        with self.assertRaises(ValueError):
            gpu.draft(30,"UNKNOWN",10,10000)

    def test_invalid_hours(self):
        for hours in (0,-1,8761,True,1.5):
            with self.assertRaises(ValueError):
                gpu.draft(30,"GPU_RENTAL",hours,10000)

    def test_invalid_budget(self):
        for budget in (-1,True,1.5,"100"):
            with self.assertRaises(ValueError):
                gpu.draft(30,"GPU_RENTAL",10,budget)

    def test_zero_expenditure(self):
        result=gpu.draft(30,"GPU_RENTAL",10,10000)
        self.assertEqual(result["actualExpenditureZAR"],0)

    def test_no_purchase(self):
        result=gpu.draft(30,"GPU_RENTAL",10,10000)
        self.assertFalse(result["gpuPurchased"])

    def test_no_workload(self):
        result=gpu.draft(30,"GPU_RENTAL",10,10000)
        self.assertFalse(result["workloadStarted"])

    def test_no_submission(self):
        result=gpu.draft(30,"GPU_RENTAL",10,10000)
        self.assertFalse(result["submitted"])

    def test_nonbinding(self):
        result=gpu.draft(30,"GPU_RENTAL",10,10000)
        self.assertFalse(result["bindingQuote"])

    def test_purchase_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.purchase()

    def test_launch_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.launch()

    def test_submit_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.submit()

    def test_owner_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.owner_access()

    def test_database_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.database_access()

    def test_child_data_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.child_data()

    def test_deployment_blocked(self):
        with self.assertRaises(PermissionError):
            gpu.deployment_change()

    def test_public_health_only(self):
        self.assertEqual(
            gpu.HEALTH_URL,
            gpu.BASE+"/api/health"
        )

if __name__=="__main__":
    unittest.main(verbosity=2)

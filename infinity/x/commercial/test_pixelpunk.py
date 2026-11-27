import unittest
import pixelpunk as p

class Tests(unittest.TestCase):

    def test_locks(self):
        p.locks()

    def test_services(self):
        self.assertEqual(len(p.SERVICES),8)

    def test_all_drafts(self):
        for service in p.SERVICES:
            result=p.draft(30,service,"Synthetic project")
            self.assertEqual(result["status"],"LOCAL_DRAFT")

    def test_child_denied(self):
        with self.assertRaises(PermissionError):
            p.draft(17,"SEO","Synthetic project")

    def test_adult_boundary(self):
        result=p.draft(18,"SEO","Synthetic project")
        self.assertEqual(result["domain"],"ADULT")

    def test_invalid_age(self):
        for age in (True,"30",121,-1):
            with self.assertRaises(PermissionError):
                p.draft(age,"SEO","Synthetic project")

    def test_unknown_service(self):
        with self.assertRaises(ValueError):
            p.draft(30,"UNKNOWN","Synthetic project")

    def test_short_description(self):
        with self.assertRaises(ValueError):
            p.draft(30,"SEO","x")

    def test_long_description(self):
        with self.assertRaises(ValueError):
            p.draft(30,"SEO","x"*1001)

    def test_invalid_description(self):
        with self.assertRaises(ValueError):
            p.draft(30,"SEO",None)

    def test_submission_blocked(self):
        with self.assertRaises(PermissionError):
            p.submit()

    def test_publishing_blocked(self):
        with self.assertRaises(PermissionError):
            p.publish()

    def test_purchase_blocked(self):
        with self.assertRaises(PermissionError):
            p.purchase()

    def test_child_data_blocked(self):
        with self.assertRaises(PermissionError):
            p.child_data()

    def test_zero_expenditure(self):
        result=p.draft(30,"SEO","Synthetic project")
        self.assertEqual(result["actualExpenditureZAR"],0)

    def test_not_submitted(self):
        result=p.draft(30,"SEO","Synthetic project")
        self.assertFalse(result["submitted"])

    def test_nonbinding(self):
        result=p.draft(30,"SEO","Synthetic project")
        self.assertFalse(result["bindingQuote"])

    def test_no_payment(self):
        result=p.draft(30,"SEO","Synthetic project")
        self.assertFalse(result["paymentRequired"])

if __name__=="__main__":
    unittest.main(verbosity=2)

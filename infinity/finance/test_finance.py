import unittest
import engine as f

class Tests(unittest.TestCase):

    def test_01_locks(self):
        f.locks()

    def test_02_readiness(self):
        self.assertEqual(
            f.readiness()["productionReadiness"],
            "NO_GO"
        )

    def test_03_approvals(self):
        self.assertEqual(
            len(f.readiness()["approvals"]),9
        )

    def test_04_pending_approvals(self):
        self.assertTrue(
            all(
                v=="PENDING"
                for v in f.readiness()["approvals"].values()
            )
        )

    def test_05_supply(self):
        self.assertEqual(
            f.economics()["maximumSupply"],
            1000000
        )

    def test_06_allocations(self):
        self.assertEqual(
            sum(f.economics()["allocations"].values()),
            1000000
        )

    def test_07_precision(self):
        self.assertEqual(
            f.economics()["decimals"],9
        )

    def test_08_minor(self):
        with self.assertRaises(PermissionError):
            f.presale_scenario(17,1)

    def test_09_boolean_age(self):
        with self.assertRaises(PermissionError):
            f.presale_scenario(True,1)

    def test_10_adult(self):
        f.presale_scenario(18,1)

    def test_11_presale_cap(self):
        r=f.presale_scenario(30,200000)
        self.assertEqual(
            r["hypotheticalGrossZAR"],2000000
        )

    def test_12_cap_exceeded(self):
        with self.assertRaises(ValueError):
            f.presale_scenario(30,200001)

    def test_13_negative_quantity(self):
        with self.assertRaises(ValueError):
            f.presale_scenario(30,-1)

    def test_14_float_quantity(self):
        with self.assertRaises(ValueError):
            f.presale_scenario(30,1.5)

    def test_15_no_funds(self):
        self.assertEqual(
            f.presale_scenario(30,100)["actualFundsZAR"],
            0
        )

    def test_16_no_reservations(self):
        self.assertEqual(
            f.presale_scenario(30,100)["reservedTokens"],
            0
        )

    def test_17_no_allocations(self):
        self.assertEqual(
            f.presale_scenario(30,100)["allocatedTokens"],
            0
        )

    def test_18_no_guarantees(self):
        self.assertFalse(
            f.presale_scenario(30,100)["guaranteedReturns"]
        )

    def test_19_profit(self):
        r=f.profit_scenario(100000,30000,20000,10000)
        self.assertEqual(r["netProfitCents"],40000)

    def test_20_buyback_ceiling(self):
        r=f.profit_scenario(100000,30000,20000,10000)
        self.assertEqual(
            r["hypotheticalBuybackCeilingCents"],2000
        )

    def test_21_loss(self):
        r=f.profit_scenario(10000,20000,10000,0)
        self.assertEqual(
            r["hypotheticalBuybackCeilingCents"],0
        )

    def test_22_no_actual_buybacks(self):
        r=f.profit_scenario(100000,0,0,0)
        self.assertEqual(r["actualBuybacksCents"],0)

    def test_23_negative_cost(self):
        with self.assertRaises(ValueError):
            f.profit_scenario(10000,-1,0,0)

    def test_24_liquidity_covered(self):
        self.assertTrue(
            f.liquidity_stress(10000,5000,2000)["covered"]
        )

    def test_25_liquidity_shortfall(self):
        r=f.liquidity_stress(1000,5000,2000)
        self.assertEqual(r["shortfallCents"],6000)

    def test_26_liquidity_surplus(self):
        r=f.liquidity_stress(10000,5000,2000)
        self.assertEqual(r["surplusCents"],3000)

    def test_27_exact_coverage(self):
        self.assertTrue(
            f.liquidity_stress(7000,5000,2000)["covered"]
        )

    def test_28_activation_locked(self):
        with self.assertRaises(PermissionError):
            f.activate()

    def test_29_payments_locked(self):
        with self.assertRaises(PermissionError):
            f.collect_payment()

    def test_30_transfers_locked(self):
        with self.assertRaises(PermissionError):
            f.transfer_token()

    def test_31_withdrawals_locked(self):
        with self.assertRaises(PermissionError):
            f.withdraw()

    def test_32_buybacks_locked(self):
        with self.assertRaises(PermissionError):
            f.buyback()

    def test_33_burns_locked(self):
        with self.assertRaises(PermissionError):
            f.burn()

    def test_34_no_mainnet(self):
        self.assertFalse(
            f.readiness()["mainnetEnabled"]
        )

    def test_35_no_expenditure(self):
        self.assertEqual(
            f.readiness()["actualExpenditureZAR"],0
        )

    def test_36_zero_demand(self):
        self.assertEqual(
            f.presale_scenario(30,0)["hypotheticalGrossZAR"],
            0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)

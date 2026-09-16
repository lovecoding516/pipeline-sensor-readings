from django.test import SimpleTestCase

from readings.anomaly import MIN_WINDOW, Verdict, evaluate


class EvaluateTests(SimpleTestCase):
    def test_hand_computed_sequence(self):
        """Every verdict below is checkable by hand against the formula.

        For [1, 2, 3, 4, 5] with a sample (n-1) standard deviation:
          i=0  window []        -> too short
          i=1  window [1]       -> too short
          i=2  window [1,2]     mu=1.5 sd=0.7071 -> |3-1.5|=1.5   > 1.4142 -> flag
          i=3  window [1,2,3]   mu=2.0 sd=1.0    -> |4-2.0|=2.0  == 2.0    -> no flag
          i=4  window [1,2,3,4] mu=2.5 sd=1.2910 -> |5-2.5|=2.5   < 2.5820 -> no flag
        """
        verdicts = evaluate([1.0, 2.0, 3.0, 4.0, 5.0])

        self.assertEqual(
            [v.anomaly for v in verdicts], [False, False, True, False, False]
        )
        self.assertEqual(verdicts[0], Verdict(False, None, None))
        self.assertEqual(verdicts[1], Verdict(False, None, None))
        self.assertAlmostEqual(verdicts[2].baseline_mean, 1.5)
        self.assertAlmostEqual(verdicts[2].baseline_std, 0.7071067811865476)

    def test_boundary_is_strictly_greater_than(self):
        """A deviation of exactly 2 sigma is not an anomaly."""
        # window [1,2,3] has mu=2, sd=1, so 4.0 sits exactly on the boundary.
        self.assertFalse(evaluate([1.0, 2.0, 3.0, 4.0])[3].anomaly)
        self.assertTrue(evaluate([1.0, 2.0, 3.0, 4.01])[3].anomaly)

    def test_first_readings_have_no_baseline(self):
        verdicts = evaluate([42.0] * 5)
        for verdict in verdicts[:MIN_WINDOW]:
            self.assertIsNone(verdict.baseline_mean)
            self.assertIsNone(verdict.baseline_std)
            self.assertFalse(verdict.anomaly)

    def test_constant_run_has_no_anomalies(self):
        """A perfectly flat run must not flag anything, despite sigma being 0."""
        self.assertFalse(any(v.anomaly for v in evaluate([42.0] * 50)))

    def test_zero_variance_window_flags_any_change(self):
        """With sigma=0 the rule degenerates to p != mu, and must not divide by zero."""
        verdicts = evaluate([42.0] * 20 + [42.01])
        self.assertTrue(verdicts[-1].anomaly)
        self.assertEqual(verdicts[-1].baseline_std, 0.0)

    def test_window_only_looks_backwards(self):
        """A late spike must not affect the verdict on earlier readings."""
        calm = [40.0, 40.1, 39.9, 40.05, 40.0, 39.95]
        without = [v.anomaly for v in evaluate(calm)]
        with_spike = [v.anomaly for v in evaluate(calm + [99.0])]
        self.assertEqual(without, with_spike[: len(calm)])
        self.assertTrue(with_spike[-1])

    def test_window_size_limits_how_far_back_it_looks(self):
        """Readings older than window_size drop out of the baseline."""
        pressures = [10.0] * 5 + [20.0] * 5 + [20.0]
        wide = evaluate(pressures, window_size=10)[-1]
        narrow = evaluate(pressures, window_size=3)[-1]
        self.assertAlmostEqual(wide.baseline_mean, 15.0)
        self.assertAlmostEqual(narrow.baseline_mean, 20.0)

    def test_empty_input(self):
        self.assertEqual(evaluate([]), [])

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            evaluate([1.0, 2.0], window_size=1)
        with self.assertRaises(ValueError):
            evaluate([1.0, 2.0], threshold=-1)

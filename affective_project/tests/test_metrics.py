"""Hand-computed checks for every evaluation metric.

The expected numbers were worked out by hand (or come from the published
worked examples cited in each test) so that the formulas can be defended in
the presentation. Run with:  python -m unittest tests.test_metrics
"""
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.evaluation import metrics  # noqa: E402


class SamConversionTests(unittest.TestCase):
    def test_scale_ends_and_middle(self):
        self.assertEqual(metrics.sam_to_unit(1), -1.0)
        self.assertEqual(metrics.sam_to_unit(5), 0.0)
        self.assertEqual(metrics.sam_to_unit(9), 1.0)
        self.assertEqual(metrics.unit_to_sam(0.5), 7.0)


class CorrelationTests(unittest.TestCase):
    def test_pearson_perfect_and_inverse(self):
        self.assertAlmostEqual(metrics.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertAlmostEqual(metrics.pearson([1, 2, 3], [3, 2, 1]), -1.0)

    def test_pearson_hand_example(self):
        # x = 1,3,2,5 ; y = 2,4,1,7 -> mean x 2.75, mean y 3.5
        # sxy = 12.5, sxx = 8.75, syy = 21 -> r = 12.5 / sqrt(183.75) = 0.9221
        self.assertAlmostEqual(metrics.pearson([1, 3, 2, 5], [2, 4, 1, 7]), 0.9221, places=4)

    def test_pearson_undefined_for_constant_series(self):
        self.assertIsNone(metrics.pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(metrics.pearson([1], [2]))

    def test_ranks_average_ties(self):
        self.assertEqual(metrics.ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])

    def test_spearman_with_ties(self):
        # ranks x = 1, 2.5, 2.5, 4 ; ranks y = 1, 2, 3, 4
        # Pearson of the ranks = 4.5 / sqrt(4.5 * 5) = 0.9487
        self.assertAlmostEqual(metrics.spearman([1, 2, 2, 3], [1, 2, 3, 4]), 0.9487, places=4)


class ErrorTests(unittest.TestCase):
    def test_mae_and_rmse(self):
        self.assertAlmostEqual(metrics.mae([0, 0], [1, -1]), 1.0)
        # rmse = sqrt((9 + 16) / 2) = 3.5355
        self.assertAlmostEqual(metrics.rmse([0, 0], [3, 4]), math.sqrt(12.5))

    def test_sign_accuracy_uses_dead_zone(self):
        # signs gold: +, 0, - ; predicted: +, 0 (0.05 is inside the dead zone), +
        self.assertAlmostEqual(metrics.sign_accuracy([0.5, 0.0, -0.5], [0.2, 0.05, 0.3]), 2 / 3.0)


class CategoricalTests(unittest.TestCase):
    def test_accuracy(self):
        self.assertAlmostEqual(metrics.accuracy(list("abca"), list("abcb")), 0.75)

    def test_confusion_matrix(self):
        classes, matrix = metrics.confusion_matrix(list("aabb"), list("abbb"), ["a", "b"])
        self.assertEqual(classes, ["a", "b"])
        self.assertEqual(matrix, [[1, 1], [0, 2]])

    def test_macro_f1_hand_example(self):
        # class a: P = 1/1, R = 1/2, F1 = 0.667 ; class b: P = 2/3, R = 1, F1 = 0.8
        # macro F1 = (0.667 + 0.8) / 2 = 0.7333
        self.assertAlmostEqual(metrics.macro_f1(list("aabb"), list("abbb")), 0.7333, places=4)
        report = metrics.per_class_prf(list("aabb"), list("abbb"))
        self.assertAlmostEqual(report["a"]["precision"], 1.0)
        self.assertAlmostEqual(report["a"]["recall"], 0.5)
        self.assertEqual(report["b"]["support"], 2)


class AgreementTests(unittest.TestCase):
    def test_krippendorff_alpha_interval_reference_example(self):
        # Worked example in Krippendorff (2011), "Computing Krippendorff's
        # Alpha-Reliability": 4 observers, 12 units, missing values; the
        # published interval alpha is 0.849.
        observers = [
            [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
            [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
            [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
            [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None],
        ]
        units = [[v for v in column if v is not None] for column in zip(*observers)]
        self.assertAlmostEqual(metrics.krippendorff_alpha_interval(units), 0.849, places=3)

    def test_krippendorff_perfect_agreement(self):
        self.assertAlmostEqual(metrics.krippendorff_alpha_interval([[1, 1], [5, 5], [9, 9]]), 1.0)

    def test_fleiss_kappa_reference_example(self):
        # Standard worked example (10 items, 14 raters, 5 categories),
        # published kappa = 0.210.
        table = [
            [0, 0, 0, 0, 14], [0, 2, 6, 4, 2], [0, 0, 3, 5, 6], [0, 3, 9, 2, 0], [2, 2, 8, 1, 1],
            [7, 7, 0, 0, 0], [3, 2, 6, 3, 0], [2, 5, 3, 2, 2], [6, 5, 2, 1, 0], [0, 2, 2, 3, 7],
        ]
        self.assertAlmostEqual(metrics.fleiss_kappa(table), 0.210, places=3)

    def test_fleiss_kappa_rejects_unequal_rater_counts(self):
        self.assertIsNone(metrics.fleiss_kappa([[2, 0], [1, 0]]))

    def test_mean_pairwise_pearson(self):
        series = {"R1": {"m1": 1, "m2": 5, "m3": 9}, "R2": {"m1": 2, "m2": 5, "m3": 8}, "R3": {"m1": 9, "m2": 5, "m3": 1}}
        # pairs: R1-R2 = 1, R1-R3 = -1, R2-R3 = -1 -> mean -1/3
        self.assertAlmostEqual(metrics.mean_pairwise_pearson(series), -1 / 3.0)


class UncertaintyTests(unittest.TestCase):
    def test_bootstrap_is_reproducible_and_brackets_the_estimate(self):
        gold = [0.0, 0.5, 1.0, -1.0, 0.2, 0.4]
        predicted = [0.1, 0.4, 0.7, -0.5, 0.2, 0.1]
        first = metrics.bootstrap_ci(metrics.mae, gold, predicted, samples=300, seed=7)
        second = metrics.bootstrap_ci(metrics.mae, gold, predicted, samples=300, seed=7)
        self.assertEqual(first, second)
        estimate = metrics.mae(gold, predicted)
        self.assertLessEqual(first[0], estimate)
        self.assertGreaterEqual(first[1], estimate)

    def test_calibration_bins(self):
        rows = metrics.calibration_bins([0.1, 0.2, 0.9], [0.8, 0.6, 0.1])
        self.assertEqual(rows[0]["count"], 2)
        self.assertAlmostEqual(rows[0]["mean_abs_error"], 0.7)
        self.assertEqual(rows[3]["count"], 1)
        self.assertIsNone(rows[1]["mean_abs_error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

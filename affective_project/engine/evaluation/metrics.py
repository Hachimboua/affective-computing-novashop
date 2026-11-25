"""Evaluation metrics, written in plain Python so they run without numpy.

Every function is small on purpose: each one is a formula from the course
that you should be able to explain and recompute by hand. They are tested on
hand-computed examples in ``tests/test_metrics.py``.

Conventions
-----------
* Functions that need variance (Pearson, Spearman) return ``None`` when a
  series is constant, because the correlation is undefined there.
* Gold values come from SAM ratings converted to [-1, 1] with
  :func:`sam_to_unit`.
"""
import math
import random


# --------------------------------------------------------------------------
# SAM conversion
# --------------------------------------------------------------------------
def sam_to_unit(rating):
    """Map a 9-point SAM rating (1..9) to the engine's [-1, 1] scale.

    5 is the neutral middle of the manikin scale, so it maps to 0;
    1 maps to -1 and 9 to +1.
    """
    return (float(rating) - 5.0) / 4.0


def unit_to_sam(value):
    """Inverse of :func:`sam_to_unit` (useful when reporting on the 1..9 scale)."""
    return float(value) * 4.0 + 5.0


# --------------------------------------------------------------------------
# Continuous agreement between engine and humans
# --------------------------------------------------------------------------
def _mean(values):
    return sum(values) / float(len(values))


def pearson(xs, ys):
    """Pearson correlation: covariance divided by the product of std devs.

    Measures whether engine and humans move together linearly. Returns None
    for fewer than 2 pairs or when either series is constant.
    """
    if len(xs) != len(ys):
        raise ValueError("pearson needs two series of the same length")
    if len(xs) < 2:
        return None
    mx, my = _mean(xs), _mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def ranks(values):
    """Return 1-based ranks; tied values share the average of their ranks."""
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        average_rank = (position + end) / 2.0 + 1.0
        for k in range(position, end + 1):
            result[order[k]] = average_rank
        position = end + 1
    return result


def spearman(xs, ys):
    """Spearman correlation: Pearson correlation of the ranks.

    Robust to non-linear but monotonic relations and to outliers.
    """
    if len(xs) != len(ys):
        raise ValueError("spearman needs two series of the same length")
    if len(xs) < 2:
        return None
    return pearson(ranks(xs), ranks(ys))


def mae(gold, predicted):
    """Mean absolute error: average distance on the [-1, 1] scale."""
    if not gold:
        return None
    return _mean([abs(g - p) for g, p in zip(gold, predicted)])


def rmse(gold, predicted):
    """Root mean squared error: like MAE but punishes large errors more."""
    if not gold:
        return None
    return math.sqrt(_mean([(g - p) ** 2 for g, p in zip(gold, predicted)]))


def sign_accuracy(gold, predicted, dead_zone=0.1):
    """Share of items where engine and humans agree on the sign.

    Values within +/- ``dead_zone`` count as neutral (sign 0).
    """
    if not gold:
        return None

    def sign(value):
        if value > dead_zone:
            return 1
        if value < -dead_zone:
            return -1
        return 0

    return _mean([1.0 if sign(g) == sign(p) else 0.0 for g, p in zip(gold, predicted)])


# --------------------------------------------------------------------------
# Categorical agreement (labels and actions)
# --------------------------------------------------------------------------
def accuracy(gold, predicted):
    """Share of exact matches."""
    if not gold:
        return None
    return _mean([1.0 if g == p else 0.0 for g, p in zip(gold, predicted)])


def confusion_matrix(gold, predicted, classes=None):
    """Return (classes, matrix) where matrix[i][j] counts gold i predicted j."""
    if classes is None:
        classes = sorted(set(gold) | set(predicted))
    index = {name: i for i, name in enumerate(classes)}
    matrix = [[0 for _ in classes] for _ in classes]
    for g, p in zip(gold, predicted):
        if g in index and p in index:
            matrix[index[g]][index[p]] += 1
    return list(classes), matrix


def per_class_prf(gold, predicted, classes=None):
    """Precision, recall and F1 for each class.

    precision = TP / (TP + FP): of the times we said X, how often right.
    recall    = TP / (TP + FN): of the true X, how many we found.
    F1        = harmonic mean of precision and recall.
    """
    if classes is None:
        classes = sorted(set(gold) | set(predicted))
    report = {}
    for name in classes:
        tp = sum(1 for g, p in zip(gold, predicted) if g == name and p == name)
        fp = sum(1 for g, p in zip(gold, predicted) if g != name and p == name)
        fn = sum(1 for g, p in zip(gold, predicted) if g == name and p != name)
        precision = tp / float(tp + fp) if tp + fp else 0.0
        recall = tp / float(tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        report[name] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return report


def macro_f1(gold, predicted, classes=None):
    """Unweighted mean of the per-class F1 (rare classes count as much as common ones)."""
    if not gold:
        return None
    report = per_class_prf(gold, predicted, classes)
    return _mean([item["f1"] for item in report.values()])


# --------------------------------------------------------------------------
# Inter-rater agreement (the realistic ceiling for the engine)
# --------------------------------------------------------------------------
def krippendorff_alpha_interval(units):
    """Krippendorff's alpha for interval data.

    ``units`` is a list of lists: the ratings each item received (raters who
    skipped an item are simply left out). alpha = 1 - D_o / D_e, where D_o is
    the observed disagreement inside items and D_e the disagreement expected
    by chance across all pairable values. 1 = perfect agreement, 0 = chance.
    Items with fewer than two ratings are ignored (not pairable).
    """
    pairable = [list(map(float, values)) for values in units if len(values) >= 2]
    all_values = [value for values in pairable for value in values]
    n = len(all_values)
    if n < 2:
        return None
    observed = 0.0
    for values in pairable:
        m = len(values)
        within = sum((a - b) ** 2 for i, a in enumerate(values) for j, b in enumerate(values) if i != j)
        observed += within / float(m - 1)
    observed /= float(n)
    expected = sum((a - b) ** 2 for i, a in enumerate(all_values) for j, b in enumerate(all_values) if i != j)
    expected /= float(n * (n - 1))
    if expected == 0:
        return None
    return 1.0 - observed / expected


def fleiss_kappa(count_table):
    """Fleiss' kappa for several raters assigning categories.

    ``count_table[i][j]`` is how many raters put item i in category j; every
    item must have the same number of raters. kappa = (P_bar - P_e) / (1 - P_e).
    """
    if not count_table:
        return None
    raters = sum(count_table[0])
    if raters < 2 or any(sum(row) != raters for row in count_table):
        return None
    items = len(count_table)
    categories = len(count_table[0])
    p_j = [sum(row[j] for row in count_table) / float(items * raters) for j in range(categories)]
    p_i = [
        (sum(c * c for c in row) - raters) / float(raters * (raters - 1))
        for row in count_table
    ]
    p_bar = _mean(p_i)
    p_e = sum(p * p for p in p_j)
    if p_e == 1:
        return None
    return (p_bar - p_e) / (1.0 - p_e)


def mean_pairwise_pearson(series_by_rater):
    """Average Pearson correlation over every pair of raters.

    ``series_by_rater`` maps rater id -> {item id: value}; only items rated by
    both raters of a pair are used.
    """
    raters = sorted(series_by_rater)
    values = []
    for i, first in enumerate(raters):
        for second in raters[i + 1:]:
            shared = sorted(set(series_by_rater[first]) & set(series_by_rater[second]))
            r = pearson(
                [series_by_rater[first][item] for item in shared],
                [series_by_rater[second][item] for item in shared],
            )
            if r is not None:
                values.append(r)
    return _mean(values) if values else None


# --------------------------------------------------------------------------
# Uncertainty of the estimates
# --------------------------------------------------------------------------
def bootstrap_ci(metric, gold, predicted, samples=1000, seed=13, level=0.95):
    """Percentile bootstrap confidence interval for a paired metric.

    Resamples (gold, predicted) pairs with replacement ``samples`` times and
    returns the (low, high) percentiles. With few items the interval is wide,
    which is exactly the honest message to report. The fixed seed makes the
    result reproducible.
    """
    if len(gold) < 2:
        return None
    rng = random.Random(seed)
    pairs = list(zip(gold, predicted))
    stats = []
    for _ in range(samples):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        value = metric([g for g, _ in sample], [p for _, p in sample])
        if value is not None:
            stats.append(value)
    if not stats:
        return None
    stats.sort()
    low_index = int(math.floor((1.0 - level) / 2.0 * (len(stats) - 1)))
    high_index = int(math.ceil((1.0 + level) / 2.0 * (len(stats) - 1)))
    return stats[low_index], stats[high_index]


def calibration_bins(confidences, abs_errors, edges=(0.0, 0.25, 0.5, 0.75, 1.0001)):
    """Mean absolute error per confidence bin.

    A well-behaved confidence should show smaller errors in higher bins.
    """
    rows = []
    for low, high in zip(edges[:-1], edges[1:]):
        selected = [e for c, e in zip(confidences, abs_errors) if low <= c < high]
        rows.append({
            "bin": "%.2f-%.2f" % (low, min(high, 1.0)),
            "count": len(selected),
            "mean_abs_error": _mean(selected) if selected else None,
        })
    return rows

# Topic 5 — Evaluation, data, ethics and report: likely questions

1. **How did you collect human ratings?**
   `python -m engine.evaluation.rate --rater R1`: each rater sees the conversation so far, rates valence, arousal and dominance on 9-point SAM scales, picks a label and the action they think is right; the engine's output is never shown. [[number of raters]] consenting volunteers with anonymous ids.

2. **Why dev and test splits?**
   Tuning on the same messages you evaluate on overestimates performance. We split by conversation (state depends on earlier turns); dev for tuning, test for the final numbers.

3. **How do you build the gold standard?**
   `build_gold` in `evaluate.py`: mean of the raters' SAM ratings converted with (r − 5)/4; majority vote for label and action, ties excluded and counted.

4. **Which metrics and why?**
   Pearson (linear agreement), Spearman (rank agreement, robust to outliers), MAE/RMSE (size of errors), sign accuracy, label/action accuracy and macro-F1 (rare classes count equally), confusion matrices, a cost-weighted action error. Formulas in `engine/evaluation/metrics.py`, checked against hand-computed examples.

5. **What is Krippendorff's alpha?**
   1 − observed disagreement / expected disagreement; 1 is perfect, 0 is chance; it handles missing ratings. We use the interval version for SAM scales. Our implementation reproduces Krippendorff's own example (0.849).

6. **What is Fleiss' kappa?**
   Agreement of several raters on categories, corrected for chance: (P̄ − Pₑ)/(1 − Pₑ). Used for labels and actions; reproduces the standard example (0.210).

7. **Why does rater agreement matter for the engine?**
   It is the realistic ceiling: the engine cannot agree with humans more than humans agree with each other.

8. **What are the ablations?**
   The same evaluation with one component switched off: no negation, no sarcasm detection, no state smoothing; plus the kit's starter engine as baseline. Differences show what each component contributes. [[TODO: results]]

9. **What is a bootstrap confidence interval?**
   Resample the (gold, predicted) pairs with replacement 1,000 times and take the 2.5% and 97.5% percentiles of the metric; with few messages the interval is wide, which is the honest message.

10. **How is confidence evaluated?**
    Calibration: mean error per confidence bin, and the Spearman correlation between confidence and error (negative is good). [[TODO: result]]

11. **What did the error analysis show?**
    [[TODO: categories from `test_errors.csv` (sarcasm, negation, missing word, short/ambiguous, other language, mixed emotion, state lag, rater disagreement), counts, and fixes.]]

12. **Ethics: GDPR and the AI Act?**
    See `ethics/ethics.md`: data minimisation (engine stores nothing; logs by the harness), consent and deletion for raters, AI Act definition of emotion recognition based on biometric data (text vs voice), workplace/education prohibition, high-risk listing, transparency; affect used only for support; "expressed, not felt" emotion (Barrett et al., 2019).

## Live-change drills (verified)

1. **Run the evaluation.** `python -m engine.evaluation.evaluate --split dev --bootstrap 200`; open `engine/evaluation/results/dev_summary.md`. Without ratings it stops with exit code 2 and writes nothing.
2. **Make missed escalations cost more.** In `evaluate.py` set `MISSED_ESCALATION_COST = 5.0`; rerun: the "Action cost" column increases for every variant that misses an escalation.
3. **Add an ablation.** Add `("no_contrast", "full engine without contrast weighting", Engine, {"CONTRAST_EARLIER_WEIGHT": 0.5, "CONTRAST_LATER_WEIGHT": 0.5})` to `VARIANTS` in `evaluate.py` (and add it to the expected set in `tests/test_evaluate.py`); rerun: a new row appears in the summary.

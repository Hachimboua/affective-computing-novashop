# Topic 4: Software, interface, tests, and demo

## Phase 0 baseline

The starter engine exposed a small `Engine.reset()` / `Engine.process()` API
to a shared harness. The GUI, scenario runner, contract tests, and session
logger all use that integration path; the harness and kit files remain
unchanged. A baseline example in mandatory M1 turn 3 returned a positive
estimate and `ANSWER` instead of the expected positive close, demonstrating
why valid numeric output alone is not enough.

## Phase 6: integration and observability

The GUI and scenario runner both call the shared `harness.Session`, which
calls `Engine.process()` and normalizes its result through
`harness.contract.normalize`. `Engine._process()` estimates text affect,
updates `StateTracker`, selects the first matching policy rule, creates a
reply, and returns V/A/D, confidence, the kit's labels, an action, flags, and
JSON-serializable `details`.

The engine measures four stages with `time.perf_counter()`:

- `text`: text perception and label estimation;
- `state`: state update and action recording;
- `policy_reply`: ordered action selection and reply rendering; and
- `total`: the complete engine call.

The kit logger in `harness/logger.py` stringifies `details` on one line. The
engine therefore rounds display values, keeps a compact state summary, and
limits `evidence` to the first `DETAILS_EVIDENCE_LIMIT` matches while
retaining the total `evidence_count`. Each retained item is `[term, V, A, D]`.
The full `TextEstimate` keeps its full evidence. `voice` and `face` are `null`
until those channels are implemented; this Phase 6 engine result uses text
only.

The internal-error boundary in `Engine.process()` returns a contract-valid
clarification with `internal_error` and the exception type, without exposing
the exception message. Tests set `ENGINE_STRICT=1` to re-raise errors and keep
faults visible.

The reusable clean-copy checker at
`affective_project_notes/tools/clean_copy_check.py` copies only the project
into a temporary folder, excluding `.git`, common virtual environments, and
`__pycache__`. It runs the contract test, full suite, and every scenario JSON
through `run_scenario.py` in the copy. Scenario output and logs are checked
but suppressed; the script prints only totals and failed check names.

## Worked example

The fresh English sentence “Could you tell me how to follow the parcel's
route?” is not an evaluation message. It produced V=0.000, A=-0.046,
D=0.000, confidence=0.522, label `neutral`, language `en`, action `ANSWER`,
and rule `R7_DEFAULT`. In one Python 3.12 run its stage timing was text=5.213
ms, state=0.147 ms, policy/reply=0.342 ms, and total=5.711 ms. Timing varies
with hardware and process state; these values are illustrative, not
performance guarantees.

The Phase 6 integration regression checks 15 new English/Portuguese
sentences for language identification, JSON serialization, timing fields, and
compact logger output. The tests also confirm that the sentences are absent
from `messages.csv` and earlier test files.

## How to change it

- To include more or fewer evidence terms in logs, change
  `DETAILS_EVIDENCE_LIMIT` in `engine/config.py`. Raising it adds detail and
  length; `tests/test_integration.py` enforces a 650-character log-line cap.
- To alter the detail schema or rounding, edit the `details` construction in
  `Engine._process()` in `engine/engine.py`; preserve JSON serialization and
  the log-size regression.
- To add another measured stage, instrument the matching section in
  `Engine._process()` with `time.perf_counter()` and extend the timing-field
  regression in `tests/test_integration.py`.
- To change what the clean-copy gate excludes or runs, edit
  `affective_project_notes/tools/clean_copy_check.py`; retain the contract,
  complete unit suite, and recursive scenario checks.
- To add a fresh integration case, extend `GENERALIZATION_CASES` in
  `tests/test_integration.py`; its checks reject overlap with the evaluation
  CSV and existing tests.

## Likely teacher questions

1. **Why keep `details` as a dictionary?** It is machine-readable and
   JSON-serializable, while compact values keep the harness's one-line text
   log readable.
2. **Does the evidence limit discard estimator evidence?** No. It applies
   only to public log details; the estimator retains its full evidence list,
   and `evidence_count` shows the number of matches.
3. **Why measure stages as well as total time?** Stage timings identify
   whether perception, state tracking, or policy/reply work dominates a slow
   call; the session timer also includes harness overhead.
4. **Why run the clean-copy gate?** It catches hidden imports or accidental
   dependencies on workspace files that would be missing from the delivered
   project copy.
5. **Where are model-evaluation results?** The human-rating CLI exists, but
   the Phase 9 metrics pipeline is not implemented and there are no real
   rating files; reporting metrics now would be fabricated.

## Live-change drills

1. Change `DETAILS_EVIDENCE_LIMIT` from `2` to `1`, then run
   `py -3.12 -m unittest discover tests -p test_integration.py`. The detail
   line remains compact, and the long-evidence test still passes. Restore `2`.
2. Temporarily change `MAX_CLARIFY` from `2` to `1`, then run
   `py -3.12 -m unittest discover tests -p test_policy.py`. The clarification
   loop offers a person sooner and its current regression should fail;
   restore `2`.
3. Add a temporary supported English or Portuguese sentence to
   `GENERALIZATION_CASES` and run the integration test. It should detect the
   expected language and keep details below the size cap; remove the drill
   sentence afterward.

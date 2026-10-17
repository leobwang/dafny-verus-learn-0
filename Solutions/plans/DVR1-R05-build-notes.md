# DVR1 R05 author checkpoint — 2026-10-17

Standing user request: continue until Basic is done. D45 records and skips
live Claude validation debt. No model call, reserve override or external push
is used here. R03's OD8/Unicode primitive packaging blocker remains parked;
R04 and R05 proceed independently under A1.

## Branch and scope

`authoring-r05` is based on the clean R04 candidate `bf1b73a`, itself descended
from local Basic `66987d9`. No legacy authoring ancestry is merged. Primary
main stays design-only at `6f453d0`. R04/R05 are authoring, not shipped; Basic
still contains Q01–Q18 and R01/R02. Full R04 author/study CI is running on its
separate clean candidate. Its canonical admission now passes12/12, its final
study workflow13/13, all four native reference targets pass the three seeds,
and47 pin checks pass. Do not confuse the old failed focused run or interrupted
worktree rehearsal with those current results.

## R05 content and native evidence

PLAN §6.5:402min, A1 only, four predictions, eight formal holes, two Python
holes, two-hole agent pair, fourth learner bench card. No earlier learner
proof or later A1b is imported. The given H4 branch, choice, call and measure
remain; only its annotation regions contain the reference additions.

`/tmp/dvl0-dvr1-r05/counts.log`: actual generated-unit references Dafny78tasks
(assertion isolation expands tasks), min6contracted symbols; Verus6tasks,
min6symbols. Self-contained prototypes also verify their copied given A1,
so their totals differ. Shipping states: four holes/errors0 per hand file;
two holes/errors0 per agent file; Python failed with two syntax-tree holes.
Counts are generated normally with `vcheck --ref --pin-counts R05`.

`admission-canonical.log`:10/10holes admitted. Both empty bodies and all named
regions fail under every applicable native mode/seed; H4's two annotation
regions are erased while preserving its supplied skeleton. Python TRIV fails
for both items. No automation-mode waiver or raised solver limit is used.

Four predictions are captured, not assumed. `measurement-results.json` and
`measurements-{d,v}.jsonl` retain ten sequential complete runs per language,
fixed W1 copy/seed/options. Actual resource counts repeat and wall durations
vary in each; private answers were written from the observations. Four fast/
whole-file controls distinguish the selected correct lemma from its file's
false second lemma. `reference-predictions.log`:4checks,0problems, including
both obligation specimens and their actual label sets. The official author
chapter-capture route supplies the local open-guard scope, never a changed
native gate or a public environment bypass.

The Python reference passes38frozen acceptance cases. Both declared trivial
replacements fail. Tests cover ordered preservation, all verdicts, null versus
zero, malformed/blank/missing rows, nonnumeric/bool/nonfinite/negative values,
sample standard deviation/CV, the all-zero convention, and actual composition
of `fvh.stats.bootstrap_ci` with the requested seed. No estimator is reimplemented.
The original name Run collided with a curated benchmark name; the record is
now `TimingRun`, consistently in signatures, references and tests. The tests
use `harness/tests/r/test_variance.py`, the existing adapter's normal stem-based
mapping; PLAN's older `test_r05_variance.py` spelling is not a second test route.

## Packaging and remaining bar

Chapter: about5900words, four prediction boxes, three diagrams and19native/
Python output captures. Ten non-prediction specimen sidecars use normal sealed
hashes wherever an `after:` guard applies. Paper: source-pinned card06.3,
facts-per-line proof, five-resample percentile/CV calculation; blank answers,
protected solution and gold/flawed fixtures. The flawed fixture's numerical
work remains intact while its next-duration guarantee is false. The rubric
uses proof-shape and distinguishes that conceptual error from arithmetic.

Bank:12questions, two disjoint six-question draws with one native live predict
each, plus two paired fresh parallel problems. Initial Verus PP2 was rejected
because an open spec fn lacked pub; the public statement and private reference
were corrected together. Both live probes reach verification; all four PP
references must gate/audit. No live grading or contractor transcript is claimed.

Initial static issues were corrected: reference CHECK switches were still
disabled, two card prose comments looked like commented checks, and the Run
name collided with the curated list. Current hollow/reference lint and avoid
pass. Eight protected patterns match their own reference once. Initial complete
source scan:22modules,1827public files,0leaks; repeat after final metadata.

Remaining: final chapter/sidecar/rubric freshness, all five written documents,
completed-reference study workflow, seed stability and focused CI, final leak
scan and archive. Commit only in STUDY with eight deny rules and no mode file.
This checkpoint is not a release claim. Local native success does not settle
experimental provenance, statistical assumptions or the contractor call budget.

## Private drivers

Scratch `/tmp/dvl0-dvr1-r05` holds captures, JSON results and author drivers.
Early generators are stale after lint/name corrections: do not rerun them
over current sources or regenerate chapter entries after capture. Preserve
failures alongside successful reruns. Archive final evidence under
`~/.cache/dafny-verus-learn-0/author-probes/dvr1/` before promotion.

At most three16GiB native lanes/48GiB total; GATE_WORKERS=1. Author probes use
a second Verus pool slot beside R04's capped lane; CI owns its pinned serial
discipline. Check available memory before each launch. No subagents are used.


## Final local validation — supersedes the pending checklist

Clean source candidate178657f passes focused author CI
20261017T075349Z-2561337:6passed,0failed,0skipped,0absent in696s. Static,
R Dafny, R Verus, paper, rubric and harness all pass. Actual full R04 author
CI remains separately running onbf1b73a; R05 does not claim a full global run.

Completed-reference private study clone:13/13commands, four genuine passing
first tries, strict report and freeze, both hand gates/audits, Python gate/audit
and both agent gates/audits. Original source baseline is pinned as local Basic
inside that disposable clone, never by moving the shared Basic branch.
Four native reference targets (hand/agent in both languages) each pass all
three pinned seeds. Final R05 pins:40checked,0problems. All ten canonical
admission items pass; Python38acceptance cases and both TRIV controls pass.

Both native viva probes reach verification with their expected observations;
all four parallel-problem references gate and audit clean. The Verus PP2
visibility correction is included. All five written documents compile, including
protected gold/flawed fixtures under /tmp/dvl0-dvr1-r05/paper-fixtures.
Reference lint0findings over189twins/22modules/515reference files; hollow
lint clean, avoid0hits, chapter5914words/4predicts/3diagrams/19pins.
Final source leakage scan is repeated below before archiving and committing
this evidence checkpoint. No live model or external publish is represented
by these results. R05 stays authoring pending the broader Basic release bar.

The whitespace-only source cleanup before178657f did not change proof tokens;
chapter input pins and rubric digests were recaptured afterward. The earlier
trailing-whitespace warnings and failed lint/prototype logs remain archived.

Final source scan: leak verifier: 22 module(s), 1826 public files scanned, OK. Archive: author-probes/dvr1/r05-final-20261017.

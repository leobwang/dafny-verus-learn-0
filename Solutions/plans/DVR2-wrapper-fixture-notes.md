# Wrapper fixture corrections — 2026-10-17

The untouched R04 global author CI20261017T074107Z-1906085 onbf1b73a
finishes13pass/1fail in18370seconds. Empty-body passes in12745seconds.
Only wrappers fails: synthetic ArmedUnits uses the checker suite's full
registry while copying only Q04's fixture tree, and the all-planned CI test
assumes no R given files exist. Study CI did not run because author failed.
Neither failure is a theorem counterexample or a deferred actor pass.

Fix the fixture, not the production verifier or generator: reset every
non-Q04 fixture status to planned, then arm only synthetic Q04; remove R
givens explicitly for the true empty CI test. Add a separate negative test
that an unproved given still fails even when every module is planned. This
retains the important verify-provided-files behavior and avoids weakening the
assertion to whatever happens to be present. No course contracts or pins
change. First land on canonical Basic authoring, then inherit in later work.
Targeted native results and the immutable full wrappers rerun are recorded
with their actual scope; no full-study or final Basic pass is inferred.

Targeted native regression:9tests pass in21.333s, covering the complete
ArmedUnits class, the true no-module/no-given path and rejection of the
unproved given with all modules planned. Private log:
/tmp/dvl0-dvr2-r10/wrapper-fixtures-targeted.log. Full immutable wrappers
CI is the next broader check; do not infer its outcome from this target.


Full immutable-wrapper regression: PASS1passed/0failed/0skipped/0absent in
2388s, author run20261017T125518Z-111732 on clean8cb6f87. The wrapper suite
has586tests,1intentional skip; the CI integration suite also passes. This is
the focused wrappers job, not a replacement full14job author/study result.
The targeted9fixture tests already pass. Full public CI/orchestration logs and source
provenance are archived at ~/.cache/dafny-verus-learn-0/author-probes/dvr2/
wrapper-fixture-fix-20261017. No theorem, quota or deferred live result changed.

The focused wrappers job retains no private/reference log tree after its CI
cleanup; the archive records that absence rather than inventing an artifact.

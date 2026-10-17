"""fvh — the course's evaluation core (QPLAN §11.8; design §10.3).

Frozen (guard rule 2f): learner code composes it and never edits it. The core
uses the Python standard library only, so every number it computes can be
audited by reading it.

  fvh.stats    the estimators and tests: pass_at_k, wilson_interval,
               bootstrap_ci, mcnemar, permutation_test, holm,
               mde_two_proportions (pure; seeded where they resample)
  fvh.records  RunRecord (one verifier run) and CalibRow (one first-try
               record of instructor/calib/<ID>.tsv), with their readers and
               writers
  fvh.holes    the Python hole form, its syntax-tree counter and its lint
               (`python -m fvh.holes FILE...`)
  fvh.verdicts the gate words and the cheat classes (data only; DV4 step 1a)
  fvh.corpus   a read-only view of the cheat corpus: each fixture a Delivery
               and a Label, kept apart (DV4 step 1a)
  fvh.tools    one interface for every instrument run: the runners, the
               provenance rule, replays of recorded results, and the
               author-only recorder `python -m fvh.tools.record` (DV4 step 1a)
  fvh.protocol the policy protocol: the typed actions (Read, Edit, Verify,
               Stop), State, Context, Budget, Observation, ACTION_SCHEMA
  fvh.policies the Policy protocol and the CI-safe Mock, Scripted and
               Replay policies
  fvh.backends the model transports and ModelPolicy, candidate_ask (built
               from the apparatus file only; FVH_NO_MODEL=1 refuses);
               fvh.backends.agent, the agent-mode route of fvh.batch: one
               Qwen agent session per attempt in a per-run container,
               reached only through scripts/mksandbox-run
  fvh.executor the executor: performs a policy's actions on a work copy and
               verifies it through an isolated runner
  fvh.budget   caps, the attempt plan, the hash-chained ledger and its
               anchors, the overage and window checks, resume
  fvh.runlog   RunMeta, the run directory, the outcome-to-RunRecord map
  fvh.apparatus  the apparatus pins and facts, drift, the prompt hash
  fvh.contract the CONTRACT parser, the allowlist rules, the acceptance forms
  fvh.prereg   the pre-registration gate
  fvh.report   the frozen half of `fvh report`, and `--reverify`
  fvh.judging  `fvh report --judge`: lab runs' deliveries re-judged against
               the sealed reference in the grader container (verdict words)
  fvh.batch    the live batch runner of `fvh run` and `resume`: the plan
               (policy arms, and agent arms by the construct "agent"), the
               per-run seeds, the attempts, the stops between attempts,
               interruption and resume
  fvh.statements  the statements pin and `fvh unseal`: a sealed stratum's
               tasks written once the learner's statement files are committed
  fvh.lsp      the one entry point to the Dafny language server
               (start_server, stop_server; QPLAN §30 Q56)
  python -m fvh  run, resume, ledger, report, apparatus, contract-local

The sandbox client is fvh.tools' ContainerRunner (the verification container
through scripts/mksandbox-run, DV4 step 2). Importing `fvh` itself loads
nothing: import the submodule you use (`from fvh import stats`).
"""

__all__ = ["apparatus", "backends", "batch", "budget", "contract", "corpus", "executor", "holes",
           "judging", "lsp",
           "policies", "prereg", "protocol", "records", "report", "runlog", "stats", "tools",
           "verdicts"]

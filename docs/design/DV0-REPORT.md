# DV0 report: pins, probes and spikes

*Phase DV0 (design §15.2), 2026-10-03. It merges the results of six lanes: toolchain, Dafny probes, Verus probes, infrastructure probes, and the BigNat spikes in Dafny and in Verus. Every fact here comes from a command run on this host and archived under `~/.cache/dafny-verus-learn-0/author-probes/` (author-only; the paths below are relative to it), each run with its input, `cmd.txt`, `stdout.txt`, `stderr.txt` and `exit.txt` (spec §9.3, law 1). Calibration evidence says only feasible or infeasible, with line counts and gate results; proof text, and the pairings of items with the provers or lemma groups that close them, stay in `Solutions/spikes/` (`Solutions/spikes/AUTHOR-NOTES.md`) and the archive. The archive is a read-denied asset in study mode (spec §7.1; see the `DELTAS.md` rules).*

*Companion files: `VERSIONS.md` holds the verified rows and the pinned message wordings (`W-D…`, `W-V…`); `docs/design/DELTAS.md` holds the changes these results force on the design and the spec, and is authoritative where they differ. `Δn` below refers to its entries.*

## 1. Outcome

- **Pins.** Dafny 4.11.0 and Verus `0.2026.09.27.3cf1832` (Rust 1.98.1, Z3 4.16.0) are installed by `scripts/get_toolchain.sh`, checked against tag, commit, asset sha256 and a tree digest. Both pass `--check` after every lane finished (`dv0-report/toolchain-recheck-{dafny,verus}`).
- **Probes.** 59 Dafny probe ids (380 runs), 38 Verus, 35 infrastructure, plus 27 toolchain probes and 8 script-test probes. 34 spec or design claims were overturned or refined (§4); together with the new facts they produce 66 deltas.
- **BigNat spikes.** L1–L4 are **feasible in both languages**: complete references, every hole fails its empty-body gate in the shipped configuration, and all references are stable under 3 seeds. **No fallback was triggered**; full multiplication verifies in both languages (§5, §6).
- **What did not get done in DV0:** the first MU/week figure (design §15.2) and the D6 read-only-credential refresh probe (design §3 D6) were not produced (routed to DV1a and DV4, §8 items 29 and 21); the `dvci` CI runner account needs a host change by the user (§8 item 31); several client-side IDE probes and agent-sandbox pieces stay open (§8).
- **Memory incidents:** two uncapped Verus gate sweeps (20 and 24 jobs), overlapping an uncapped first Dafny sweep (up to 24 z3), ran the host out of memory and were killed; their outputs are quarantined and are not evidence. Afterwards every multi-job gate sweep ran under a memory cap; the single-job reference and `verify.sh` runs ran uncapped (§7).
- **Blocking for DV1:** no probe outcome blocks DV1a. Three prerequisites are listed in §9.

## 2. Pins

Full rows, hashes and provenance are in `VERSIONS.md` §1.

| | Dafny | Verus |
|---|---|---|
| binary | `.toolchain/dafny-4.11.0/dafny/dafny`, `4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2` | `.toolchain/verus-0.2026.09.27.3cf1832/verus-x86-linux/verus`, commit `3cf18325f0fd0c3040fbdec8c0f2255c0504c91a` |
| release asset | sha256 `a46a9ff7…8267179`, 65,307,946 B | sha256 `43814031…6978`, 485,702,797 B |
| installed tree | 290 files, digest `e879bb85…` | 3,873 files, digest `57f0bd81…` |
| solver | bundled Z3 4.12.1 (default) and 4.14.1 | bundled Z3 4.16.0, the only solver; no cvc5, no Singular |
| dependencies | `--standard-libraries` (`DafnyStandardLibraries.doo`, Dafny 4.11.0.0) | Rust 1.98.1 (rustup, minimal profile); `vstd = "=0.0.0-2026-09-20-0158"` resolves from crates.io (not byte-compared with the bundled vstd) |
| run | `--target py`, no .NET needed | `verus --compile`; `cargo test` beside `verus!` |
| hazards found | `dafny server` writes into the install (Δ33) | the Z3 version check runs inside the SMT session (Δ21) |

Host and agent tooling: Ubuntu 24.04.3, 32 CPUs, 123 GiB RAM with no swap, one 97,887 MiB GPU; Claude Code 2.1.288, opencode 1.18.25, Ollama 0.33.2, Docker 29.1.3; three local models pinned by digest (`VERSIONS.md` §1.4).

## 3. Probe verdicts

Verdicts: **as-spec** (the spec or design predicted it), **differs** (a prediction was wrong), **new-fact** (nothing predicted it), **not-run** (with the reason).

### 3.1 Dafny (59 probe ids; 31 new-fact, 21 as-spec, 4 differs, 3 not-run)

All runs used the pinned binary with `--resource-limit 1000000` (`dafny/_harness/env.sh`; `dafny/INDEX.txt` maps directories to questions).

| id | verdict | fact | archive |
|---|---|---|---|
| pins | new-fact | every verifying run pinned `--resource-limit 1000000`; 380 runs archived | `dafny/_harness/env.sh`; `dafny/` (all `exit.txt`) |
| rl-calibration | new-fact | the limit is Z3 rlimit per batch above a ≈3k logged baseline; a trivial nonlinear lemma fails at ≤700, passes at ≥1000; exhaustion is W-D11, exit 4 | `dafny/rl-calibration/` |
| D1 | differs | a bodyless lemma warns "bodyless **method**" (W-D01); verify exit 2, `--allow-warnings` 0, `test` 3 | `dafny/D1-hole-kinds/k01,k02,k03,k05,k07` |
| D1-test-gate | new-fact | `test`/`run` without `--allow-warnings`: any warning aborts translation (W-D05), exit 3 | `dafny/D1-hole-kinds/k07/test-py` |
| D1-silent-kinds | new-fact | verify-silent: bodyless method without `ensures`, lemma with only `requires`, function without `ensures`, abstract-module and trait members, `{:axiom}`, `assume {:axiom}`, `decreases *` | `dafny/D1-hole-kinds/k04…k19` |
| D1-allow-axioms | as-spec | silences the bodyless and `assume` warnings, not `{:verify false}`, `{:only}` or `{:extern}` | `dafny/D1-hole-kinds/kNN/verify-ax` |
| D1-abstract-bodyless | as-spec | abstract-module and trait bodyless members do not warn; audit reports 0 for the module, 2 for the trait | `dafny/D1-hole-kinds/k10,k11` |
| G5-verify-only | new-fact | `{:verify false}` warns once; `{:only}`/`@VerifyOnly` warns twice per attribute and skips other members | `dafny/D1-hole-kinds/k12,k13,k20` |
| D1a-wording | new-fact | both "assertion might not hold" and "a postcondition could not be proved on this return path" exist; locations are 1-based line, 0-based column | `dafny/D4-filters-isolate/base` |
| D2-audit-kinds | new-fact | audit always exits 0, never verifies, one row per declaration (W-D14) | `dafny/D1-hole-kinds/kNN/audit` |
| D2-include | as-spec | audit skips included code and is non-transitive; the included hole still fails `verify` | `dafny/D2-audit-include-compare/a…e2` |
| G9 | as-spec | a wrong lemma in an included file: `verify` exit 0, audit 0; `--verify-included-files` → 4 | `dafny/G9-include-unverified` |
| D2-compare-report | as-spec | md report has no file/line; `--compare-report` mismatch or missing file → exit 2 | `dafny/D2-audit-include-compare/f…k` |
| D3 | as-spec | a parse or resolution error anywhere stops verification; the summary names the first input | `dafny/D3-resolution-then-verify` |
| D4 | new-fact | `--filter-position` switches to "assertions verified"; body lines match only with `--isolate-assertions`; non-matching filters exit 0 | `dafny/D4-filters-isolate` |
| G8 | as-spec | filters exit 0 having verified a subset, or nothing | `dafny/G8-filter-exit0` |
| D5 | new-fact | `test` prints `Name: PASSED/FAILED` (W-D21); fail exit 3; no tests or no match exit 0 silently | `dafny/D5-test-run-py` |
| G18 | as-spec | `{:tset}` silently never runs; `@Tset` is a resolution error | `dafny/D5-test-run-py/test-misspelled…` |
| D6 | new-fact | `--json-output` is JSON Lines (diagnostic, status, error); not available for `audit` | `dafny/D6-json-output` |
| D7 | new-fact | a refining lemma may not restate `requires`; `...` copying works; concrete refinement re-emits hole warnings | `dafny/D7-refinement` |
| D8-server | new-fact | `dafny server` never verifies a `.dfy.specimen` URI (W-D28) | `dafny/D14-D8-lsp-scoping/s4-open-specimen` |
| D8-ide | not-run | needs VS Code with the extension (GUI) | — |
| D8-workspace-symbols | new-fact | symbols come only from projects with an open file | `dafny/D14-D8-lsp-scoping/s5-workspace-symbols` |
| D9 | new-fact | with `{}`, auto-induction closes simple inductive and nonlinear lemmas; `Rev(Rev(s))` does not close | `dafny/D9-empty-body-induction/default` |
| induction | as-spec | `{:induction false}` and `--manual-lemma-induction` each stop the auto-induction | `dafny/D9-empty-body-induction/*` |
| D10 | new-fact | project `solver-path` is honoured | `dafny/D10-solver-path-project` |
| G15 | as-spec | a lying solver greens a false lemma | `dafny/G15-fake-solver` |
| D11 | differs | with `--allow-warnings`, proof holes compile and run; bodyless compiled declarations never do | `dafny/D11-compile-unit-holes` |
| TC3 (`assume {:axiom}` runs) | as-spec | compiled code with `assume {:axiom}` verifies and runs with the unproven assumption | `dafny/D11-compile-unit-holes/u_assume_axiom_compiled` |
| D12 | as-spec | one warning per `ensures` clause; one audit row per declaration | `dafny/D12-two-ensures` |
| D13 | new-fact | `includes` reaching `../../../given` work; given files re-verify in every project; a bad glob fails only as "module does not exist" | `dafny/D13-includes-given` |
| D13-options | new-fact | project `[options]` honoured; CLI wins; a sibling project is ignored without `--find-project` | `dafny/D13-project-options` |
| G21 | as-spec | project-file poisoning (`allow-warnings`, `base` chain, `solver-path`) gives silent green | `dafny/G21-project-poisoning`, `dafny/D13-project-options` |
| G10-library | differs | `library` inputs warn per file (exit 2) but stay unverified | `dafny/D13-includes-given/lib-*` |
| D14 | new-fact | the server scopes to the nearest `dfyconfig.toml`; tier subdirectories are separate projects | `dafny/D14-D8-lsp-scoping/s1…s3` |
| D14-server-writes-install | new-fact | each `dafny server` start writes a log file into the install, breaking `--check` | `dafny/D14-D8-lsp-scoping/server-side-effect-logs` |
| G22 | as-spec | without the bundled `z3/`, the CLI uses a PATH `z3` (a liar greens); with none, exit 4 | `dafny/G22-path-z3` |
| legacy-cli | as-spec | legacy CLI: a bodyless lemma exits 0; `/allowAxioms:0` still exits 0 | `dafny/legacy-cli` |
| find-dead-code | new-fact | needs a module and `{:testEntry}`; then flags every block of a contradictory method | `dafny/G12-vacuous-requires/find-dead-code*` |
| G12-analyze-proofs | new-fact | `--analyze-proofs` catches vacuous `requires` (exit 2); `--warn-contradictory-assumptions` is internal-only | `dafny/G12-vacuous-requires` |
| stdlib | new-fact | the `Std` module list at 4.11.0; imports work with the flag, without re-verification | `dafny/stdlib-modules` |
| G11 | as-spec | `expect` outside tests is assumed by the verifier and fails at runtime; audit 0 | `dafny/G11-expect-assumed` |
| G20 | as-spec | default 30 s time limit exit 4; limit 0 unbounded; resource limit exits 4 in 0.57 s | `dafny/G20-timelimit-vs-rlimit` |
| measure-complexity | new-fact | flags `--random-seed`, `--mutations`, `--worst-amount`; no `--iterations`; byte-identical reruns | `dafny/measure-complexity` |
| module-options | differs | module `{:options}` rejects the induction, trigger and nonlinear knobs | `dafny/escape-hatches/modopt-*` |
| G17-assert-only | new-fact | `assert {:only}` warns and is audited; other Boogie attributes not enumerated | `dafny/escape-hatches/assert-only*` |
| G7 | as-spec | `test --no-verify` runs tests with nothing verified, exit 0; `verify` rejects the flag | `dafny/escape-hatches/*-no-verify` |
| exit-codes | as-spec | census of 380 runs: 0/1/2/3/4 meanings refined (Δ14); the one exit 124 is the harness's `timeout 90` killing an unbounded run, not a Dafny code | `dafny/` (all `exit.txt`); `dafny/G20-timelimit-vs-rlimit/nl3-tl0-ext90` |
| determinism | new-fact | byte-identical output over runs and `--cores`; stable error order that is not source order | `dafny/determinism` |
| assume-after-failure | new-fact | a failed assert is assumed afterwards: 6 failing asserts → 2 errors | `dafny/determinism/errlimit-*` |
| static-assert-literals | as-spec | static asserts on literals are proved, fuel-dependent (`Count(15)` fails) | `dafny/misc-spec-rows/static-assert,count-depth` |
| decreases-star-lemma | as-spec | `decreases *` on lemmas and functions is a parse error | `dafny/misc-spec-rows/dec-star` |
| basename-normalization | new-fact | `--use-basename-for-filename` leaves the JSON `uri` absolute | `dafny/escape-hatches/path-basename`, `dafny/misc-spec-rows/json-basename` |
| output-streams | new-fact | everything on stdout; stderr empty in 361 of 380 runs | `dafny/` (all `stderr.txt`) |
| verified-count-unit | new-fact | "N verified" counts tasks per symbol and check kind | `dafny/D13-includes-given/v1-textlog` |
| server-time-limit-default | new-fact | `dafny server --help` default is 30 s; the claimed IDE 20 s is unverified | `dafny/help/server` |
| internal-options | new-fact | 35 verify options are internal-only, incl. `--plugin`, `--solver-option`, `--bprint` | `dafny/help/verify-internal` |
| G14 | not-run | no specific unsound `--boogie`/`--solver-option` setting identified | — |
| G16 | not-run | `--plugin` needs a .NET assembly; no `dotnet` on the host | — |

### 3.2 Verus (38 probe ids; 14 as-spec, 13 new-fact, 9 differs, 2 not-run)

All runs used the pinned binary with `--rlimit 10` and a scrubbed environment (`env -i`).

| id | verdict | fact | archive |
|---|---|---|---|
| P1 | as-spec | `vstd::pervasive::assume(false)` is green under `--no-cheating` | `verus/cheat-pervasive_assume` |
| P2 | as-spec | `axiom fn` is red under `--no-cheating` | `verus/cheat-axiom_fn` |
| P3 | differs | `external_type_specification` green; `external_trait_specification` and `external_fn_specification` red | `verus/cheat-external_*` |
| P4 | as-spec | `exec_allows_no_decreases_clause` + `loop {}` proves `1 + 1 == 3`, green under `--no-cheating` | `verus/cheat-exec_allows_no_decreases_clause` |
| P5 | new-fact | `verified` counts function bodies with obligations, loops and nonlinear asserts; `errors` counts functions | `verus/P5-verified-unit` |
| P6 | as-spec | `#[test]`s outside `verus!` run under `cargo test` and `verus --compile --test` | `verus/P6-cargo-test` |
| P6-new | new-fact | `cargo verus new` pins vstd, runs `git init`, writes no `rust-toolchain.toml`; vstd resolves and verifies | `verus/P6-cargo-test/new,cargo-verus-verify` |
| P7 | differs | `proof_note` does not attach to `admit()`; key spellings mix hyphens and underscores; order nondeterministic | `verus/P7-proof-note` |
| P7-notes-assert | new-fact | `obligation_proof_notes` / `failed_proof_notes` on asserts; compare as sets | `verus/P7-proof-note/asserts-json*` |
| P8 | new-fact | `--error-format=json` diagnostics on stderr; the "aborting" line is also a diagnostic | `verus/P8-error-format-json` |
| P9 | new-fact | `.vir` holds signatures, specs and open spec bodies, no proof or exec bodies; `--export` takes a path | `verus/P9-export-vir` |
| P10 | differs | `VERUS_EXTRA_ARGS` ignored; `VERUS_Z3_PATH` honoured; a wrong Z3 panics unless the check is disabled | `verus/P10-env-vars` |
| P11 | as-spec | 5 runs byte-identical; only JSON key order varies | `verus/P11-determinism` |
| P12 | not-run | the playground is never mentioned, which is the probe's precondition | — |
| P13 | differs | `default-members` narrows a bare `cargo verus verify`; the excluded `Solutions` crate is unreachable | `verus/P13-workspace/bare-verify…` |
| P13b | differs | a module crate on exactly one layer fails; it must also depend on the lower layers its imported specs name | `verus/P13-workspace/chain-dep-*` |
| P14 | new-fact | cargo-verus caching ignores forwarded args: a cached run with `--no-cheating` is a fake green | `verus/P13-workspace/cache-*` |
| P15 | not-run | named in design §14.5 only, never defined | — |
| WS (`--workspace`) | new-fact | every member verified, one vstd, one JSON document per crate; cargo option order matters | `verus/P13-workspace/workspace-flag-*` |
| JSON-pass | as-spec | full `verification-results` record; `--time` adds per-function rlimit (`mode:` key) | `verus/json-fields/pass*` |
| JSON-fail | as-spec | failing run record; under `--no-cheating` with a cheat, only three keys remain | `verus/json-fields/fail` |
| JSON-partial | differs | partial runs omit `success`; `--verify-module` + `--verify-function` refused (exit 255) | `verus/json-fields/partial-*`, `verify-*` |
| NC-admit-assume | as-spec | `admit()`, `assume()` red under `--no-cheating` | `verus/cheat-admit,cheat-assume` |
| NC-external_body | as-spec | `external_body` (proof and exec) red; not counted in `verified` | `verus/cheat-external_body` |
| NC-assume_specification | as-spec | `assume_specification` red | `verus/cheat-assume_specification` |
| NC-uninterp | differs | `uninterp` and bodyless spec fns red; `arbitrary()` bodies pass | `verus/cheat-uninterp_spec_fn…` |
| NC-extras | as-spec | `assume_termination` red; `#[verifier::external]` green and uncounted | `verus/cheat-assume_termination,cheat-external_attr` |
| NC-batch | as-spec | 7 cheats → exactly 7 errors in one run, next to real failures | `verus/cheat-all_in_one` |
| NC-clean | new-fact | a clean crate gives the full JSON under `--no-cheating`: one run suffices | `verus/misc/no-cheating-clean-json` |
| V18-no-verify | differs | `--no-verify` on a failing file: exit 0, JSON `success: true`, `verified: 0` | `verus/misc/no-verify-*` |
| V9 | as-spec | code outside `verus!`: `verified: 0`, empty `func-details` | `verus/V9-outside-verus` |
| expand-errors | new-fact | per-conjunct ✔/✘ blame as a separate note | `verus/expand-errors` |
| triggers | new-fact | `--triggers` notes, including vstd-internal quantifiers | `verus/triggers` |
| smt-seed | new-fact | seeds change rlimit counts, not diagnostics; an unknown SMT option panics (134) | `verus/smt-seed` |
| rlimit-hit | as-spec | an rlimit hit is an error, counted in `errors` | `verus/misc/rlimit-tiny*` |
| integer-ring | differs | `by (integer_ring)` is an unknown prover at the pin | `verus/misc/integer-ring-no-singular` |
| vstd-u64 | new-fact | `checked_*`/`wrapping_*` specs exist; no `overflowing_add`, `carrying_add`, `widening_mul` | `verus/vstd-specs` |
| verus-spec-check | new-fact | builds on the pin but its README example fails verify; it patches the `verus!` macro crate | `verus/verus-spec-check` |

### 3.3 Infrastructure and agent tooling (35 probe ids; 22 new-fact, 6 as-spec, 5 differs, 2 not-run)

| id | verdict | fact | archive |
|---|---|---|---|
| docker-version | as-spec | Docker Engine 29.1.3 client and server, containerd 2.2.1, runc 1.3.4 | `infra/docker-version` |
| docker-identity | new-fact | the DV0 probe lanes' session held a stale `docker` gid; `/etc/group` lists no members, so new logins have no Docker access (Δ60) | `infra/docker-identity` |
| docker-fresh-login-groups | differs | a fresh login is denied the Docker socket | `infra/docker-fresh-login-groups` |
| sudo-n-docker-version | new-fact | `sudo -n docker version` works | `infra/sudo-n-docker-version` |
| sudo-n-list | new-fact | `(ALL) NOPASSWD: ALL` | `infra/sudo-n-list` |
| sg-docker-version | new-fact | `sg docker` worked only in the lanes' session, which held the stale gid; from a session without it, it fails (`Password: Invalid password.`, exit 1), so it is not an access route | `infra/sg-docker-version`; `dv0-adversarial/rerun/infra_sg-docker-version` |
| docker-run-network-none | new-fact | `--network none`: only `lo`, nothing reachable, 0.21 s per run | `infra/docker-run-network-none` |
| ollama-listen | new-fact | Ollama listens on 127.0.0.1 only; unit sets context 262144 and KV q8_0 | `infra/ollama-listen` |
| docker-hostgw-ollama-bridge-v2 | differs | host-gateway from a bridge container: connection refused | `infra/docker-hostgw-ollama-bridge-v2` |
| docker-hostnet-ollama | new-fact | `--network host` reaches Ollama but gives no isolation | `infra/docker-hostnet-ollama` |
| docker-internal-net-forwarder | new-fact | internal network + gateway-bound forwarder: Ollama reachable, nothing else | `infra/docker-internal-net-forwarder` |
| rootless-tooling | new-fact | rootless extras installed; `newuidmap`/`newgidmap` missing; AppArmor restricts user namespaces | `infra/rootless-tooling` |
| rootless-setuptool-check-force | new-fact | the setup check asks for `apt-get install -y uidmap` | `infra/rootless-setuptool-check-force` |
| userns-sandbox-alternatives | as-spec | `unshare -rn` and `bwrap --unshare-net` fail inside Claude Code | `infra/userns-sandbox-alternatives` |
| ollama-version | as-spec | 0.33.2, binary sha256 pinned | `infra/ollama-version` |
| ollama-list | new-fact | three tags, two of them flash-next | `infra/ollama-list` |
| ollama-api-tags | new-fact | full digests and sizes; flash-next lists no `tools` capability | `infra/ollama-api-tags` |
| host-gpu | new-fact | 97,887 MiB GPU; qwen3.8 built-in sampling defaults | `infra/host-gpu` |
| ollama-gen-qwen3.8 | new-fact | one sample: 121.7 tok/s decode, 6.7 s cold load | `infra/ollama-gen-qwen3.8` |
| ollama-v1-messages-empty | as-spec | empty body → HTTP 400 with an Anthropic-style error and a random request id | `infra/ollama-v1-messages-empty` |
| claude-version | as-spec | 2.1.288 | `infra/claude-version` |
| claude-help | differs | every planned flag present except `--max-turns`, which is accepted anyway | `infra/claude-help` |
| claude-p-policy-json | new-fact | a tool-less `-p` call works from an empty cwd; JSON reports usage and a notional cost | `infra/claude-p-policy-json` |
| claude-p-design-argv-stream | differs | `--json-schema` adds a tool and a turn; `--system-prompt` does not hide the cwd | `infra/claude-p-design-argv-stream` |
| claude-auth-status-redacted | new-fact | subscription auth (claude.ai, max); no API-key variables | `infra/claude-auth-status-redacted` |
| opencode-version | as-spec | 1.18.25, binary sha256 pinned | `infra/opencode-version` |
| opencode-help | new-fact | help on stderr; no flag disables tools or MCP | `infra/opencode-help` |
| opencode-env-flags | new-fact | 82 `OPENCODE_*` names in the binary | `infra/opencode-env-flags` |
| opencode-iso-baseline | new-fact | the default agent has every tool and 76 `~/.claude/skills` rules from cwd ancestry | `infra/opencode-iso-baseline` |
| opencode-iso-cwd-outside-home | new-fact | a cwd outside `$HOME` removes the skill rules | `infra/opencode-iso-cwd-outside-home` |
| opencode-iso-config-B1 | differs | `tools {"*": false}` + `mcp {}` disables tools but leaves the skill rules | `infra/opencode-iso-config-B1` |
| opencode-iso-config-B2 | new-fact | the config plus `OPENCODE_DISABLE_*` gives a clean, tool-less agent | `infra/opencode-iso-config-B2` |
| opencode-iso-config-B3 | new-fact | `permission {"*": "deny"}` in place of the `tools` key (same variables, `--pure`) gives the same agent; both keys together, or any run without `--pure`, were not probed | `infra/opencode-iso-config-B3` |
| rootless-docker-host-loopback | not-run | needs the `uidmap` system package (a user decision) | — |
| qwen3.8-flash-next-load | not-run | not loaded by instruction (112 GB) | — |

### 3.4 Toolchain lane

27 probes and 8 script-test probes under `toolchain/`: GitHub API tag and digest checks, both installs, bundled solver versions and hashes, default-solver tracing, smoke runs of `dafny verify`, `dafny run --target py`, `verus`, `verus --compile` and `cargo verus toolchain list`, and refusal tests T1–T13 for `get_toolchain.sh` (all exit 1 with nothing installed). Rows: `VERSIONS.md` §1.1–§1.3.

## 4. Corrections carried forward

Claims in the spec or the design that the pins overturned or refined (spec §2.3.6, §9.3). A chapter never repeats the left column.

| # | claim (where) | what the pin does (probe) | kind | Δ |
|---|---|---|---|---|
| C1 | the lemma-hole warning reads "…bodyless lemma… enclosing lemma…" (spec §3.3) | it reads "…bodyless method… enclosing method…" (D1) | overturned | 1 |
| C2 | holes block compiling and testing the whole unit; the compiler refuses bodyless lemmas and `assume` without `{:axiom}` (spec §3.3, §11.5 item 7) | only without `--allow-warnings`; with it, proof holes compile and run; bodyless compiled declarations are always refused (D11) | overturned | 2 |
| C3 | module `{:options}` takes `--manual-triggers`, `--manual-lemma-induction`, `--disable-nonlinear-arithmetic` (spec §11.1 row 30) | each is a parse error (module-options) | overturned | 30 |
| C4 | `--library`/`.doo` inputs are silent (spec §11.4 G10) | each `.dfy` library input warns, exit 2; contents still unverified (G10-library) | overturned | 15 |
| C5 | Dafny holes are the `ensures`-bearing bodyless declarations (spec §3.3, §11.4 G2/G4) | a bodyless method without `ensures` and a lemma with only `requires` are also silent, in audit too (D1-silent-kinds) | refined | 3 |
| C6 | whole-program audit substitutes for a transitive audit (spec §11.1 row 3) | audit misses abstract-module bodyless lemmas and `expect` outside tests (D1-abstract-bodyless, G11) | refined | 4 |
| C7 | one warning per hole when the hole has one `ensures` (spec §3.3) | `@VerifyOnly`/`{:only}` print their warning twice; counters dedupe by position (G5) | refined | 5 |
| C8 | exit codes 1 CLI, 2 parse/resolution and warnings, 3 compile, 4 verification (spec §11.1 row 25) | 3 also covers runtime test failures; 2 also `--compare-report` and `find-dead-code`; `Z3 is not found` is 4; empty `includes` is 1 (exit-codes) | refined | 14 |
| C9 | `--use-basename-for-filename` strips absolute paths (spec §3.8.6) | JSON `uri` stays absolute; diagnostics need sorting (basename-normalization, determinism) | refined | 36 |
| C10 | Boogie and solver dumps via pass-through options, "[verify the exact flags]" (spec §11.1 row 33) | the dump flags are internal-only, and std-tier units cannot take `--boogie` at all (internal-options, spike) | refined | 17 |
| C11 | `--warn-contradictory-assumptions` is a G12 instrument (spec §11.4 G12) | it is internal-only; `--analyze-proofs` is the public instrument (G12-analyze-proofs) | refined | 16 |
| C12 | low fuel is an empty-body lever (design §16; spec §11.5 item 9) | on the spine, low fuel breaks the references; `{:fuel F,1,1}` is invalid (spike-dafny) | overturned | 46 |
| C13 | running the tools writes nothing into the Dafny tree (`VERSIONS.md`, toolchain lane) | `dafny server` writes a log file per start (D14-server-writes-install) | overturned | 33 |
| C14 | Dafny IDE default time limit 20 s (spec §8.7, §11.1 row 32) | the server's own default is 30 s; 20 s, if real, is an extension setting and stays unverified (server-time-limit-default) | refined | — |
| C15 | module-level verifier settings are module-scoped ("a module-scoped subset", spec §11.1 row 30) | the module attribute leaks into every later module in the same file (spike-dafny) | refined | 31 |
| C16 | `uninterp spec fn` and `arbitrary()` bodies are not flagged by `--no-cheating` (spec §3.3) | `uninterp` and bodyless spec fns are flagged; only `arbitrary()` passes (NC-uninterp) | overturned | 8 |
| C17 | V18 is caught by requiring `success: true` (spec §11.4 V18) | `--no-verify --output-json` reports `success: true`, `verified: 0` (V18-no-verify) | overturned | 11, 12 |
| C18 | the JSON gate keys are always present (spec §11.1 row 2; design §7.1) | partial runs omit `success`; a no-cheating run with a cheat omits `verified`, `errors`, `is-verifying-entire-crate` (JSON-partial, JSON-fail) | overturned | 12 |
| C19 | `external_type_specification` / `external_trait_specification` "possibly green" (spec §11.4 V6) | type spec green; trait and fn specs red (P3) | refined | 9 |
| C20 | `by (integer_ring)` works with Singular 4.3.2 (spec §11.1 rows 11–12) | rejected as an unknown prover at the pin (integer-ring) | overturned | 47 |
| C21 | `VERUS_EXTRA_ARGS` / `VERUS_Z3_PATH` may change verification (spec §11.4 V24) | `VERUS_EXTRA_ARGS` is ignored; `VERUS_Z3_PATH` is honoured with an in-session version check (P10) | refined | 21 |
| C22 | Verus hole count = number of `--no-cheating` diagnostics (spec §3.3) | minus the final "aborting due to" diagnostic (P8) | refined | 7 |
| C23 | a bare `cargo verus verify` runs every `verify = true` crate even with `default-members` (spec §10.2) | `default-members` narrows it (P13) | overturned | 23 |
| C24 | each module crate depends on exactly its tier's layer (design §10.1, §14.2 rule 1) | it must also depend on every lower layer its imported specs name (P13b) | overturned | 22 |
| C25 | `--verify-function` works within `--verify-module` (`verus --help`) | refused; use `--verify-only-module` or `--verify-root` (JSON-partial) | overturned | 41 |
| C26 | `--export CRATENAME=PATH` (`verus --help`) | the argument is a path; `--crate-name` names the crate (P9) | overturned | 25 |
| C27 | "Docker 29.1.3 works" (design §13.3) | only for sessions holding the stale group; a fresh login is denied (infra) | overturned | 60 |
| C28 | host Ollama is reachable from the sandbox through an allowlist proxy (design §13.3 item 3) | Ollama is bound to loopback; host-gateway is refused; a forwarder on the internal network's gateway works (infra) | refined | 61 |
| C29 | `--system-prompt` gives full prompt replacement, "[verify]" (design §11.1) | environment context is still injected: the model reported the exact cwd (infra) | overturned | 63 |
| C30 | policy mode with `--tools ""` has no tools (design §11.1) | `--json-schema` adds `StructuredOutput` and needs 2 turns (infra) | refined | 63 |
| C31 | opencode is isolated by an isolated HOME, `tools {"*": false}` and `mcp {}` (design §11.1) | it still picks up `~/.claude/skills` from the cwd's ancestors (infra) | overturned | 64 |
| C32 | one `qwen3.8-flash-next` model that needs CPU offload, "[verify]" (design §11.1) | two tags, neither listing `tools`; the larger cannot fit the GPU (infra) | refined | 65 |
| C33 | the planned BigNat holes fit their tier bands (design §7.4–§7.5) | Verus `add_limb` and Dafny `AddLimbCorrect` exceed the intro band; Q13 (D), Q16 H1 (D), Q16 H2 (V) fall below theirs (spikes) | overturned | 52, 53 |
| C34 | pinning resource limits, never wall-clock, bounds every run (design §11.1) | a Verus front-end hang is not bounded by `--rlimit`; a wall-clock safety kill is needed (spike-verus) | refined | 58 |

## 5. BigNat admissibility (L1–L4)

### 5.1 Method

| | Dafny | Verus |
|---|---|---|
| sources | `Solutions/spikes/dafny/QG_L{1..4}_BigNat.dfy`, `QG_BigNat_Tests.dfy` | `Solutions/spikes/verus/qg_bignat_{l1..l4,x}` (one crate per layer, each on vstd and the crate below) |
| reference check | `dafny verify --standard-libraries --resource-limit 5000000 --cores 2` on L1–L4: exit 0, `129 verified, 0 errors`; `dafny test --target py` with `QG_BigNat_Tests.dfy`: exit 0, 4 tests `PASSED` on concrete values (`spike-dafny/test-py`) | direct chain `verify.sh` at `--rlimit 2`; `cargo verus verify --workspace`: exit 0 (vstd 2059, L1 3, L2 7, L3 7, L4 17, extras 15 verified); also clean under `--no-cheating` |
| seeds | `measure-complexity --random-seed S --mutations 1`, S = 1, 2, 3 | `--smt-option smt.random_seed=S`, S = 1, 2, 3, and no seed |
| empty-body gate | "maximal automation" = baked levers stripped (auto-induction on, nonlinear arithmetic on, functions transparent, default fuel), body `{}`; then each lever alone; "as shipped" = empty body with the shipped levers. Out-of-resource results re-run at 50,000,000 | modes E0 (empty proof), E0H (E0 at `--rlimit 20`), E1/E2/EC/EM (E0 plus `broadcast use` of vstd seq groups, light arithmetic groups, the course L3 group, `group_mul_properties`), NL/BV (one whole-goal prover line), INV (invariants dropped), TRIV (trivial exec body: spec non-vacuity) |
| line count | proof lines of the reference body (for methods: annotation lines) | script heuristic: non-blank, non-comment lines of proof text, incl. invariants, `decreases`, proof blocks, ghost lets, closing braces (`spike-verus/run3/summary/lines.json`) |
| memory | every sweep under `systemd-run … -p MemoryMax=16G -p MemorySwapMax=0` (16 GiB); ≤3 jobs × `--cores 2` (`spike-dafny/INDEX.txt`); no per-job RSS was recorded; no run exited 137 or 143 | every gate sweep under `-p MemoryMax=32G -p MemorySwapMax=0` (32 GiB; `spike-verus/_tools/final_sweeps.sh`); 4 workers (light modes), 2 (EM); highest cgroup `memory.peak` 22.3 GiB (23,899,148,288 B, default-mode sweep); `oom_kill` 0 in all three sweeps (`run3/summary/gate-rl2*.json`) |
| archive | `spike-dafny/` (`summary.json`, `gate/`, `gateseeds/`, `seed-1..3/`) | `spike-verus/run3/` (`summary/table-rl2.txt`, `bands.json`, `gate/`, `ref/`) |

Line counts from the two lanes are not comparable with each other; each is compared only with its own language's band. In "seeds", 3/3 means the reference passes under all three seeds and every failing gate mode fails under all three.

### 5.2 Dafny: 39 measured items

Gate classes: **hole** (fails even at maximal automation), **hole + lever** (fails only with the lever baked in), **reveal drill** (SMT closes it; made opaque, a reveal-only answer closes it), **not a hole** (no lever makes the empty body fail while the reference passes). Planned homes are the spike lane's proposal from design §7.4–§7.5, to be confirmed by DV2–DV5.

| item | layer | kind | proof lines | empty body, max automation | lever as shipped | seeds | class | planned home |
|---|---|---|---|---|---|---|---|---|
| ToNatAppendZero (worked) | L1 | lemma | 6 | fails | — | 3/3 | hole (ships proved: W item) | Q01 W |
| ToNatSingleton | L1 | lemma | 1 | verifies | opaque `ToNat` | 3/3 | reveal drill | given helper |
| ToNatCons | L1 | lemma | 1 | verifies | opaque `ToNat` | 3/3 | reveal drill | given helper |
| ToNatHeadTail | L1 | lemma | 0 | verifies | opaque `ToNat` | 3/3 | reveal drill | given helper |
| ValidTail | L1 | lemma | 7 | verifies | opaque `Head`/`Tail` or `Valid` | 3/3 | reveal drill | given helper |
| ValidCons | L1 | lemma | 7 | verifies | opaque `Valid` | 3/3 | reveal drill | given helper |
| DropStep | L1 | lemma | 3 | verifies | opaque `Drop` | 3/3 | reveal drill | given helper |
| ToNatBound | L1 | lemma | 4 | verifies | `{:induction false}` | 3/3 | hole + lever | Q01/Q02 intro |
| NormalizeToNat | L2 | lemma | 6 | fails | — | 3/3 | hole | Q02 |
| NormalizeCanonical | L2 | lemma | 3 | verifies | `{:induction false}` | 3/3 | hole + lever | Q02/Q03 |
| NormalizeIdempotent | L2 | lemma | 3 | verifies | `{:induction false}` | 3/3 | hole + lever | Q13 (below band, Δ53) |
| FromNatCorrect | L2 | lemma | 5 | verifies | `{:induction false}` | 3/3 | hole + lever | Q03; Q10 pair |
| FromNatCanonical | L2 | lemma | 4 | verifies | `{:induction false}` | 3/3 | hole + lever | Q03 |
| AddLimbCorrect | L2 | lemma | 12 | verifies | `{:induction false}` | 3/3 | hole + lever | Q02/Q03 (above intro band, Δ52) |
| NormalizeLoop | L2 | method, loop | 4 (of 10) | fails | — | 3/3 | hole | Q02; Q10 pair |
| Cmp by method | L3 | function by method, loop | 6 | fails | — | 3/3 | hole | Q05 "D by method" |
| CmpCorrect | L3 | lemma | 7 | verifies | `{:induction false}` | 3/3 | hole + lever | Q04 |
| PowIsStdPow | L3 | lemma (std tier) | 3 | verifies | `{:induction false}` | 3/3 | hole + lever | Q04 library strand |
| PowMono | L3 | lemma (library call) | 3 | verifies | `{:induction false}` | 3/3 | hole + lever | Q04 library call |
| ToNatLowerBound | L3 | lemma | 5 | verifies | `{:induction false}` | 3/3 | hole + lever | Q04–Q06 |
| CanonicalLengthOrder | L3 | lemma | 3 | verifies | `{:induction false}` | 3/3 | hole + lever | Q04–Q06 |
| CanonicalUnique | L3 | lemma | 15 | fails | — | 3/3 | hole | Q06 or Q13 |
| MulNonneg | L4 arith | lemma (library call) | 1 | verifies | nonlinear off | 3/3 | hole + lever | Q07 arithmetic library |
| MulZero | L4 arith | lemma | 2 | verifies (also nonlinear off) | — | 3/3 | not a hole | given helper |
| MulComm | L4 arith | lemma | 1 | verifies (also nonlinear off) | — | 3/3 | not a hole | given helper |
| MulLimbDigit | L4 arith | lemma | 1 | fails (nonlinear on) | — | 3/3 | hole | Q07; Q04 carry theme |
| DistribHorner | L4 arith | lemma (library calls) | 2 | verifies | nonlinear off | 3/3 | hole + lever | Q07 arithmetic library |
| AddCCorrect | L4 | lemma | 17 | verifies | `{:induction false}` + nonlinear off + opaque `AddC` (opaque alone insufficient) | 3/3 | hole + lever | Q07–Q09; Q13; Q16 H1 |
| AddCorrect | L4 | lemma | 1 | fails | — | 3/3 | hole | Q07 or given |
| AddCDropStep | L4 | lemma | 3 | verifies | opaque `AddC` | 3/3 | reveal drill | given helper |
| AddLoop | L4 | method, loop | 9 (of 26) | fails | — | 3/3 | hole | Q07–Q09 exec add |
| MulLimbCCorrect | L4 | lemma | 15 | out of resource at 5M for seeds 1 and 3, closes under seed 2 and at 50M | `{:induction false}` + nonlinear off | 3/3 | hole + lever | Q16 H3 |
| MulLimbCorrect | L4 | lemma | 1 | out of resource at 5M; fails at 50M | — | 3/3 | hole | given or one-line |
| MulLimbLoop | L4 | method, loop | 6 | fails | — | 3/3 | hole | Q16 H3 Dafny mirror |
| MulCorrect | L4 | lemma (full multiplication) | 14 | out of resource at 5M; fails at 50M | — | 3/3 | hole | not in the design; L5–L7 candidate |
| Spec.ZeroCorrect | L4 spec | refinement lemma | 0 | verifies | — | 3/3 | not a hole | — |
| Spec.FromNatCorrect | L4 spec | refinement lemma | 1 | fails | — | 3/3 | hole | Q08; Q14 |
| Spec.AddCorrect | L4 spec | refinement lemma | 1 | fails | — | 3/3 | hole | Q08; Q14 |
| Spec.CmpCorrect | L4 spec | refinement lemma | 1 | fails | — | 3/3 | hole | Q08; Q14 |

**Totals:** 14 holes, 15 holes with a lever (13 `{:induction false}`, 2 nonlinear-off only), 7 reveal drills, 3 not holes; 24 of 39 verify with an empty body at maximal automation at the 5M spike limit (25 counting `MulLimbCCorrect`, which closes only at the 50M escalation or under seed 2). **Verdict: feasible.** Costliest reference symbol: 237,499 resource units (plain run), 374,999 under seed 1.

### 5.3 Verus: 30 measured items

Every reference passes under seeds 1–3 and without a seed at `--rlimit 2`, and under `--no-cheating`. "All modes fail" means every applicable mode of §5.1 fails 3/3 (EM ran seed 1 only, `run3/summary/gate-rl2-EM.json`); "rlimit" marks a failure by resource limit rather than an error. Memory figures are z3 maximum RSS in GiB (`maxrss_kib` in `run3/summary/gate-rl2*.json`). "Author notes" means `Solutions/spikes/AUTHOR-NOTES.md`, which is author-only and holds the item-to-prover and item-to-group pairings this report leaves out.

| item | layer | kind | proof lines | empty-body gate | seeds | planned home |
|---|---|---|---|---|---|---|
| `lemma_seq_to_nat_push_zero` (worked) | L1 | proof fn | 7 | all modes fail (EM: rlimit, 6.8 GiB z3) | 3/3 | Q01 W item |
| `lemma_seq_to_nat_drop_last_zero` | L2 | proof fn | 2 | all modes fail | 3/3 | Q02/Q10 helper of `normalize` |
| `normalize` | L2 | exec, `&mut`, loop | 6 (of 10) | all modes fail incl. INV, TRIV (EM: rlimit) | 3/3 | Q02; Q10 invariant pair |
| `from_u64` | L2 | exec | 4 | E0, E0H, E1, TRIV fail; E2 rlimit (7.5 GiB); EM rlimit (14.0 GiB) | 3/3 | Q02–Q03 |
| `lemma_add_limb_lift` | L2 | proof fn, recursive | 14 | all modes fail | 3/3 | Q02–Q03 helper |
| `add_limb` | L2 | exec, loop, ghost carry | 21 (of 41) | all modes fail incl. INV | 3/3 | Q02–Q03 (above intro band, Δ52) |
| `lemma_weight_mono` | L3 | broadcast proof fn | 4 | all modes fail incl. EC, NL | 3/3 | Q04 |
| `lemma_seq_to_nat_upper` | L3 | broadcast proof fn | 4 | all modes fail (EM: rlimit) | 3/3 | Q04 |
| `lemma_seq_to_nat_lower` | L3 | broadcast proof fn | 5 | all modes fail | 3/3 | Q04 |
| `group_bignat_bounds` (the three above) | L3 | broadcast group | 13 | as members | 3/3 | Q04 `broadcast use` target |
| `lemma_lt_at` | L3 | proof fn, recursive | 5 | all modes fail | 3/3 | Q04–Q06 helper of `cmp` |
| `cmp` | L3 | exec, loop | 16 (of 36) | all modes fail incl. INV (EM: rlimit) | 3/3 | Q04–Q06; Q16 H2 (below hard band, Δ53) |
| `lemma_add_lift` | L4 | proof fn | 18 | all fail; E1 one error and two rlimit | 3/3 | Q07–Q09 helper |
| `add` | L4 | exec, loop, `u128` carry | 24 (of 44) | all modes fail incl. INV | 3/3 | Q07–Q09 |
| `lemma_mul_limb_lift` | L4 | proof fn | 24 | all fail; E2 rlimit (1.0–1.8 GiB); EM rlimit (2.2 GiB) | 3/3 | Q07–Q09; Q16 H3 helper |
| `mul_limb` | L4 | exec, loop, `u64 × u64` via `u128` | 32 (of 53) | all modes fail incl. INV (EM: rlimit) | 3/3 | Q07–Q09; Q16 H3 |
| `shift_limb` | L4 | exec | 12 | all modes fail | 3/3 | helper of full `mul` |
| `mul` | L4 | exec, full multiplication | 25 | all modes fail (EM: rlimit) | 3/3 | beyond design L4; L5–L7 candidate |
| `NatLike` impl for `BigNat` (6 bodies) | L4 | trait impl, code only | 0 | TRIV fails 3/3 for each method (specs not vacuous) | 3/3 | Q08; Q14 |
| `double_plus_one` | L4 | generic client, code only | 0 | TRIV fails | 3/3 | Q08 client |
| `to_u64` | extras | exec, `Option<u64>` | 10 | all modes fail **after** the opaque-`weight` lever; before it, some gate modes verified the empty proof 3/3 (Δ48; details in the author notes) | 3/3 | Q10 round-trip pair |
| `round_trip` | extras | exec, code only | 0 | TRIV fails | 3/3 | Q10 pair |
| `lemma_sub_lift` | extras | proof fn | 16 | all modes fail (EM: rlimit) | 3/3 | Q13 helper |
| `sub` | extras | exec, borrow chain | 22 | all modes fail incl. INV (EM: rlimit) | 3/3 | Q13 sub with borrow |
| `lemma_limb_product_bound` | extras | proof fn | 5 | every empty-proof mode fails; closes with a single prover choice | 3/3 | predict item (Δ49; author notes) |
| `lemma_digit_split` | extras | proof fn | 2 | every empty-proof mode fails; closes with a single prover choice | 3/3 | predict item (Δ49; author notes) |
| `split_u128` | extras | exec | 3 | all modes fail | 3/3 | Q07 exec client (author notes) |
| `lemma_eq_any` | extras | proof fn | 13 | all modes fail (EM: rlimit) | 3/3 | Q16 H2 alternative |
| `lemma_lt_at_any` | extras | proof fn | 12 | all modes fail | 3/3 | Q16 H2 alternative |
| `cmp_any` | extras | exec, non-canonical inputs | 14 | all modes fail incl. INV, TRIV | 3/3 | Q16 H2 alternative |

**Lever adopted:** L3 `weight` made opaque (Δ48). L1–L4 use no `nonlinear_arith`, no `bit_vector`, no `assume`, `admit` or `external_body` (trust scan, `spike-verus/run3/final-trust-scan`); the only prover sites are in the two predict items of the extras crate. **Verdict: feasible.** Heaviest reference function: 402,506 Z3 rlimit (`lemma_sub_lift`, extras crate, unseeded run, `run3/final-verify-sh-json/outputs`); under seeds 1–3 the maximum is 369,430 (`add`, seed 3, `run3/summary/ref-rl2.json`).

### 5.4 Band check

Bands from design §7.5 (Dafny intro ≤10, intermediate 10–30, hard 30–80; Verus intro ≤15, intermediate 15–45, hard 45–120). Combined items count the helper lemmas a learner would write.

| target (planned home) | lang | lines | band | status |
|---|---|---|---|---|
| `normalize` + helper (Q02; Q10) | V | 8 | intro | in band |
| `from_u64` (Q02–Q03) | V | 4 | intro | in band |
| `add_limb`, lift lemma given / invented (Q02–Q03) | V | 21 / 35 | intro | **above**; invariant-only hole 10, in band (Δ52) |
| `AddLimbCorrect` (Q02/Q03) | D | 12 | intro | **above** by 2 (Δ52) |
| bounds group (Q04) | V | 13 | intro | in band |
| `lemma_lt_at` (Q04) | V | 5 | intro | in band |
| `to_u64` + `round_trip` (Q10) | V | 10 | intro | in band |
| other Dafny intro holes (L1–L3) | D | 1–7 | intro | in band |
| `add` + lift (Q07–Q09) | V | 42 | intermediate | in band |
| `mul` + `shift_limb` (beyond L4) | V | 37 | intermediate | in band |
| `sub` + lift (Q13) | V | 38 | intermediate | in band as shipped; an earlier version measured 47, above the band (author notes) |
| "normalize idempotent" (Q13) | D | 3 | intermediate | **below**; bundled unique-canonical-form item ≈27, in band (Δ53) |
| abstract-BigNat refinement (Q14) | D | ≈10 | intermediate | at the bottom edge |
| `CanonicalUnique` (Q06 or Q13) | D | 15 | intermediate | in band |
| H1 generalize before induction via the add carry (Q16) | D | ≈23 | hard | **below** (Δ53) |
| H2 `cmp` with invented invariant (Q16), lt_at given / bounds invented / `cmp_any` | V | 21 / 34 / 39 | hard | **below** (Δ53) |
| H3 `mul_limb` + lift (Q16) | V | 56 | hard | in band |
| H3 Dafny mirror (Q16) | D | 26 proof (≈43 with code) | hard | in band only if code counts or full multiplication (+14) is added (Δ53) |

## 6. Fallbacks

| fallback (design) | status | evidence |
|---|---|---|
| L4 multiplies by one limb (§4, §10.1) | **not triggered**: full multiplication verifies in both languages | `spike-dafny/summary.json` (MulCorrect); `spike-verus/run3/summary/table-rl2.txt` (`mul`) |
| Verus-only `mul_limb` for Q16 H3 (§7.5) | **not triggered**: the Dafny mirror passes the gate and 3 seeds | `spike-dafny/summary.json` (MulLimbCCorrect, MulLimbLoop) |
| single-file Verus spine | **not needed**: one crate per layer verifies directly and via `cargo verus verify --workspace` | `spike-verus/run3/cargo-verus-workspace-3`, `final-verify-sh-*` |
| one Dafny project per (track, tier) (§14.2) | **not needed**: D13 and D14 pass | `dafny/D13-includes-given`, `dafny/D14-D8-lsp-scoping` |
| `nonlinear_arith`/`bit_vector` in the spine | **avoided**: L1–L4 use vstd arithmetic lemmas instead | `spike-verus/run3/final-trust-scan` |
| policy mode only, if the sandbox is infeasible (§16) | **undecided**: the network pattern works (Δ61), the Docker access route is a user decision (Δ60) | `infra/docker-*` |
| harness-executed Claude runs, if read-only credentials cannot refresh (§3 D6) | **undecided**: the probe was not run; this fallback stays the default until it is | — |
| R-track fallbacks (star-free regexes, forward jumps) | out of DV0 scope (DVR0) | — |

## 7. Resource limits and memory

| | Dafny | Verus |
|---|---|---|
| unit | `--resource-limit N`: Z3 rlimit per batch; the CSV `ResourceCount` is in the same units with a ≈3k per-batch baseline | `--rlimit N` = Z3 rlimit 3,000,000 × N per query (measured at N = 1, 2, 10, 30) |
| verdict when hit | W-D11 `Verification out of resource (<name>)`, summary `…, 1 out of resource`, exit 4 | W-V05 `function body check: Resource limit (rlimit) exceeded; …`, counted in `errors`, exit 1 |
| DV0 probes | 1,000,000 | `--rlimit 10` (30,000,000) |
| BigNat spikes | 5,000,000 (`--cores 2`); escalation 50,000,000 | `--rlimit 2` (6,000,000), `--num-threads 1`; E0H at `--rlimit 20` |
| costliest reference | 237,499 plain; 374,999 / 260,661 / 315,365 under seeds 1/2/3 | unseeded: 402,506 (`lemma_sub_lift`, extras crate), 365,624 in L1–L4 (`add`); seeds 1–3: 369,430 (`add`, seed 3) |
| headroom at the spike limit | 13.3× | ≈14.9× (over 402,506) |
| **course pin (Δ56, adopted by the orchestrator 2026-10-03)** | **5,000,000** | **`--rlimit 2`** |
| memory | no RSS figure recorded for the Dafny spike (no memory kills); `--cores` defaults to 16 on this host, so it is always passed | `broadcast use` of `group_mul_properties`: 6.7–14.0 GiB z3 maximum RSS on the 17 EM jobs that reached the rlimit after 43.3–105.5 s; 6.8 GiB on a 2-line lemma with only that group (Δ57) |
| wall clock | `--verification-time-limit 0` runs unbounded; refused (Δ10) | a `bit_vector` assert on a `Seq` goal hangs the front end > 600 s; harness kill, counted as failure (Δ58) |

Goldens captured at the probe limits that involve a resource outcome are re-captured at the course pin before any chapter quotes them.

**Memory incidents.** Two earlier Verus gate sweeps ran without a memory cap, with 20 and 24 concurrent `verus` jobs, overlapping the first, also uncapped Dafny sweep (up to 24 concurrent z3; `spike-dafny/_superseded-run1-2026-10-03/README`). Together they ran the host out of memory at 11:05 and 12:36 on 2026-10-03 and were killed. Their outputs are quarantined in `spike-verus/_invalid-oom-2026-10-03/` (see its `README.txt`) and are not evidence. Afterwards every multi-job gate sweep ran under `systemd-run --user --scope` memory caps, with no memory kills; the single-job runs noted below did not:
- **Verus gate sweeps:** `-p MemoryMax=32G -p MemorySwapMax=0`, 4 workers (2 for EM), one z3 each (`spike-verus/_tools/final_sweeps.sh`). Each of the three sweep summaries records cgroup `memory.max` 34,359,738,368 B and `oom_kill` 0 (`run3/summary/gate-rl2.json`, `gate-rl2-EC-BV.json`, `gate-rl2-EM.json`). The reference-chain runs went one job at a time and **uncapped** (`ref-rl2.json`: 1 worker, the session's tmux scope with `memory.max` 120,259,084,288 B, cgroup peak 1,097,474,048 B), as did the unseeded `verify.sh` runs behind the headline 402,506 (`run3/final-verify-sh-*`, no `systemd-run`; `final-verify-sh-json` maxrss 314,616 KiB).
- **Dafny sweeps:** `-p MemoryMax=16G -p MemorySwapMax=0`, at most 3 jobs × `--cores 2` (`spike-dafny/INDEX.txt`). No spike-dafny run exited 137 or 143.
- The only exit 137 left in `spike-verus/run3/` is `bv-seq-goal-hang`, a deliberate 120 s `timeout -s KILL` (Δ58), not a memory kill.

The binding rules came out of these incidents: `CLAUDE.md` §Resources.

## 8. Open issues, routed

| # | issue | owner |
|---|---|---|
| 1 | Claude Code permission-rule syntax, hooks schema and skill frontmatter keys are unverified (`VERSIONS.md` §2.3). **Answered in DV1a (2026-10-03):** `VERSIONS.md` §2.3 now records the hook input and environment, the deny-rule forms and messages, the order of hooks and deny rules, and the block-message shape (probes `dv1a/hook-input-probe`, `dv1a/e2e-guard-wiring`). Skill frontmatter beyond `name` and `description` is string evidence only (`dv1a/skill-frontmatter-strings`): a behavioural probe of `disable-model-invocation` is still open. **Routed 2026-10-04:** that probe must show the model refused the skill and the slash command still running. DV2 runs it in its study-clone simulation (spec §9.5 step 8; DELTAS Δ89) **Half answered in DV2b-2 (2026-10-05; DELTAS Δ127):** in the study-clone simulations on Claude Code 2.1.289, each headless session's init listed the six flagged skills as slash commands, and each ran when invoked as a slash command. No session made a `Skill` tool call, so the model-side refusal is still unobserved. The calibration harness records `Skill` calls when it runs (Δ128) | DV1a (answered); DV2 (the frontmatter probe: the slash-command half observed in DV2b-2, the model-side refusal open) |
| 2 | rule 1e: does the hook input carry the session id? `Skill(local-assistant)` deny supported? (design §13.2 "[verify]"). **Answered in DV1a (2026-10-03):** yes to both. The hook input carries `session_id` and `transcript_path` (a `-p` run has no `scratchpad_dir`), and both `Skill(skill:<name>)` and `Skill(<name>)` deny rules refuse the skill (`VERSIONS.md` §2.3; DELTAS Δ80, Δ82) | DV1a (answered) |
| 3 | P14's scope was set de facto by the Verus lane (caching, forwarding, focus); P15 is undefined: confirm or drop both **Closed in DV1b (2026-10-04):** P14 stays as scoped, since no course tool calls cargo-verus and V25 therefore cannot answer a gate; P15, never defined, is dropped (DELTAS Δ99) | DV1b (closed) |
| 4 | course resource-limit pins (Δ56): adopted by the orchestrator on 2026-10-03; wire them into the tools and record them in `VERSIONS.md` §2.5 **Done in DV1b (2026-10-04):** `scripts/dvl/pins.toml` holds the pins and every tool reads them; `VERSIONS.md` §2.5 records them ("the pins as wired"; DELTAS Δ98–Δ100) | DV1b (done) |
| 5 | vstd from crates.io vs the release's bundled `vstd.vir`: not byte-compared; `cargo verus verify --check-toolchain` with a mismatched pin not probed **Not done in DV1b or DV1c.** No gate depends on it: `dvl.verus` verifies with the release's bundled vstd only and never calls cargo-verus (DELTAS Δ99). Still open | open (was DV1b); the orchestrator re-routes it |
| 6 | `.doo` route for given layers (to stop re-verifying them in every unit); the exact build command at 4.11.0 is unknown **Not probed in DV1b.** Given layers still re-verify in every unit (Δ27); the question returns with the first given layers, which DV2 writes (DELTAS Δ94) | DV2 (proposed, with the given layers, Δ94) |
| 7 | an exec-body hole form that compiles under `test`/`run`, for units that must run tests next to exec holes (Δ2) **Answered in DV1b (2026-10-04):** a method or function whose whole body is `{ assume false; }` is one W-D03 hole and compiles under `--allow-warnings`; unrelated tests pass, and a test that relies on its result fails at run time (`VERSIONS.md` §2.1, row D11; `dv1b/dafny/exec-hole-assume-false-compiles`) | DV1b (answered) |
| 8 | Verus import tiers (`prelude → seq_lib → arithmetic → all`) and their lint; the spec-freeze parser (tree-sitter-verus); `--log call-graph` usefulness **Partly answered in DV1b:** every module name in the checker's Verus tier allowlists exists in the pinned vstd, and `multiset_lib` sits outside the `seq_lib` tier while `set_lib` and `map_lib` sit inside (the checker's owners decide; Δ77). The spec-freeze parser is a tokenizer-based one, `scripts/dvl/verus_spec.py`, not tree-sitter-verus (DELTAS Δ99). The usefulness of `--log call-graph` was not evaluated | DV1b (partly answered); `--log call-graph` open |
| 9 | the CI empty-body gate re-implements the spikes' tooling: strip `// @hole-begin/@hole-end` markers and baked levers, then try item levers **Done in DV1b:** `dvl.dafny.empty_body`, `dvl.verus.empty_body` and the author-only `firsttry --empty-body` strip the baked levers and try the item levers (DELTAS Δ98, Δ99). The gate replaces a hole's whole body; hollowing regions marked inside a body is a format DV2 and DV3a decide | DV1b (done); DV2, DV3a (region markers) |
| 10 | real learner hole crates (one module crate per tier, Δ22) were not built by the spike **Moved to DV2 (DELTAS Δ94):** DV1b and DV1c ship no layer crate, given Dafny layer or check unit | DV2 (Δ94) |
| 11 | G14 (unsound `--boogie`/`--solver-option`), G16 (`--plugin`), other Boogie pass-through attributes (G17) **Not done in DV1c:** the cheat corpus was not built (DELTAS Δ106). G14 and G16 stay unrun; the wrapper refuses both routes (Δ10), so they are refusal-only rows **Done in DV1c, reopened (2026-10-04; DELTAS Δ108, Δ109):** the corpus is built. G14 and G16 are `covered-elsewhere` manifests: they name the wrapper tests and guard fixtures that show each route refused, the runner checks that those tests exist, and nothing runs them. G17 is a live fixture, `tests/corpus/dafny/G17`: the `{:selective_checking}`/`{:start_checking_here}` pair verifies under the plain run and the gate, and the lint (through `vaudit`) flags both attributes (`VERSIONS.md` §2.1). Other pass-through attributes were not probed | DV1c (done, Δ108) |
| 12 | V11 `cfg(verus_only)`, V16 `--no-lifetime`/`--no-erasure-check`, V17 `-V allow-inline-air`, V21 `global layout`, a local `external_body` struct **Partly answered in DV1b:** a local `external_body` struct gets no `--no-cheating` diagnostic, and the lint catches it (`VERSIONS.md` §2.2, partial evidence). V11, V16, V17 and V21 were not probed as tool behaviour; the wrapper refuses the V16 and V17 flags and the lint flags `cfg(verus_only)` | DV1c (reopened, Δ106) |
| 13 | cheat corpus: ≈25 Dafny vectors captured live (G1–G13, G15, G18–G22 and six attribute or statement forms) and the Verus `--no-cheating` set; ≥46 needed **Not built in DV1c** (DELTAS Δ106): `scripts/ci.sh` reports the corpus job ABSENT **Built in DV1c, reopened (2026-10-04; DELTAS Δ108):** 105 manifests under `tests/corpus/<lang>/<ID>/`, the canonical layout (Δ109). Every one of the 47 catalog rows has a manifest. 28 rows have live fixtures, and 19 are `covered-elsewhere`. There are also 36 DELTAS additions and 17 controls, and each language's Q and R halves cover all of its X families. `scripts/test_corpus.py --ci` re-checks the recorded outcomes and hashes, and `scripts/ci.sh`'s `corpus` job runs it and fails on an absent corpus (Δ109). X09, X14 and X18 have no fixture in either language. Gate v2's UNKNOWN (DV4) and the Q09/R13 halves (DV3b, DVR3) remain | DV1c (done, Δ108, Δ109); DV3b, DVR3, DV4 |
| 14 | VS Code client: `.dfy.specimen` association (D8), which project the extension sends and multi-root handling (D14), the claimed 20 s time limit; verus-analyzer `verusBinary` pin and verusfmt | DV2 (before Release A; GUI, by the user) |
| 15 | the empty-body gate re-runs on every real hole as modules are written (D9 covered the mechanism and the spike items only) **Done for Q01–Q03 (DV2a–DV2b-2; DELTAS Δ113, Δ120, Δ124, Δ129):** `scripts/ci.sh --author`'s `empty-body` job runs `firsttry.sh <ID> --empty-body` on every armed module. DV2b-2's author run (2026-10-05) passed it in 3014 s, every hole passing: Q01 8/8 (1200 s), Q02 16/16 (1356 s), Q03 15/15 (458 s). Later modules re-run it as they arm | DV2 (done for Q01–Q03); DV3a, DV3b |
| 16 | confirm the planned homes in §5 (especially Q01's holes, Δ51) and the band redesigns (Δ52, Δ53) | DV2, DV5 |
| 17 | latexmk version, `uv` version and `uv.lock`. **Recorded 2026-10-04:** `uv 0.12.4`, latexmk 4.83 on pdfTeX from TeX Live 2023 (`VERSIONS.md` §1.4; `dv1a/uv-version`, `dv1a/latexmk-version`). No `uv.lock` or `pyproject.toml` exists yet. **Re-routed 2026-10-04:** DV1b pins the lock with the first one and re-runs both version probes then **Still none at DV1c's close (2026-10-04):** no `uv.lock` or `pyproject.toml` exists; the first comes with the harness, and the phase that writes it pins it and re-runs both version probes | DV4 (with the first lock; re-routed from DV1b) |
| 18 | Dafny solver swap to the bundled z3 4.14.1 (Q09 theme); `measure-complexity --mutations > 1`; brittleness CV thresholds | DV3b |
| 19 | Docker access route (Δ60): `sudo -n docker`, re-add the group, or rootless (needs `uidmap`, then the AppArmor and host-loopback tests) | user, before DV4 |
| 20 | HTTPS CONNECT allowlist proxy and the exact Anthropic hostnames the CLI contacts | DV4 |
| 21 | D6 credential-refresh probe: credentials-only `CLAUDE_CONFIG_DIR`, read-only mount and token refresh, rotation (`claude setup-token` is a candidate). Design §3 D6 calls this a DV0 probe; DV0 did not produce it | DV4 |
| 22 | `--no-session-persistence` leaves no transcript: not checked, because lanes may not read `~/.claude/projects`; the user should confirm **Answered by observation in DV1c (2026-10-04):** over the 10 headless sessions of the DV1c acceptance test on 2.1.289, `--no-session-persistence` wrote no `*.jsonl` transcript; only empty directories remained (`VERSIONS.md` §2.3; `dv1c/acceptance/env.json`) | DV1c (answered) |
| 23 | `--max-turns` enforcement; how much environment context (beyond the cwd) `--system-prompt` keeps; whether `--safe-mode`'s listed plugins start LSP servers or hooks | DV4 |
| 24 | Ollama `/v1/messages` with real Anthropic-format requests (tools, streaming, thinking); flash-next tool calls and offload throughput; a proper Qwen throughput probe (longer outputs, repeats, concurrency, GPU sharing with Lean par runs) | DV4 |
| 25 | auto-update off for `claude` and opencode, tested by behaviour. **Observed in DV1a (2026-10-03):** the CLI auto-updated from the pinned 2.1.288 to 2.1.289 (`VERSIONS.md` §1.4; `dv1a/claude-version-drift`) | DV4 |
| 26 | no course sandbox image exists yet (digest row blank) | DV4 |
| 27 | benchmark pool validity on the pins (LemmaScript, MINIF2F-DAFNY, HumanEval-Verus, DafnyBench and vericoding subsets); RL weights | DV5 |
| 28 | R-track claims marked [verify] in design §8.2 and §10.2 (R01 `midpoint`, R09 char encoding, R10 `type_invariant`, R13 `--log`, R14 `trigscan`, the Rust `regex` crate as dev-dependency and differential oracle) | DVR0–DVR3 |
| 29 | the first MU/week quota figure (design §15.2 DV0 content): DV0 did not produce it; until it is measured, §15's dates stay as stated. **Re-routed 2026-10-03 (DELTAS Δ70):** measured over Release A authoring (DV2), since no DV1a lane owned it | DV2 (re-routed from DV1a, Δ70) |
| 30 | the local-assistant skill targets `qwen3.8-flash-next:UD-Q4_K_XL`, which lists no `tools` capability (Δ65); outside this repo | user |
| 31 | the self-hosted CI runner account `dvci` (design §14.4) was neither set up nor probed in DV0. Creating it is a host change for the user, needed before DV1c's CI goes live. **Dropped (DELTAS Δ67, user decision 2026-10-03):** CI is a local script, `scripts/ci.sh`, with no GitHub Actions and no runner account | none (dropped by Δ67) |
| 32 | **From DV1a.** The reference side of the reserved names: the checker never reads a reference tree, so a reference-only crate, package or module under `Solutions/**` named `solutions_policy` or `solutions-first` goes unchecked. The author-only reference lint adds the check (DELTAS Δ86, Δ79) **Done in DV1b:** `scripts/reference_lint.py` (author-only) checks the reserved names across the reference tree: 23 reference files clean, and planted names found in directory, Cargo, Rust and Dafny names (DELTAS Δ101, Δ103) | DV1b (done) |
| 33 | **From DV1a.** The registry lane's `dafny resolve` runs (no solver): per-layer prefix globs resolve in `includes`, a std unit with `standard-libraries = true` resolves, and a core unit cannot reach L3. These are lane-report evidence only and were never archived. Re-run them on real units, archive the runs under `dv1b/` and add a `VERSIONS.md` row (DELTAS Δ78) **Done in DV1b (2026-10-04):** re-run on generated units of the checker's armed Q04 and archived under `dv1b/dafny/armed-*`; `VERSIONS.md` §2.1, row "generated units" | DV1b (done) |
| 34 | **From DV1a.** Whether a workflow subagent's hook input carries its parent's `session_id`, which decides whether rule 1e treats the subagent's transcript and scratch as its own (DELTAS Δ82; `VERSIONS.md` §2.3) **Not run in DV1b or DV1c** (DELTAS Δ82 Status). Still open. **Not answered by DV2b-2's simulations either** (DELTAS Δ127): course skills start no subagents (`CLAUDE.md` §Session hygiene), so a skill simulation cannot observe one; it needs a probe of its own | open (was DV1b); a dedicated probe (DV2's simulations could not answer it) |
| 35 | **From DV1a.** A challenge module that ships a written item (a blueprint or sketch graded by `/grade-paper`) sets `paper = true` and names a rubric. Today all of Q19–Q33 have `paper = false` and an empty `rubric`, `/grade-paper` refuses `paper = false`, and the checker does not enforce "written item ⇒ `paper = true`" (DELTAS Δ74) | DV7 |
| 36 | **From DV1b and DV1c.** Design §14.4's "hole counts by tool = chapter = CI pin" is enforced only as "tool count = shipped hole forms per item" (`scripts/ci.sh`): a second hole added inside an existing item's block raises both counts and passes. Pin the stated count, as a chapter fence or a registry field, and have `ci.sh` compare with it (DELTAS Δ104) **Done in DV2a's fix round and DV2b (DELTAS Δ115, Δ120, Δ121; closed at DV2b-2's close):** `expected/<ID>.counts` pins each exercise, check, exit and agent file's shipped hole count; `ci.sh`'s verify jobs compare every file with its pin (`vcheck --shipped`), so a second hole inside an item's block now fails; and `chapter_lint.py` checks that each chapter's files table states the pinned counts | DV2 (done) |
| 37 | **From DV1c.** `vcheck` has no `--ref --brittleness`, so `ci.sh`'s brittleness job re-verifies given layers and learner units under the seeds but not the reference twins that spec §8.5 names (DELTAS Δ104) | DV3b (with item 18) |
| 38 | **From DV1b.** Exit thresholds for the practice tiers and for R06 and R11 are pinned nowhere; `firsttry --exit` prints the score and exits 0 there (DELTAS Δ102). Where Verus value slots live (specimens or a given-only check crate) and whether `dafny/checks/` units are generated or standalone are open too (Δ94, Δ102) | DV2 (Q tiers, slots, check units); DVR1, DVR2 (R06, R11) |
| 39 | **From DV1b and DV1c.** The dvl scratch default `/tmp/dvl-<uid>` is shared by author and study sessions. The libraries now delete source copies and Verus `deps/` after each run, but the kept cmd, stdout and stderr of an author-only run (`--ref`, `--empty-body`, `pins.py --ref`, `reference_lint.py`) can name reference locations and messages there. `scripts/ci.sh` already sends its author-only steps' scratch to `~/.cache/dafny-verus-learn-0/ci/` (rule 1); the tools could do the same for every author-only run | orchestrator (tools) |
| 40 | **From DV1c (guard and tools, optional).** Add `ci.sh … --author` to the hook's `RX_AUTHOR` (a study session in the authoring worktree can run it today; its reference output stays in the cache); set `allow_abbrev=False` in every course tool's parser so each author option has one spelling; author-gate `vaudit --trust FILE` or restrict it to `expected/`; self-gate `vaudit --write` (DELTAS Δ105) | the guard's and the tools' owners |
| 41 | **From DV1c.** Decide whether `ci.sh`'s ABSENT status (today only the corpus job) fails the pre-merge gate once the corpus lands, and how the corpus is built (DELTAS Δ106) **Decided and built (2026-10-04):** the corpus was built under a narrower brief, as source-level fixtures only, by four lanes running one solver job at a time (Δ108). The orchestrator decided that an absent corpus fails (Δ108), and `ci.sh` now does so (Δ109). The `corpus` job fails, before any solver step, on a missing `scripts/test_corpus.py` or `tests/corpus/`, on a failed or empty `--list`, and on a fixture outside `tests/corpus/<lang>/<ID>/`. No job reports ABSENT any more | orchestrator (decided, Δ108); DV1c (built, Δ109) |
| 42 | **From DV1c.** `CLAUDE.md` §Authoring mode does not name the acceptance test (`tests/acceptance/guard_doors.py`) as the by-hand step before a merge that changes the guard, the deny list or the CLI pin (DELTAS Δ107). Optional: a live layer-2 demonstration for doors (a) and (e), two more sessions **Done (found at DV2b-2's close, 2026-10-05):** `CLAUDE.md` §Authoring mode, step 3 of *Authoring sessions and the merge into `main`*, names `python3 tests/acceptance/guard_doors.py all` as that by-hand step (in the tree since DV1c's commit 557f98f). DV2b-2 changed the guard (DELTAS Δ125), so the test is due before the next merge. The layer-2 demonstration stays optional | orchestrator (the naming done; the layer-2 demonstration optional) |
| 43 | **From DV1b, lane-reported without an archived command line**, so not entered in `VERSIONS.md`: in a `--verify-*` run under `--no-cheating`, a hole anywhere in the crate gives exit 1 and drops `verified` and `errors`; the `--time` function breakdown of a partial run lists unselected functions as `success: true`. A Dafny claim that the W-D13 summary names `the_program` with several inputs was not reproduced (it names the first input; `VERSIONS.md` §2.1, row D3). Re-capture before quoting | any phase that quotes them |

## 9. DV0 deliverables and blocking issues for DV1

| design §15.2 DV0 item | status |
|---|---|
| pins | done (`VERSIONS.md` §1) |
| probes D1–D14, P1–P15, legacy CLI, `find-dead-code`, `verus-spec-check`, `claude` flags | done, except D8/D14 client side, G14, G16, P12 (precondition absent), P15 (undefined); P14 partial |
| Docker sandbox | partial: the network pattern works (Δ61); the access route is a user decision (Δ60); no image built |
| Ollama `/v1/messages`, Qwen throughput, pool validity | partial, n = 1, not run |
| BigNat L2–L4 spikes in both languages (complete, in band, empty-body-killed, 3-seed stable) | done, with L1 and extras; complete, gate-killed and 3-seed stable; band mismatches recorded (Δ52, Δ53) |
| first MU/week figure | **not measured**; re-routed to DV2, measured over Release A authoring (DELTAS Δ70; §8 item 29) |

**Blocking or prerequisite for DV1** (no probe outcome blocks DV1a):
1. **Done before the DV0 commit:** `Solutions/spikes/dafny/tools/gate.py.pre-oom-fix`, which kept the unsafe pre-fix defaults (6 workers × `--cores 4`, up to 24 concurrent z3) that `CLAUDE.md` §Resources forbids for a script in the tree, has been deleted. The incident record is in the archive (`spike-verus/_invalid-oom-2026-10-03/README.txt`, §7) and the rules in `CLAUDE.md` §Resources.
2. **At DV1b start:** wire in the course resource-limit pins the orchestrator adopted on 2026-10-03 (Δ56); every DV0 golden involving a resource outcome is re-captured at the pin.
3. **For DV1c's core CI:** the self-hosted `dvci` runner account (design §14.4) was neither set up nor probed in DV0; creating it is a host change for the user (§8 item 31). **Dropped:** the user decided on 2026-10-03 that CI is a local script with no runner account (DELTAS Δ67), so DV1c needs no host change for CI.

**At DV1b's and DV1c's close (2026-10-04).** Item 2 is done for the pins: the Δ56 pins are wired in `scripts/dvl/pins.toml` and recorded in `VERSIONS.md` §2.5. No golden that quotes a resource outcome exists yet, so nothing needed re-capturing; `pins.py` captures every golden at the pin as modules arm. Item 3 stays dropped. No DV0 outcome blocked DV1b or DV1c. Against design §15.2: DV1b shipped `vcheck`, `vaudit`, `specfreeze`, `firsttry` and `pins.py` (DELTAS Δ95–Δ103), and its per-layer crates and check units moved to DV2 (Δ94). DV1c shipped the core CI, `scripts/ci.sh` (Δ104), and passed its acceptance test (Δ107). The G/V corpora were not built (Δ106).

## 10. Side effects and housekeeping

- **Toolchain tree.** Six `dafny server` runs wrote log files into `.toolchain/dafny-4.11.0/dafny/`; the Dafny lane moved them to `dafny/D14-D8-lsp-scoping/server-side-effect-logs/`. `get_toolchain.sh --check` passes for both pins (`dv0-report/toolchain-recheck-{dafny,verus}`).
- **Scratch.** A 148 MB copy of the Dafny install (with `z3/` moved aside, for G22) remains in the session scratchpad (`dafny-noz3`, `dafny-noz3-moved`); the user may delete it.
- **Helper collision.** The Verus and infra lanes both wrote `scratchpad/probe.sh` at about 10:31–10:32:08; one infra probe landed under `verus/` and the infra lane removed it and re-ran it under `infra/`. The Verus lane did not report checking its own runs from that window (Δ66).
- **Superseded archive directories** are not evidence: `spike-dafny/_superseded-run1-2026-10-03/`, `_exploration-2026-10-03-1600/`; `spike-verus/_superseded-run1/`, `_superseded-run2/`, `_invalid-oom-2026-10-03/`, `run3/_stopped-attempt{1,2}/`, `run3/pre-lever-transparent-weight/`; `infra/docker-hostgw-ollama-bridge/` (use `-v2`).
- **Repository state.** Nothing is committed. Untracked: `CLAUDE.md`, `VERSIONS.md`, `scripts/`, `Solutions/` (the spikes), `docs/design/DV0-REPORT.md`, `docs/design/DELTAS.md`.
- **Hard rules.** No lane reported reading a forbidden path or calling a usage-billed model API. The infra lane made two `claude -p` calls on the subscription (`authMethod claude.ai`) and one local Qwen generation.

# R12 verifier-driving tools

Run from the course root. Defaults read learner implementations or explicit
course forms. These tools never locate a reference completion. Commit the five
predictions before observing their answers. Native commands use the course's
pinned toolchain and memory/process caps.

`python3 tools/R12/check_clients.py` gates the actual Dafny and Verus implementations,
then compiles66finite checks per language:63Boolean arrays of lengths0–5 and
three remaining-budget cases. Dafny source is embedded in the root because an
include does not verify included implementations. This can detect concrete code
defects; it is not a universal proof or a judge of model-produced native results.
Unfinished learner sources are refused before compilation.

`python3 tools/R12/admit_forms.py FORM... --native` checks each explicit `.dfy` or
`.rs` task form. Its committed `R12_HINT_SITES` JSON lists one site per source line.
An `expr` site replaces `/*R12_HINT:name*/ true` with a bounded expression using
only its declared identifiers. A `calls` site replaces `/*R12_CALLS:name*/` with
at most eight calls to its listed local proof declarations. Call sites belong
to native proof-declaration bodies; each bare name must uniquely bind in the
same native namespace without shadowing. These are data
vocabularies; arbitrary code, trust statements, attributes, imports, declarations,
comments, strings and newlines are rejected. Native grammar checks independently
preserve declarations/models and executable skeletons, and call sites cannot
name executable functions. Native mode also requires a clean audit and a failing
zero-hole proof-stage baseline. Completion, three-seed robustness and wrong-hint
controls remain separate admission evidence.

The five Python exercises live in `harness/r/fvh_r/engine.py`; extractor, loop and
environment modules expose their public API. This lets the frozen single-file
reference adapter test their composition. The default gate is:

```bash
scripts/vcheck --gate harness/r/fvh_r/engine.py
```

H1py parses ordered normalized wrapper JSON without guessing missing values.
H2py localizes exact diagnostic paths against original trusted spans. H3py bounds
the verdict loop; H4py implements one stage/observe search engine; H5py renders
hint data at fixed sites. The frozen executor owns file actions, tools and
provenance. Policies cannot call tools. An independent provided source-frame
check runs after rendering and before proposing an edit.

The model returns exactly `{"hints":["expression or approved proof calls",...]}`.
The legacy `invariants` key is accepted only for all-expression tasks. It cannot
supply outcome fields, wrapper flags, arbitrary source or a success claim.
The provided seeded policies are `fvh_r.engine:R12Independent`, `R12Repair`,
`R12BestFirst` and `R12BestFirstRaw`. Use the frozen batch `construct="seeded"`.
The plan statement binds the original source with exactly one
`R12_TASK_SHA256: <64 hex>` line; the policy refuses missing/stale bindings
before sampling or editing. Ten generation requests require twelve fixed executor
turns: baseline, at most
ten generations and closure. A baseline native Verify is not a model call. An already-green original form
is rejected as inadmissible rather than counted as a zero-call model success.
Missing native phase/count and synthetic kills remain incomplete observations.

`python3 tools/R12/profiler.py TARGET --symbol SYMBOL --repeats 3` measures each
explicit symbol through `scripts/vcheck --json --measures --symbol ... --isolate`.
A1py is the toolwright body. The CLI freezes source before/after, reports exact
scope and keeps failed/inconclusive outcomes and unavailable resources. Isolated
measurements are not full gates. `tools/R12/test_profiler.py` freezes the provided
models/CLI around the actor body, in addition to behavioral cases.

Live Lab α runs remain subject to actual pre-registration, plan/source hashes,
method grades, container provenance, model/account windows, budgets and the GPU
calendar. Mock/Scripted/Replay checks do not create grades or live results.
Unavailable live apparatus is recorded as deferred under D45; it is never a pass.

`python3 tools/R12/read_trace.py` reads this module's own24-message recorded
conversation. It checks Content-Length against UTF-8 bytes, decoded documents
against wire frames and didOpen text against the committed source fixture. It
never starts a language server or turns a diagnostic into a full gate verdict.

`tools/R12/plan.py` builds Lab alpha's locked plans from the schema-2 stratum
`bench/local/r/labalpha/STRATUM.toml` (DVR4 plan section 3.8): a pilot plan (the
pilot clusters, all four regimes), a confirmatory plan (the confirmatory clusters,
the two primary arms) and a descriptive plan (the descriptive subset, the other two
regimes), each arm a `fvh.labalpha` regime (the equal feedback cap and the
failed-node rule around the engine's policy), three repeats, B = 10. It refuses a
stratum whose tasks are not all admitted against their source bytes, and `fvh run`
refuses a confirmatory or descriptive plan without the committed freeze
(`fvh.prereg.check_roles`). The 40 toy forms of the first build are apparatus
smoke in `bench/local/r/labalpha-smoke/` (CI replay only, never data).

`tools/R12/admit_forms.py FORM --admit HINTS.json --evidence DIR` is the author's
admission run: given a form and its reference hint data explicitly, it runs the
seven controls (frame, failing baseline, lab-gate reference, three seeds, clean
audit, failing empty body under maximal automation, failing wrong hints) and
writes the evidence and the public ADMISSION.json. It never locates a reference.

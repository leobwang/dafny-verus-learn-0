# Lab α task admission and execution

The required main stratum is40native task forms,20Dafny and20Verus. Keep these
course-authored forms separate from the learner's earlier personal bench cards;
the author must not fill personal learner artifacts or label reconstructed
course goals independent/unseen. Record original source, exact statement/domain,
exposure and dependency cluster. The main data assembly is still in progress;
this directory does not yet contain an admitted40-task STRATUM.toml.

A final schema1manifest names lab="R12", pools="bench/public/POOLS.toml" and
its pools_sha256. Each [[card]] has id, lang, path, source_sha256, origin, exposure,
cluster, statement, admission and admission_sha256. Its source is one native
course-relative file under bench/local/r; reference completions remain protected.
A source-bound admission JSON has status="admitted", the exact source_sha256
and all seven checks true: baseline-proof-fails, max-auto-empty-fails,
reference-gate, reference-three-seeds, wrong-hints-fail, audit-clean and
original-model-code-frame. Retain the actual native Result documents behind
those checks. JSON booleans are summary evidence, not authenticated proof
certificates; author review and the frozen execution provenance remain required.

The original form carries R12_HINT_SITES and R12_SOURCE_SPANS manifests.
Expression sites and approved local proof-call sites preserve models and code.
Use tools/R12/admit_forms.py for native parser/frame and baseline checks; those
are only part of admission. In particular, maximal-automation empty-body failure,
complete three-seed references and semantic negative controls cannot be inferred
from a static frame or ordinary baseline failure. An opaque wrapper alone is
not an acceptable substitute for maximal-automation failure.

Each [[unused_public]] names set, task and pool_sha256 from the pinned public
pools. Exclude every previously recorded draw. This slice remains separate,
possibly seen and unrun; its execution would need an explicit registered budget
allocation within the module ceiling and its own exact plan binding/grade.

Once actual admission is complete, tools/R12/plan.py builds reviewable plans
from that manifest. It refuses incomplete/stale strata and never invokes models,
containers, Batch.open or gradebook writes. The Qwen plan uses40tasks×4arms×3
repeats×10generations=480runs/4800calls. The separate Claude plan selects5tasks
per language from the same frozen stratum with an explicit subset seed, ten
calls each plus at most ten sentinels. Both allow12executor turns for baseline,
ten generations and closure. All model calls use the frozen transports.

The frozen plan format has global task/repeat fields, so the40-task/3-repeat
Qwen plan and10-task/1-repeat Claude subset are separate executable plans.
A single preregistration block binds one actual digest at a time. Preserve the
registered method, update its exact plan binding and obtain a genuine matching
grade before each separately executed plan. A fixture grade cannot unlock one.
Creating both files does not authorize or start either experiment.

Record actual costs, truncation, model/account windows and GPU calendar events.
D45 live work remains deferred under the user-directed skip. Docker29.1.3responds
on the author machine at the construction check; that daemon observation is not
validation of pinned images, agent manifests or live provider readiness. No host
execution replaces required container provenance. Mock/Scripted/Replay validates
software behavior only and never supplies missing live rows or grades.

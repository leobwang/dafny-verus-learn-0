from pathlib import Path
import hashlib
root=Path.cwd()
def put(p,t):
 p=root/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
def doc(title,body):return r'''\documentclass[11pt]{article}
\input{preamble}
\title{R12 --- Driving the verifier + Lab $\alpha$ \\ \large '''+title+r'''}
\author{dafny-verus-learn-0}
\date{}
\begin{document}
\maketitle
\sloppy
'''+body+'\n\\end{document}\n'
lines=Path('/home/leobwang/code/research/agentic-formal-veri/cheatsheets.md').read_bytes().splitlines(keepends=True)
cards=[('06.10','Cobblestone',2635,2673),('01.12','HyperTree Proof Search',429,456)]
# Each range ends at the presentation link, before the next heading.
for cid,title,start,end in cards:
 block=b''.join(lines[start-1:end]);assert block.startswith(('### '+cid).encode())
 print(cid,start,end,hashlib.sha256(block).hexdigest())
fields=['Claim and refutation','Feedback and estimand','Arms and fixed configurations','Tasks, strata and exposure','Budget arithmetic','Generation settings and prompts','Cost and throughput','MDE and multiplicity','Seeds and repeats','Version and source bindings','Cheat surface and gates','Exclusions and missing outcomes','Stopping rule','Prediction intervals','Contamination controls','Disclosure','Batch plan binding']
problem=r'''\section*{Instructions}
Commit the five native predictions before checking their results. Read B3 and B4
from your own pinned local notes, then complete B1 before any live Lab $\alpha$
run. B1 is graded by \texttt{/grade-paper R12}; B2 only by
\texttt{/grade-paper R12 --report} after runs. Every method dimension must be at
least3. The frozen harness also requires the exact PREREG hash and the exact
\texttt{plan-sha256:} binding. A calibration fixture cannot unlock a run.

\begin{problem}[pre-registration]\label{prob:B1}
Pre-register where the three fixed search regimes' success-versus-node-budget
curves cross, and whether localized obligations improve best-first search over
raw verifier JSON. Use one engine with independent $(10,1,\mathrm{fifo})$,
repair $(1,10,\mathrm{lifo})$ and best-first $(3,10,\mathrm{best})$; the fourth arm
keeps best-first and changes only feedback to raw. A generated candidate is a
node even when malformed. No configuration is retuned at a budget prefix.
The observation at $k=1,\ldots,10$ is a prefix of the same run, not a new run.

Name falsifiable contrasts, estimands and language strata. Define solved as a
full original-task zero-hole proof-stage gate, with original source, models,
code, levers, audit and executor provenance preserved. Missing scores and empty
localization do not establish success. Specify paired permutation tests at each
registered budget point with Holm correction over the named family, and
bootstrap bands with the task as cluster. Compose \texttt{fvh.stats} rather
than reimplementing estimators. State whether bands are pointwise; do not call
pointwise intervals simultaneous bands. Define how crossing and ties are
reported when uncertainty prevents ordering.

The main local stratum has40tasks,20per language, with an unused public slice
kept separate. Record exact form hashes, admission evidence and source exposure;
course-derived tasks are previously seen. Public tasks must come from an unused
pinned pool and stay explicitly possibly contaminated. The live Qwen ceiling is
$40\times4\times3=480$runs and $480\times10=4800$calls, with10GPU-hours.
Claude's descriptive subset is10tasks,5per language, at10calls plus at most
10sentinels:110calls and10runs. A public-slice pilot is not silently additional
budget: it requires its own bound plan, grading and an explicit allocation within
the same ceiling or remains unrun. No provider or container blocker permits
releasing a quota, replacing the verifier or using host execution for agent code.

State seeds, prompts, settings, per-arm time/token/GPU accounting, throughput
assumption and its measured source, truncation sensitivity, exclusions, stopping
rule,80\%prediction intervals and the fallback when the ceiling is infeasible.
Compute the MDE with \texttt{fvh.stats.mde\_two\_proportions} at the number of
independent task clusters, baseline, paired flag and family-adjusted alpha;
explain why three repeats do not turn40tasks into120independent tasks.
Write all17fields in the answer template. Finalize the batch file, then bind its
actual64hex digest and re-grade the changed registration before execution.
\end{problem}

\begin{problem}[lab-report]\label{prob:B2}
After authorized, unlocked runs, provide one Reproduce command over
\texttt{research/runs/R12/}. Regenerate cumulative success curves at budgets1--10,
paired differences, corrected tests, bootstrap intervals, per-language views,
all arm costs and truncation rates from recorded attempts. Re-judge every claimed
success in the pinned container with the original task form, full gate, audit,
source frame and statement freeze. Report the curve crossing only with its
registered uncertainty rule. Audit20transcript moments including malformed
nodes, empty localization, unknown scores, source/provenance attacks and stopped
requests. Include deviations, prediction-interval scoring and contamination.
Keep Claude's small subset descriptive. Grade method and reproducibility,
never favorable outcomes. If live apparatus is unavailable, record deferred
rows and the exact blocker; a mock/replay result cannot fill a live report.
\end{problem}
'''
for n,(cid,title,start,end) in enumerate(cards,3):
 digest=hashlib.sha256(b''.join(lines[start-1:end])).hexdigest()
 problem+=r'\begin{problem}[paper-card]\label{prob:B'+str(n)+'}\n'+r'\textbf{Card'+cid+': '+title+r'.} Fill Task shape, Oracle, Trust, Cheat surface, Metric, Budget, Variance and Artifact. The card score is the minimum of its eight field scores. Use exactly the local range below; name missing information instead of inventing it.'+'\n'+r'\begin{verbatim}'+'\n'+f"sed -n '{start},{end}p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum\n{digest}  -\n"+r'\end{verbatim}'+'\n'+r'Compare the paper with this lab: what is a search node, who certifies a retained fragment, and which budget or trust claim does not transfer? This lab is bounded annotation search; it implements neither a Coq subgoal splitter nor an AND-hypertree policy/critic training system.'+'\n'+r'\end{problem}'+'\n'
put('paper/R12_problems.tex',doc('Written problems',problem))
blank=r'''% PREREG-BEGIN
\section*{Problem B1 (pre-registration)}\label{ans:B1}
\begin{answer}
'''
for field in fields:blank+='\\textbf{'+field+r':} \dots'+'\n\n'
blank+=r'''A final registration must name the batch plan path and write one actual
\texttt{plan-sha256:}64hex binding. Editing this block after grading requires a
new grade; no placeholder hash unlocks the batch.
\end{answer}
% PREREG-END
\section*{Problem B2 (lab report)}\label{ans:B2}
\begin{answer}
\textbf{Reproduce:} \dots

\textbf{Curves, paired effects, intervals and multiplicity:} \dots

\textbf{Re-judgement, provenance and transcript audit:} \dots

\textbf{Costs, truncation, deviations and prediction intervals:} \dots

\textbf{Contamination and disclosure:} \dots
\end{answer}
'''
cardfields=['Task shape','Oracle','Trust','Cheat surface','Metric','Budget','Variance','Artifact']
for n in [3,4]:
 blank+='\\section*{Problem B'+str(n)+'}\\label{ans:B'+str(n)+'}\n\\begin{answer}\n'
 for f in cardfields:blank+='\\textbf{'+f+r':} \vspace{1cm}'+'\n\n'
 blank+='\\end{answer}\n'
put('paper/R12_answers.tex',doc('My answers',blank))
method=r'''\section*{Problem B1}\label{ans:B1}
\begin{answer}
This is a prospective author method exemplar, not a graded registration, a
live result or a run authorization. A learner must choose and bind actual final
artifacts before grading. It cannot supply a missing task-admission or cost pin.

\textbf{Claim and refutation.} Primary contrast is localized minus raw
best-first cumulative solve rate over the same40tasks at each registered budget
1--10, two-sided; equal or negative estimates with compatible intervals refute a
claim of positive advantage. Secondary comparisons are the three localized
regimes pairwise. Predeclare all40pointwise comparisons as one Holm family.
A crossing is a change in the sign of a registered paired difference; overlapping
pointwise uncertainty gives an unresolved crossing, not evidence of a ranking.

\textbf{Feedback and estimand.} A task's rate at a prefix averages its three
recorded repeated runs. Estimate an arm difference by averaging task-level
paired differences. Pair by original task, retaining every repeated run in its
cluster. Localized feedback derives only from that candidate's trusted native
Result plus original source spans. Raw feedback is the same Result document;
no hidden reference, reference proof or human repair enters either prompt.

\textbf{Arms.} One engine, with independent10/1/fifo, repair1/10/lifo,
best-first3/10/best, and best-first/raw3/10/best. Width/depth/priority remain fixed
across prefixes. Malformed output consumes a node and parent width slot, scores
are advisory only, and unknown scores sort last. Accepted means the full bound
native gate succeeds; score0and an empty obligation list are insufficient.

\textbf{Tasks and exposure.} Admit40forms,20per language, before running. Keep
exact original bytes, models, executable skeleton and allowed proof-call
bindings. Require failing zero-hole proof-stage baselines, complete references
under three seeds and wrong-hint controls. Record course provenance and authorship
rather than claiming course-derived goals are unseen. Keep the public slice
pinned, unused and unrun unless separately allocated and graded.

\textbf{Budgets.}480runs,4800generation calls:120runs/1200calls per Qwen arm;
fixed turns12cover initial native baseline, ten possible generations and closure.
Baseline verification is not a model call; failed/malformed generations are.
Claude's10task descriptive subset allows100calls plus at most10sentinels,110total.
No pilot is additional to these ceilings. Seeds and prompt/source/task/plan hashes
must be materialized before grading; Claude repeats are not controllable seeds.

\textbf{Cost and stopping.}10GPU-hours means36000GPU-seconds, an average ceiling
of7.5GPU-seconds per generation over4800calls before other GPU use. This arithmetic
is not a throughput observation. Pin a current measured token/GPU assumption and
per-arm expected totals. If they exceed the ceiling, retain a locked/deferred
experiment and amend/re-grade a smaller allocation; do not run a favorable arm
first or unlock a reserve. Stop at the fixed node cap, success or exhausted
frontier. Administrative deferrals preserve the frozen resume rules and do not
become best-of-n. State unavailable apparatus without host fallback.

\textbf{Uncertainty.} Use paired permutation tests on40task-level values,
Holm on the40declared comparisons, and \texttt{fvh.stats.bootstrap\_ci} over
whole task-level vectors through a registered scalar statistic for each prefix.
Declare these95\%intervals pointwise. Task clusters, not120repeats, define$n$.
For baseline0.5, pairedTrue, alpha0.05/40, the frozen MDE call below is the
planning approximation; correlation assumptions and repeated measures still
limit interpretation. Register resampling seeds,10000resamples and80\%
prediction intervals for each claim before data.
\begin{verbatim}
from fvh import stats
stats.mde_two_proportions(40, 0.5, alpha=0.05/40, paired=True)
\end{verbatim}

\textbf{Integrity.} Hash the actual engine, adapter, task files, source spans,
prompts and settings. Check source frames independently of the learner renderer;
proof callees must be provided local proof declarations. Keep the full gate,
audit, specfreeze, lever checks and executor/container provenance. Include
killed, truncated and malformed attempts in the registered denominator, with
truncation sensitivity. Reissue only true infra-failed ids under frozen rules.
No absence of a diagnostic becomes proof evidence.

\textbf{Disclosure and binding.} One machine/solver pin, model substitution,
small task set, course exposure and Claude as subject/grader are limitations.
The final learner registration supplies actual prediction intervals, final seeds,
all artifact hashes, cost measurement and a single final plan digest. This
exemplar deliberately has no unlock row or pretend plan binding.
\end{answer}
\section*{Problem B2}\label{ans:B2}
\begin{answer}
No live result is supplied. A valid report regenerates every table from frozen
logs, retains unrun/deferred ids without inventing outcomes, re-judges successes
under original task/frame/model bindings in the pinned container, and distinguishes
pointwise uncertainty from simultaneous bands. Mock/Scripted/Replay fixtures
validate software behavior only. D45 live runs stay deferred under the recorded
user-directed skip. Numeric scores for an imagined experiment are not permitted.
\end{answer}
'''
cob=[
'Coq proof synthesis retains checked prefixes and recursively repairs deepest broken subproofs. GPT-4-0613 is tested on four random100-theorem subsets, with other models also studied; there is no fine-tuning.',
'Coq checks retained fragments and supplies the subgoal structure. CoqHammer is tried before fresh samples. The fail-safe admit marker records an in-progress goal; it is not an accepted completed proof.',
'The checker, original theorem and imported assumptions remain trusted, along with CoqHammer\'s checking route. Soundness of checking does not establish that a theorem faithfully encodes its intended task.',
'A missing goal must not be rewarded as solved. Oracle lemma/decomposition hints are derived from human proofs and must be disclosed. Our lab never introduces admit as an allowed hint or imports the paper\'s repair marker as an acceptance rule.',
'Cobblestone solves48/38/44/43percent on CoqGym100, Wigderson100, PnVRocqLib100 and BB5100. PALM\'s token-matched52/30/35/41shows complementarity. A union63/48/59/61is not one system\'s rate. Added value counts new solved theorems relative to another set.',
'Each invocation first tries hammer and then four whole-proof samples from context/CoT variants; depth at most5, at most5invocations and20samples. Mean1.25USD and14.7minutes applies to the two named subsets. These are not this lab\'s10nodes or a matched GPU budget.',
'The excerpt gives small random subsets and no variance report. It cannot support a confidence interval, zero variance or a general all-project effect. PALM can win on one subset while union gains remain real.',
'Kasibatla et al., ICSE2026, arXiv2410.19940. Pin the local excerpt and disclose Coq/GPT-4-era8K context and oracle sources. The excerpt does not pin a replication commit or provide this course\'s native hint-site environment.'
]
hyper=[
'Backward proving in Metamath, Lean3/Mathlib miniF2F and160Equations Identities with a440M--600M encoder-decoder policy/critic, supervised pretraining followed by online training.',
'Tactics produce AND-hyperedges: each chosen tactic requires every child goal. Prover-checked solved/invalid leaves get1/0; unsolved leaves use a learned critic. A critic score is guidance, not proof acceptance.',
'Trust the actual checker and formal statement, not the policy or product of estimated child values. The product uses an independence assumption. A NumPy floating-point checker was exploited and a miniF2F statement had truncated-subtraction misformalization.',
'Online learners can exploit an unsound checker or an incorrect task statement. Rewarding a critic value without final checking would create another bypass. Our source frame and original task binding address a narrower surface and do not prove checker soundness.',
'Metamath test pass@32is72.4; miniF2F-test pass@64is40.6or41.0in the named compute settings; Equations cumulative91.3is a different denominator. Cumulative transductive headline rates must not be merged with a fixed pass@k comparison.',
'Large-scale online training and search, for example1620A100-days for one7-day miniF2F setting; weights refresh every5minutes and hyperparameters vary per attempt. Training cost and generation budgets differ from this lab\'s fixed ten-node comparisons.',
'The excerpt supplies several benchmarks/settings and ablations but no repeated-run confidence interval for a common fixed experiment. Large compute, transductive cumulative reporting, Lean3 and small models limit transfer.',
'Lample et al., NeurIPS2022, arXiv2205.11491, Evariste. Local lines429--456are pinned. The excerpt alone does not identify this lab\'s replication commit or promise that best-first native annotation search reproduces AND-hypertree learning.'
]
for n,values in [(3,cob),(4,hyper)]:
 method+='\\section*{Problem B'+str(n)+'}\\label{ans:B'+str(n)+'}\n\\begin{answer}\n'
 for field,value in zip(cardfields,values):method+='\\textbf{'+field+':} '+value+'\n\n'
 method+='\\end{answer}\n'
put('paper/solutions/R12_solutions.tex',doc('Reference Solution',method))
put('tests/instructor/fixtures/R12_gold_answers.tex',doc('Gold method calibration fixture',method.replace('Reference Solution','Gold method calibration fixture')))
flawed=r'''% PREREG-BEGIN
\section*{Problem B1}\label{ans:B1}
\begin{answer}
We will prove best-first is superior regardless of the observed rates. Independent
gets one call, best-first gets100. We tune width using each prefix\'s results.
Forty tasks times four arms times three repeats times ten calls is400calls, so
all extra pilots are free. Treat120repeats as independent tasks and stop when our
favorite arm leads. Missing diagnostics and score0count as proofs; allow the
model to change postconditions. Run missing containers on the host. There is no
need to bind a plan, hash a task or disclose previously seen proofs. Claude\'s
controllable seeds eliminate model variance. A mock green result fills every
unrun live row. Confidence is100\%without computing an interval.
\end{answer}
% PREREG-END
\section*{Problem B2}\label{ans:B2}
\begin{answer}
All experiments succeeded; no logs, costs, deviations or re-judgement are needed.
\end{answer}
'''
for n in [3,4]:
 flawed+='\\section*{Problem B'+str(n)+'}\\label{ans:B'+str(n)+'}\n\\begin{answer}\n'
 for f in cardfields:flawed+='\\textbf{'+f+':} Both papers use this course\'s ten-node Verus loop with no training, prove every task, report zero variance and guarantee the intended specification. Every learned value is a checked proof.\n\n'
 flawed+='\\end{answer}\n'
put('tests/instructor/fixtures/R12_flawed_answers.tex',doc('Flawed method calibration fixture',flawed))

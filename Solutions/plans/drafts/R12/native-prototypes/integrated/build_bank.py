from pathlib import Path
root=Path.cwd()
intro='''# R12 bank — Driving the verifier + Lab α

Use CORE.md and design-judgment review. Ask one question per turn, acknowledge
neutrally and grade after the committed draw. Draw A: K1,K2,K3,K5,K9,K11.
Draw B: K4,K6,K7,K8,K10,K12. These are disjoint six-question draws. K2/K8
are fresh native predictions on pure field models, not authenticated wrapper
evidence. Author controls and calibration fixtures are not live actor outcomes.

## Controlled tag vocabulary

| tag | focus |
|---|---|
| `verdict-reading` | exact native result stage/scope |
| `contract-allowlist` | original model and edit frame |
| `eval-reporting` | measurement and evidence scope |
| `loop-invariants` | consumed prefix and original input |
| `pre-registration` | fixed choices and hashed plan |
| `matched-compute-search` | equal nodes and fixed regimes |
| `agent-output-is-data` | bounded proposals and trusted execution |
| `paper-cards` | source-bound claims |
| `json-verdict-channels` | complete native schemas |
| `lsp-and-dafny-server` | captured framed protocol reading |

## Questions

'''
dprobe='''module R12_LiveShape {
 predicate ShapeGate(stage:int,count:int,unfinished:int) {
  stage==2 && count>0 && unfinished==0
 }
 lemma ObserveShape() {assert ShapeGate(2,4,0);}
}
'''
vprobe='''use vstd::prelude::*;
verus! {
 pub open spec fn live_shape_r12(stage:int,count:int,unfinished:int)->bool {
  stage==2 && count>0 && unfinished==0
 }
 proof fn observe_shape_r12() {assert(live_shape_r12(2,0,0));}
}
'''
qs=[
('reconstruct','a native observation','verdict-reading`, `json-verdict-channels','R01','Which fields and original bindings must a candidate carry before a driving loop can stop as solved?','Full proof-stage verified Result, positive count, zero holes/findings/errors, expected target/file hashes and executor provenance. A green compile/test or partial symbol check has different scope. The model never supplies authoritative acceptance.','Read the exact scope instead of searching the message for verified.'),
('predict','fresh field model','verdict-reading`, `contract-allowlist','R01','Commit the complete Dafny probe before running its native referee.\n\n```dafny\n'+dprobe+'```\n\n**Native referee:** verified, zero holes; this proves the printed field predicate only.','The concrete fields satisfy the model. This is not a signed native document, freshness proof or evidence for another file.','Ask which exact expression the verifier actually checked.'),
('diagnose','an unlocalized failure','json-verdict-channels`, `verdict-reading','R05','An error has an unknown file and no matching trusted span. Should the extractor guess a symbol from its message, discard it or retain it?','Retain an unlocalized obligation with original run/language/phase and coordinates. Unknown scope is not solved. Ambiguous equal innermost spans stay unlocalized.','Choose two functions with the same name in distinct paths.'),
('derive','a consumed prefix','loop-invariants`, `contract-allowlist','R06','For a count loop and a first-rejection loop, state what connects the current index to the original flags. Why is an index bound alone insufficient?','Count needs a prefix-count relation and arithmetic bounds; first rejection needs all earlier flags true. At exit, relate the full input and the returned observation, including empty input.','Use equal-length arrays with different flags.'),
('audit','stage and observe','agent-output-is-data`, `matched-compute-search','R09','Why does the engine reserve a generated node before waiting for its native outcome? What if the transport or trusted runner fails?','Generation consumes a node/parent slot; pending evidence binds to that node. Malformed data consumes generation without native execution. Infra/transport statuses propagate under frozen accounting; they cannot erase requests or invent success.','Trace a failure between a proposal and its native Verify.'),
('compare','three regimes at equal cost','matched-compute-search`, `pre-registration','R07','Give the three fixed configurations and explain why retuning depth for each budget invalidates a prefix curve.','Independent10/1/fifo, repair1/10/lifo, best3/10/best, with stable ids and unavailable scores last. Every budget point reads the same trajectory prefix; raw ablation holds the best config fixed.','Compare a budget3prefix with the first three nodes of budget10.'),
('audit','renderer and independent guard','agent-output-is-data`, `contract-allowlist','R10','Why test a buggy renderer against a separate source-frame check? What else does form admission establish?','Renderer purity is learner work; an independent guard protects original bytes. Native admission compares model/declaration/code skeletons and binds callees to local proof declarations. It separately requires proof-stage failing zero-hole baseline; full completion/seeds/negative controls remain required.','Place a marker in a postcondition or executable RHS and ask which boundary rejects it.'),
('predict','fresh empty-count claim','verdict-reading`, `json-verdict-channels','R01','Commit the complete Verus probe before running its native referee.\n\n```rust\n'+vprobe+'```\n\n**Native referee:** failed at verify, zero holes; original field model.','A zero count does not satisfy a strictly positive-count gate even with the printed stage and no holes. This models one condition, not a complete authenticated acceptance route.','Evaluate the count conjunct on the concrete input.'),
('critique','salvage and AND structure','paper-cards`, `matched-compute-search','R11','Compare what Cobblestone retains with HyperTree child values. Which mechanisms does this native annotation lab actually implement?','Cobblestone keeps prover-checked prefixes and repairs supplied subgoals. HyperTree follows all tactic children and trains policy/critic online; product values are estimates. This lab uses fixed annotation sites and best-first guidance, without Coq subgoal splitting or online AND-hypertree training.','Name a mechanism and find its actual course implementation, or disclose it as absent.'),
('audit','costs and clusters','pre-registration`, `eval-reporting','R07','How many runs/calls are planned, and what is the independent uncertainty unit? Where does the unused public slice fit?','480runs/4800Qwen calls,110Claude calls including at most10sentinels. Forty tasks are clusters, repeats remain within tasks. Extra public/pilot execution needs explicit allocation, hash binding and grading within ceilings.','Recompute the product and distinguish an unused slice from a free new experiment.'),
('read','framed server evidence','lsp-and-dafny-server`, `eval-reporting','R05','Read a captured Content-Length frame and publishDiagnostics notification. What does it establish and what is absent?','Length counts UTF-8 body bytes, not characters. A diagnostic belongs to its URI/version and original buffer. Notifications have no request id; params may be arrays for other messages. This is trace reading, not writing a client, proving a full gate or asserting that holes are visible.','Locate actual wire bytes, source URI and native diagnostic before summarizing.'),
('design','a reproducible report','pre-registration`, `eval-reporting','R09','Describe a reproducible curve comparison when some live apparatus is unavailable. Which fields cannot be filled from replay?','Regenerate tables from frozen actual logs, paired task clusters and registered family. Re-judge claimed successes in pinned containers and retain deferred ids. Replay validates implementation only; it cannot supply model costs, human grades, provider windows or unrun outcomes.','Point to one actual run id for each claimed empirical row.')]
out=intro
for i,(kind,title,tags,back,q,insight,move) in enumerate(qs,1):
 out+=f'### K{i} [{kind}] — {title}\n**viva:** yes'+(' (verifier-refereed predict)' if kind=='predict' else '')+f' · **tags:** `{tags}` · **backward-edge:** {back}\n\n{q}\n\n**Target insights.** {insight}\n\n**Misconception → counter-move.** {move}\n\n**Incomplete → narrow.** Name the missing native field or binding. **Off-track → anchor.** Follow one actual candidate through the trusted executor. **Correct → deepen.** State which broader claim still lacks evidence.\n\n'
out+='''## Parallel practice

### PP1 — paired budget spend
Implement remaining credit after two requests under the original arithmetic
domain in both languages. Preserve headers and trust policy.

```dafny
module R12_ParallelCredit {
 method CreditR12(limit:nat,spent:nat) returns(left:nat)
  requires spent+2<=limit
  ensures left+spent+2==limit
 {assume false;}
}
```

```rust
use vstd::prelude::*;
verus! {
#[verifier::external_body]
fn credit_r12(limit:usize,spent:usize)->(left:usize)
 requires spent+2<=limit,
 ensures left+spent+2==limit,
 {unimplemented!()}
}
```

### PP2 — paired later rejection
Prove a strict earlier-index exclusion from the same original prefix fact.
Do not change the domain to exclude a boundary index.

```dafny
module R12_ParallelPrefix {
 lemma EarlierR12(flags:seq<bool>,first:nat,other:nat)
  requires first<=|flags|
  requires forall j:nat :: j<first ==> flags[j]
  requires other<|flags| && !flags[other]
  ensures first<=other
 {assume false;}
}
```

```rust
use vstd::prelude::*;
verus! {
proof fn earlier_r12(flags:Seq<bool>,first:int,other:int)
 requires 0<=first<=flags.len(),
  forall|j:int|0<=j<first ==> flags[j],
  0<=other<flags.len(),!flags[other],
 ensures first<=other,
 {proof_note::assume_false();}
}
```

## Review and debrief

Review original source frames, native scope, generation accounting and costs.
Keep both failed and corrected artifacts. Two readiness failures trigger a
narrower explanation of the same original task, never a weakened replacement.
Check the profiler's exact argv and frame snapshot against the actor delivery.
Keep all D45 live results deferred until actual authorized, unlocked runs exist.
'''
p=root/'.claude/skills/instructor/banks/R12.md';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(out)
# Protected native witnesses for author validation only; no learner solution copied.
b=Path('/tmp/dvl0-dvr2-r12/bank-native');b.mkdir(exist_ok=True)
(b/'k2.dfy').write_text(dprobe);(b/'k8.rs').write_text(vprobe)
blocks=out.split('## Parallel practice',1)[1]
import re
for i,(d,v) in enumerate(zip(re.findall(r'```dafny\n(.*?)```',blocks,re.S),re.findall(r'```rust\n(.*?)```',blocks,re.S)),1):
 (b/f'pp{i}.dfy').write_text(d.replace('{assume false;}','{left:=limit-spent-2;}' if i==1 else '{}'))
 (b/f'pp{i}.rs').write_text(v.replace('#[verifier::external_body]\n','').replace('{unimplemented!()}','{limit-spent-2}').replace('{proof_note::assume_false();}','{}'))

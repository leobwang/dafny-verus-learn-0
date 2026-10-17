/* CONTRACT
goal: refactor the proofs of this file so that the reasoning they share lives in helper lemmas under HELPERS and no proof body is longer than the REFACTOR comment's bound; change no statement
allowed-files:
  - dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q07_frozen.dfy dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` reports no change
  - `scripts/vaudit dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` reports no finding
  - `git diff` from the commit of research/q07_frozen.dfy changes no line of a FROZEN statement, and every new lemma sits under HELPERS
  - no `{:fuel}` attribute is added to any lemma
*/
/*!
# Q07 Refactor — refactorer under harness (`/contract Q07`)

What this file ships: four verified lemmas about compositions of layer L4's
`Add` and `MulLimb`, each proved monolithically (the same reasoning written
out again in every body), in two sections. FROZEN holds the statements the
contract pins: its freeze line compares them with your snapshot. API holds
statements that callers rely on but that no acceptance line pins. HELPERS is
empty: it takes the helper lemmas of the refactor. The file is green with no
hole: `scripts/vcheck` reports it verified. Check command:

    scripts/vcheck dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy

The file is outside every build: no unit includes it.

Before the run:
1. Copy the FROZEN section to research/q07_frozen.dfy: the module's first
   line and its imports, then everything from `### FROZEN` through the end
   of `ScaledSumThree`, then a closing `}`. It is the snapshot the
   contract's freeze line compares against.
2. Commit research/q07_frozen.dfy (and research/q07_frozen.rs, for the Verus
   file) in a commit that leaves this file as shipped. That commit is the
   starting state of both runs below.

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. In a FRESH session, run /contract Q07 on this file.
2. Review the diff from the snapshot's commit and fill REVIEW (the block at
   the end): every changed line; every API statement (weaker than before? a
   conjunct dropped? an attribute added?); every new helper's statement
   (weaker than what its callers need? a `requires` that no caller can
   establish?). A weakened API statement can pass every machine-checked
   acceptance line, so only a reader is sure to catch it.
3. The local replay (item A2, below): the same contract, replayed by a local
   agent with the local Qwen model in a per-run container, from the snapshot's
   commit, with
       scripts/contract_local.sh Q07 --file dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy
   in your own terminal. Its patch and run record land in research/runs/Q07/
   and are never applied to your tree. The module's budget allows one
   replay. Ask first whether it can run on your machine with
       scripts/contract_local.sh Q07 --available
   Audit its patch (research/runs/Q07/<run>/patch.diff) as you audited the
   /contract diff.
4. Fill COMPARISON: which acceptance lines each run met, which statements
   each changed, what only a reader could catch.
*/
module {:disableNonlinearArithmetic} Q07_AgentRefactor {
  import opened QG_L1_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul

  // item: Q07.A1d S5

  // REFACTOR: no proof body longer than 3 lines (lines of code, not counting
  //    blank lines and comments).

  // ### FROZEN

  // Two numbers scaled by one limb, then added: the sum scaled.
  lemma ScaledSum(s: seq<nat>, t: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && d < BASE
    ensures Valid(Add(MulLimb(s, d), MulLimb(t, d)))
    ensures ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == (ToNat(s) + ToNat(t)) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(t, d);
    assert Valid(MulLimb(t, d)) && ToNat(MulLimb(t, d)) == ToNat(t) * d;
    AddCorrect(MulLimb(s, d), MulLimb(t, d));
    assert ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == ToNat(s) * d + ToNat(t) * d;
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
    assert (ToNat(s) + ToNat(t)) * d == ToNat(s) * d + ToNat(t) * d;
  }

  // Three numbers scaled by one limb, then added left to right: the sum scaled.
  lemma ScaledSumThree(s: seq<nat>, t: seq<nat>, u: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && Valid(u) && d < BASE
    ensures Valid(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
    ensures ToNat(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
              == (ToNat(s) + ToNat(t) + ToNat(u)) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(t, d);
    assert Valid(MulLimb(t, d)) && ToNat(MulLimb(t, d)) == ToNat(t) * d;
    MulLimbCorrect(u, d);
    assert Valid(MulLimb(u, d)) && ToNat(MulLimb(u, d)) == ToNat(u) * d;
    AddCorrect(MulLimb(s, d), MulLimb(t, d));
    assert ToNat(Add(MulLimb(s, d), MulLimb(t, d))) == ToNat(s) * d + ToNat(t) * d;
    AddCorrect(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d));
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
    assert (ToNat(s) + ToNat(t)) * d == ToNat(s) * d + ToNat(t) * d;
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s) + ToNat(t), ToNat(u));
    assert (ToNat(s) + ToNat(t) + ToNat(u)) * d == (ToNat(s) + ToNat(t)) * d + ToNat(u) * d;
  }

  // ### API

  // Scaling twice is scaling by the product.
  lemma ScaleTwice(s: seq<nat>, d: nat, e: nat)
    requires Valid(s) && d < BASE && e < BASE
    ensures Valid(MulLimb(MulLimb(s, d), e))
    ensures ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * (d * e)
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    MulLimbCorrect(MulLimb(s, d), e);
    assert ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * d * e;
    LemmaMulIsAssociative(ToNat(s), d, e);
  }

  // A number plus another scaled by one limb.
  lemma AddScaled(a: seq<nat>, s: seq<nat>, d: nat)
    requires Valid(a) && Valid(s) && d < BASE
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == ToNat(a) + ToNat(s) * d
  {
    MulLimbCorrect(s, d);
    assert Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d;
    AddCorrect(a, MulLimb(s, d));
  }

  // ### HELPERS (the refactor's helper lemmas go here)

  // item: Q07.A2d S5
  // The local replay of this contract (Qwen, in a per-run container):
  //     scripts/contract_local.sh Q07 --file dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy
  // See step 3 of the header. Its patch is data: it is never applied to
  // this file.
}

/*
REVIEW (learner-owned; advisory: no script reads it). After the /contract run,
from `git diff` against the snapshot's commit:
  changed lines (file:line, what changed):
  API statements (each: unchanged / weaker, and how):
  new helpers (each: its statement strong enough for every caller? a
  `requires` no caller can establish?):

COMPARISON (learner-owned; advisory). The /contract run and the local replay
(research/runs/Q07/<run>/patch.diff and its run record):
  acceptance lines met (each run):
  statements changed (each run):
  what only a reader could catch:
*/

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
# Q07 Refactor — refactorer under harness (Reference Solution)

Hole-free reference for `dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy`
(author-only): the delivered state, the proof that the contract is
satisfiable as stated. Same CONTRACT, module, imports, statements, item
markers and order as the agent file; every FROZEN and API body is refactored
to at most 3 lines, and the one helper the refactor needs sits under HELPERS,
after the loud heading. Silent under `scripts/vcheck --ref`; `scripts/vaudit
--ref` reports no finding; `scripts/specfreeze --against` a snapshot of the
shipped FROZEN section reports no change.
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
    AddScaledValue(MulLimb(s, d), t, d, ToNat(s) * d);
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s), ToNat(t));
  }

  // Three numbers scaled by one limb, then added left to right: the sum scaled.
  lemma ScaledSumThree(s: seq<nat>, t: seq<nat>, u: seq<nat>, d: nat)
    requires Valid(s) && Valid(t) && Valid(u) && d < BASE
    ensures Valid(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
    ensures ToNat(Add(Add(MulLimb(s, d), MulLimb(t, d)), MulLimb(u, d)))
              == (ToNat(s) + ToNat(t) + ToNat(u)) * d
  {
    ScaledSum(s, t, d);
    AddScaledValue(Add(MulLimb(s, d), MulLimb(t, d)), u, d, (ToNat(s) + ToNat(t)) * d);
    LemmaMulIsDistributiveAddOtherWay(d, ToNat(s) + ToNat(t), ToNat(u));
  }

  // ### API

  // Scaling twice is scaling by the product.
  lemma ScaleTwice(s: seq<nat>, d: nat, e: nat)
    requires Valid(s) && d < BASE && e < BASE
    ensures Valid(MulLimb(MulLimb(s, d), e))
    ensures ToNat(MulLimb(MulLimb(s, d), e)) == ToNat(s) * (d * e)
  {
    MulLimbCorrect(s, d);
    MulLimbCorrect(MulLimb(s, d), e);
    LemmaMulIsAssociative(ToNat(s), d, e);
  }

  // A number plus another scaled by one limb.
  lemma AddScaled(a: seq<nat>, s: seq<nat>, d: nat)
    requires Valid(a) && Valid(s) && d < BASE
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == ToNat(a) + ToNat(s) * d
  {
    AddScaledValue(a, s, d, ToNat(a));
  }

  // ### HELPERS (the refactor's helper lemmas go here)

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // The reference refactor has one helper, AddScaledValue: adding a number
  // scaled by one limb to a number whose value is a given v. Its value
  // parameter v is an int, not a nat: with nonlinear arithmetic off, a call
  // that passes `ToNat(s) * d` cannot show the product is a nat. ScaledSum
  // calls it after MulLimbCorrect (which makes its `requires` hold),
  // ScaledSumThree reuses ScaledSum, and AddScaled is the helper at v =
  // ToNat(a). Every body is at most 3 lines.
  //
  // Soft spots a contract run shows (the learner's REVIEW looks for them):
  //   - a helper whose value parameter is a nat: its call fails a subset
  //     constraint, and the fix a contractor reaches for is a `requires` or
  //     a weaker helper;
  //   - a helper called before the fact that makes its `requires` hold;
  //   - a helper stated with the value only, without validity;
  //   - a helper with a `requires` that some caller cannot meet (d > 0);
  //   - a {:fuel} attribute added to a lemma (the contract's audit line);
  //   - an API statement weakened to fit a helper (ScaleTwice's validity
  //     conjunct dropped): the gate, the audit and the freeze line all
  //     accept it, because the snapshot holds FROZEN only. REVIEW is where
  //     it is caught.

  lemma AddScaledValue(a: seq<nat>, s: seq<nat>, d: nat, v: int)
    requires Valid(a) && Valid(s) && d < BASE && ToNat(a) == v
    ensures Valid(Add(a, MulLimb(s, d)))
    ensures ToNat(Add(a, MulLimb(s, d))) == v + ToNat(s) * d
  {
    MulLimbCorrect(s, d);
    AddCorrect(a, MulLimb(s, d));
  }

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

/* CONTRACT — R08 semantic debugger, R-v0
goal: repair the pruning engine so that it honours the interface's laws for its original language Matches
allowed-files:
  - dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy
acceptance:
  - before the first edit, retain the original snapshot and the native verify-stage diagnostic of scripts/vcheck dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy
  - preserve the provided interface, the types, Lang, Res and every requires and ensures; edit only the bodies of the engine's functions and lemmas
  - after every edit run scripts/vcheck dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy and retain the actual stage, holes and diagnostics
  - scripts/vcheck --gate dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy exits 0 with zero counted holes over the full file
  - scripts/vaudit dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy has no findings and scripts/specfreeze --against <snapshot> dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy preserves every original statement
  - name a concrete pattern and word on which the original engine's step law fails, and explain why a verified engine with a changed Lang would not repair this contract; retain costs and the failed attempt
*/
/*!
# R08 semantic debugger (Exercises)

A third engine for A2's step-matcher interface: Config = Re, and each step prunes the
derivative's alternatives, dropping the impossible ones and duplicates. It reaches the
verifier with zero holes and fails at a real postcondition. The fault is semantic: decide
whether the proof or the engine is wrong before you edit anything.
*/
module R08_AgentInfra refines RG_A2_StepMatcher {
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv

  type Pattern = Re
  type Config = Re

  // The engine: simplify the alternatives of a regex.
  function Prune(r: Re): Re
  {
    match r
    case Alt(a, b) =>
      var x, y := Prune(a), Prune(b);
      if x == Empty || x == Eps then y
      else if y == Empty then x
      else if x == y then x
      else Alt(x, y)
    case _ => r
  }

  ghost predicate Lang(p: Pattern, w: seq<char>)
  {
    Matches(p, w)
  }

  ghost predicate Res(st: Config, w: seq<char>)
  {
    Matches(st, w)
  }

  function Start(p: Pattern): Config
  {
    Prune(p)
  }

  function Feed(st: Config, c: char): Config
  {
    Prune(A2.Deriv(st, c))
  }

  predicate Final(st: Config)
  {
    Nullable(st)
  }

  // item: R08.A1d
  // Pruning keeps the language.
  lemma {:induction false} PruneLaw(r: Re, w: seq<char>)
    ensures Matches(Prune(r), w) <==> Matches(r, w)
  {
    match r
    case Alt(a, b) =>
      PruneLaw(a, w);
      PruneLaw(b, w);
    case _ =>
  }

  lemma StartLaw(p: Pattern, w: seq<char>)
  {
    PruneLaw(p, w);
  }

  lemma FeedLaw(st: Config, c: char, w: seq<char>)
  {
    PruneLaw(A2.Deriv(st, c), w);
    A2.DerivCorrect(st, c, w);
  }

  lemma FinalLaw(st: Config)
  {
    B.NullableCorrect(st);
  }
}

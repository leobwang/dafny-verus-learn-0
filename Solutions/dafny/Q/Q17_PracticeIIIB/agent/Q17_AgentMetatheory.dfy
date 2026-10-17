/* CONTRACT
goal: prove every statement under STATEMENTS, which are the statements of research/q17_statements.dfy copied here unchanged; change no statement
allowed-files:
  - dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` exits 0, with zero tool-counted holes
  - `scripts/specfreeze --against research/q17_statements.dfy dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` reports no change
  - `scripts/vaudit dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` reports no finding
  - new lemmas only under HELPERS; a statement you cannot prove is reported, never changed
*/
/*!
# Q17 The metatheory contractor — rung 13 (Reference Solution)

Hole-free reference for `dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy`
(author-only; never learner-visible): the delivery a correct contract run
ends with, on the reference statements. Same CONTRACT, module, given
declarations and order; STATEMENTS holds the reference statement (proved)
and its witness, HELPERS the lemmas the run adds
(Solutions/plans/Q17-code-notes.md).
*/
module Q17_AgentMetatheory {

  // Given (not an item): the language and the generator of std/Q17_Vcgen.dfy
  // (its worked example W2), unchanged.
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)

  datatype BExp = Lt(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)

  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | If(b: BExp, c1: Cmd, c2: Cmd)
               | While(b: BExp, inv: BExp, body: Cmd)

  datatype Outcome = Stuck | Done(s: State)

  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
  }

  predicate Holds(p: BExp, s: State)
  {
    match p
    case Lt(l, r) => Eval(l, s) < Eval(r, s)
    case And(p1, p2) => Holds(p1, s) && Holds(p2, s)
    case Not(p1) => !Holds(p1, s)
    case Imp(p1, p2) => Holds(p1, s) ==> Holds(p2, s)
  }

  function Update(s: State, x: nat, v: int): State
  {
    (y: nat) => if y == x then v else s(y)
  }

  function Exec(c: Cmd, s: State, fuel: nat): Outcome
    decreases fuel, c
  {
    match c
    case Skip => Done(s)
    case Assign(x, e) => Done(Update(s, x, Eval(e, s)))
    case Seq(c1, c2) =>
      (match Exec(c1, s, fuel)
       case Stuck => Stuck
       case Done(s1) => Exec(c2, s1, fuel))
    case If(b, c1, c2) => if Holds(b, s) then Exec(c1, s, fuel) else Exec(c2, s, fuel)
    case While(b, inv, body) =>
      if fuel == 0 then Stuck
      else if !Holds(b, s) then Done(s)
      else
        (match Exec(body, s, fuel - 1)
         case Stuck => Stuck
         case Done(s1) => Exec(While(b, inv, body), s1, fuel - 1))
  }

  function SubstE(t: Expr, x: nat, e: Expr): Expr
  {
    match t
    case Const(n) => Const(n)
    case Var(y) => if y == x then e else Var(y)
    case Plus(a, b) => Plus(SubstE(a, x, e), SubstE(b, x, e))
  }

  function SubstB(p: BExp, x: nat, e: Expr): BExp
  {
    match p
    case Lt(l, r) => Lt(SubstE(l, x, e), SubstE(r, x, e))
    case And(p1, p2) => And(SubstB(p1, x, e), SubstB(p2, x, e))
    case Not(p1) => Not(SubstB(p1, x, e))
    case Imp(p1, p2) => Imp(SubstB(p1, x, e), SubstB(p2, x, e))
  }

  function Pre(c: Cmd, q: BExp): BExp
  {
    match c
    case Skip => q
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Pre(c1, Pre(c2, q))
    case If(b, c1, c2) => And(Imp(b, Pre(c1, q)), Imp(Not(b), Pre(c2, q)))
    case While(b, inv, body) => inv
  }

  function Vcs(c: Cmd, q: BExp): set<BExp>
  {
    match c
    case Skip => {}
    case Assign(x, e) => {}
    case Seq(c1, c2) => Vcs(c1, Pre(c2, q)) + Vcs(c2, q)
    case If(b, c1, c2) => Vcs(c1, q) + Vcs(c2, q)
    case While(b, inv, body) =>
      {Imp(And(inv, b), Pre(body, inv)), Imp(And(inv, Not(b)), q)} + Vcs(body, inv)
  }

  ghost predicate Valid(p: BExp)
  {
    forall s :: Holds(p, s)
  }

  // item: Q17.A1d S8

  // ### STATEMENTS (yours, copied unchanged from research/q17_statements.dfy)

  // reference-only: the learner's statement as committed, with the run's proof
  lemma VcSound(c: Cmd, q: BExp, s: State, fuel: nat)
    requires forall p | p in Vcs(c, q) :: Valid(p)
    requires Holds(Pre(c, q), s)
    ensures Exec(c, s, fuel).Done? ==> Holds(q, Exec(c, s, fuel).s)
    decreases fuel, c
  {
    match c
    case Skip =>
    case Assign(x, e) =>
      SubstSound(q, x, e, s);
    case Seq(c1, c2) =>
      VcSound(c1, Pre(c2, q), s, fuel);
      if Exec(c1, s, fuel).Done? {
        VcSound(c2, q, Exec(c1, s, fuel).s, fuel);
      }
    case If(b, c1, c2) =>
      if Holds(b, s) {
        VcSound(c1, q, s, fuel);
      } else {
        assert Holds(Not(b), s);
        VcSound(c2, q, s, fuel);
      }
    case While(b, inv, body) =>
      if fuel > 0 && Holds(b, s) {
        var i1 := Imp(And(inv, b), Pre(body, inv));
        assert i1 in Vcs(c, q);
        assert Holds(i1, s) && Holds(And(inv, b), s);
        VcSound(body, inv, s, fuel - 1);
        if Exec(body, s, fuel - 1).Done? {
          VcSound(c, q, Exec(body, s, fuel - 1).s, fuel - 1);
        }
      } else if fuel > 0 {
        var i2 := Imp(And(inv, Not(b)), q);
        assert i2 in Vcs(c, q);
        assert Holds(i2, s) && Holds(And(inv, Not(b)), s);
      }
  }

  // reference-only: the learner's witness as committed
  /** Your non-vacuity witness for `VcSound`. */
  lemma VcSoundWitness(s: State)
  {
    var c := Assign(0, Const(1));
    var q := Lt(Const(0), Var(0));
    assert Vcs(c, q) == {};
    assert Holds(Pre(c, q), s);
    VcSound(c, q, s, 0);
    assert Exec(c, s, 0).Done?;
  }

  // ### HELPERS (the contractor's lemmas, only here)

  // reference-only: a helper the metatheory run adds (expressions)
  lemma SubstSoundE(t: Expr, x: nat, e: Expr, s: State)
    ensures Eval(SubstE(t, x, e), s) == Eval(t, Update(s, x, Eval(e, s)))
  {
    match t
    case Const(n) =>
    case Var(y) =>
    case Plus(a, b) =>
      SubstSoundE(a, x, e, s);
      SubstSoundE(b, x, e, s);
  }

  // reference-only: a helper the metatheory run adds (the assignment case)
  lemma SubstSound(p: BExp, x: nat, e: Expr, s: State)
    ensures Holds(SubstB(p, x, e), s) == Holds(p, Update(s, x, Eval(e, s)))
  {
    match p
    case Lt(l, r) =>
      SubstSoundE(l, x, e, s);
      SubstSoundE(r, x, e, s);
    case And(p1, p2) =>
      SubstSound(p1, x, e, s);
      SubstSound(p2, x, e, s);
    case Not(p1) =>
      SubstSound(p1, x, e, s);
    case Imp(p1, p2) =>
      SubstSound(p1, x, e, s);
      SubstSound(p2, x, e, s);
  }
}

// AUDIT (learner-owned; after the contract run)
//   each statement as strong as the prose meant? (proved too easily = a finding):
//   did the contractor stop and report a statement, or change one, or touch another file:
//   the helpers it added, and which of them you would have stated yourself:

/*!
# Q17 — Practice III-B: the VC generator (Exercises)

Imports: none. The module defines a small language of its own and needs
neither the spine nor the standard library.

How to work this file: after H2 (the header of std/Q17_PracticeIIIB.dfy
gives the module's order and its done gate, which covers this file: the
unit is dafny/Q/Q17_PracticeIIIB/std).
1. Read the worked example W2: a language with annotated loops, a run that
   may run out of fuel, and the verification-condition generator `Pre` and
   `Vcs`.
2. H3 is a statement item: you write the statements, the metatheory run
   proves them. Write them under STATEMENTS, with their witnesses, until the
   given corollary `CountCorrect` verifies through them without its assume;
   then commit them (the agent file's header says how) and run
   `/contract Q17` on dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy.
3. Until then your statements are lemmas with no body, each counted as a
   hole. Once the run has delivered, copy its proofs, with the lemmas it
   added under HELPERS, into this file's STATEMENTS section, the statements
   unchanged: then the unit's gate counts no hole here.
4. Stuck for 20 minutes? /tutor Q17.

This file ships with exactly 1 hole: H3, the labelled assume of the given
corollary, counted by `scripts/vcheck`. The unit turns off automatic
induction for lemmas.
*/
module Q17_Vcgen {

  // item: Q17.W2d S8
  /** **W2.** A small language with annotated loops. Expressions `Expr` are
      integer constants, variables (numbered by `nat`) and sums; assertions
      `BExp` compare two expressions with `Lt` and combine with `And`, `Not`
      and `Imp`; commands `Cmd` are `Skip`, assignment, sequence, the
      two-armed `If(b, c1, c2)` and `While(b, inv, body)`, a loop that
      carries its invariant `inv`. A state maps every variable to an
      integer, and `Update(s, x, v)` is `s` with `x` set to `v`.

      `Exec(c, s, fuel)` runs `c` from `s` with a fuel: each loop iteration
      spends one unit, and a run that would need more than it has is
      `Stuck`; otherwise it ends `Done(t)` in a state `t`. `Pre(c, q)` is the
      precondition the generator computes for `c` and the postcondition `q`,
      by syntax: an assignment substitutes into `q`, a sequence composes, an
      `If` splits on its guard, and a loop's precondition is its invariant.
      `Vcs(c, q)` is the set of side conditions the generator emits, two per
      loop (its body's included); `Valid(p)` says `p` holds in every
      state. The generator's claim is that `Pre` and `Vcs` together are
      enough. */
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

  // ===========================================================================
  // The generator's soundness, stated (H3)
  // ===========================================================================

  // Given (not an item): a counting loop, its postcondition, and its side
  // conditions proved valid. From `x0 >= 0`, `Count` sets `x1` to 0 and
  // counts it up to `x0`.
  const Count: Cmd := Seq(Assign(1, Const(0)),
                          While(Lt(Var(1), Var(0)), Not(Lt(Var(0), Var(1))),
                                Assign(1, Plus(Var(1), Const(1)))))

  const CountPost: BExp := And(Not(Lt(Var(1), Var(0))), Not(Lt(Var(0), Var(1))))

  lemma CountVcsValid()
    ensures forall p | p in Vcs(Count, CountPost) :: Valid(p)
  {
    var inv := Not(Lt(Var(0), Var(1)));
    var b := Lt(Var(1), Var(0));
    var body := Assign(1, Plus(Var(1), Const(1)));
    assert Vcs(Count, CountPost) == {Imp(And(inv, b), Pre(body, inv)), Imp(And(inv, Not(b)), CountPost)};
    forall s: State
      ensures Holds(Imp(And(inv, b), Pre(body, inv)), s) && Holds(Imp(And(inv, Not(b)), CountPost), s)
    {
    }
  }

  // item: Q17.H3d S8
  // uses: ensures, witness
  // prose: VcSound
  // contractor: Q17.A1d
  /** **H3.** Statement item. *If every side condition the generator emits
      for `c` and `q` is valid, and the generator's precondition holds in
      the start state, then every run of `c` from that state that ends, ends
      in a state where `q` holds: the generator is sound for partial
      correctness.*

      State it under STATEMENTS below as
      `lemma VcSound(c: Cmd, q: BExp, s: State, fuel: nat)` with no body and
      one `ensures`, and add any further statement you want the metatheory
      run to prove. Write a non-vacuity witness in `VcSoundWitness`: a call
      whose `requires` hold and whose run ends. Then uncomment the checks of
      the given corollary `CountCorrect` and delete its assume: it must
      verify through your statement. In which states does a loop's run use
      its side conditions? */
  // STATEMENTS (Q17.H3d): your statements, here, as lemmas with no body.

  lemma CountCorrect(s: State, fuel: nat)
    requires s(0) >= 0
    ensures Exec(Count, s, fuel).Done? ==> Exec(Count, s, fuel).s(1) == Exec(Count, s, fuel).s(0)
  {
    assume false;  // HOLE: delete once VcSound is stated
    // Uncomment as you go:
    // CountVcsValid();
    // assert Holds(Pre(Count, CountPost), s);
    // VcSound(Count, CountPost, s, fuel);
  }

  /** Your non-vacuity witness for `VcSound`: one call whose `requires` hold
      and whose run ends. */
  lemma VcSoundWitness(s: State)
  {
  }
}

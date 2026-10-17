/*!
# Q14 — Practice II-B: the loop rule (Exercises)

Imports: none. The module defines a small language of its own and needs
neither the spine nor the standard library.

How to work this file: after H3 (the header of std/Q14_PracticeIIB.dfy gives
the module's order and its done gate, which covers this file: the unit is
dafny/Q/Q14_PracticeIIB/std).
1. Read the worked example W2: Q11's language with a loop that carries its
   invariant, a run that may run out of fuel, and the loop's two side
   conditions, which `Wp` does not hold and `Vcs` collects.
2. Replace the hole H4. Read the hint only when stuck.
3. Stuck for 20 minutes? /tutor Q14.

This file ships with exactly 1 hole: H4, a lemma with no body, counted by
`scripts/vcheck`. The unit turns off automatic induction for lemmas.
Nonlinear arithmetic is off in `Q14_Loop` (the attribute on its `module`
line).
*/
module {:disableNonlinearArithmetic} Q14_Loop {

  // item: Q14.W2d S8
  /** **W2.** Q11's small language with a loop. Expressions `Expr` are
      integer constants, variables (numbered by `nat`) and sums; assertions
      `BExp` compare two expressions with `Lt` and combine with `And`, `Not`
      and `Imp`; commands `Cmd` are `Skip`, assignment, sequence, the
      one-armed `IfThen(b, c)` and `While(b, inv, body)`, a loop that carries
      its invariant `inv`. A state maps every variable to an integer.

      `Exec(c, s, fuel)` runs `c` from `s` with a fuel: each loop iteration
      spends one unit, and a run that would need more than it has is
      `Stuck`; otherwise it ends `Done(t)` in a state `t`. `Wp(c, q)` is
      computed by syntax as in Q11, and the weakest precondition it gives a
      loop is just its invariant. That is only sound when the loop's two
      side conditions hold in every state (`Valid`): the invariant and the
      guard give the body's precondition for the invariant, and the
      invariant without the guard gives `q`. `Vcs(c, q)` collects every
      loop's side conditions, its body's included. */
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)

  datatype BExp = Lt(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)

  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | IfThen(b: BExp, c: Cmd)
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

  function Exec(c: Cmd, s: State, fuel: nat): Outcome
    decreases fuel, c
  {
    match c
    case Skip => Done(s)
    case Assign(x, e) => Done((y: nat) => if y == x then Eval(e, s) else s(y))
    case Seq(c1, c2) =>
      (match Exec(c1, s, fuel)
       case Stuck => Stuck
       case Done(s1) => Exec(c2, s1, fuel))
    case IfThen(b, c1) => if Holds(b, s) then Exec(c1, s, fuel) else Done(s)
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

  function Wp(c: Cmd, q: BExp): BExp
  {
    match c
    case Skip => q
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Wp(c1, Wp(c2, q))
    case IfThen(b, c1) => And(Imp(b, Wp(c1, q)), Imp(Not(b), q))
    case While(b, inv, body) => inv
  }

  function Vcs(c: Cmd, q: BExp): set<BExp>
  {
    match c
    case Skip => {}
    case Assign(x, e) => {}
    case Seq(c1, c2) => Vcs(c1, Wp(c2, q)) + Vcs(c2, q)
    case IfThen(b, c1) => Vcs(c1, q)
    case While(b, inv, body) =>
      {Imp(And(inv, b), Wp(body, inv)), Imp(And(inv, Not(b)), q)} + Vcs(body, inv)
  }

  ghost predicate Valid(p: BExp)
  {
    forall s :: Holds(p, s)
  }

  // item: Q14.H4d S8
  /** **H4.** The loop case of soundness for the fuelled runs: if the body
      `c` is sound for the invariant (the first `requires`: from any state
      where `Wp(c, inv)` holds, every run that ends, ends where `inv`
      holds), every side condition of the loop is valid, and its weakest
      precondition holds in `s`, then every run of the loop from `s` that
      ends, ends where `q` holds. The whole soundness proof is a recursion
      over commands; this is the case it needs for `While`, with the
      recursion's result for the body given as a hypothesis. From which
      state does the lemma's own recursive call start, and what does each
      side condition say in the state where it is used? */
  lemma WpSoundWhile(b: BExp, inv: BExp, c: Cmd, q: BExp, s: State, fuel: nat)
    requires forall u: State, f: nat ::
               Holds(Wp(c, inv), u) && Exec(c, u, f).Done? ==> Holds(inv, Exec(c, u, f).s)
    requires forall p :: p in Vcs(While(b, inv, c), q) ==> Valid(p)
    requires Holds(Wp(While(b, inv, c), q), s)
    ensures Exec(While(b, inv, c), s, fuel).Done? ==> Holds(q, Exec(While(b, inv, c), s, fuel).s)
    decreases fuel
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint: the side conditions are quantified over the members of a set:
  //    one gives nothing until the verifier sees that it is a member.
}

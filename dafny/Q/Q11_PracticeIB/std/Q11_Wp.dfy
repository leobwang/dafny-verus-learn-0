/*!
# Q11 — Practice I-B: one case of a soundness proof (Exercises)

Imports: none. The module defines a small language of its own and needs
neither the spine nor the standard library.

How to work this file: after the VC items H7 and H8 (the header of
std/Q11_PracticeIB.dfy gives the module's order and its done gate, which
covers this file: the unit is dafny/Q/Q11_PracticeIB/std).
1. Read the worked example W2: its `Wp` is computed by syntax, the way you
   computed H7's and H8's preconditions by hand.
2. Replace the hole H9. Read the hint only when stuck.
3. Stuck for 20 minutes? /tutor Q11.

This file ships with exactly 1 hole: H9, a lemma with no body, counted by
`scripts/vcheck`. The unit turns off automatic induction for lemmas.
*/module {:disableNonlinearArithmetic} Q11_Wp {

  // item: Q11.W2d S8
  /** **W2.** A small imperative language with a one-armed conditional, and
      its weakest precondition. Expressions `Expr` are integer constants,
      variables (numbered by `nat`) and sums; assertions `BExp` compare two
      expressions with `Lt` and combine with `And`, `Not` and `Imp`
      (implication); commands `Cmd` are `Skip`, assignment, sequence and
      `IfThen(b, c)`, which runs `c` when `b` holds and does nothing
      otherwise. A state maps every variable to an integer. `Eval` and
      `Holds` give expressions and assertions their meaning in a state;
      `Exec` runs a command.

      `Wp(c, q)` computes, by syntax alone, an assertion that holds before `c`
      exactly when `q` holds after it: `Skip` keeps `q`, an assignment
      substitutes its expression for the variable (`SubstB`, built on
      `SubstE`), a sequence composes, and `IfThen(b, c)` is the conjunction
      of two implications, one for each way the condition can go. */
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)

  datatype BExp = Lt(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)

  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | IfThen(b: BExp, c: Cmd)

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

  function Exec(c: Cmd, s: State): State
  {
    match c
    case Skip => s
    case Assign(x, e) => (y: nat) => if y == x then Eval(e, s) else s(y)
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
    case IfThen(b, c1) => if Holds(b, s) then Exec(c1, s) else s
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
  }

  // item: Q11.H9d S8
  // uses: assert
  /** **H9d.** The `IfThen` case of soundness: if the branch `c` is sound for
      `q` (the first `requires`) and `Wp(IfThen(b, c), q)` holds in `s`, then
      `q` holds after `IfThen(b, c)` runs from `s`. The whole soundness
      proof is a recursion over commands; this is the one case it needs for
      `IfThen`, with the recursion's result for `c` given as a hypothesis.
      What does `Wp(IfThen(b, c), q)` say in each of the two ways `b` can go? */
  lemma WpSoundIfThen(b: BExp, c: Cmd, q: BExp, s: State)
    requires forall t :: Holds(Wp(c, q), t) ==> Holds(q, Exec(c, t))
    requires Holds(Wp(IfThen(b, c), q), s)
    ensures Holds(q, Exec(IfThen(b, c), s))
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint: `Holds` of a compound assertion unfolds one level at a time; which
  //    of its `Imp`s and `Not`s must the verifier see unfolded?
}

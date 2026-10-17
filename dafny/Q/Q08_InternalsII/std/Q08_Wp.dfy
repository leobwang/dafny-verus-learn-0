/*!
# Q08 — Internals II: a verified weakest precondition (Exercises)

Imports: none. The module defines a small language of its own and needs
neither the spine nor the standard library.

How to work this file: after std/Q08_Canon.dfy (the header of
std/Q08_InternalsII.dfy gives the module's order and its done gate, which
covers this file: the unit is dafny/Q/Q08_InternalsII/std).
1. Work the weakest precondition by hand first: the prediction P5 and the
   paper lab compute one before this file mechanizes it. Loops stay on paper.
2. Read the worked example W2, then replace each hole in order: H8d, H9d,
   H10d. Read Hint(1) only when stuck, Hint(2) only when still stuck.
3. Stuck for 20 minutes? /tutor Q08.

This file ships with exactly 3 holes: H8d, H9d and H10d, each a lemma with no
body, counted by `scripts/vcheck`. The unit turns off automatic induction for
lemmas: a recursive proof writes its recursive calls.
*/
module {:disableNonlinearArithmetic} Q08_Wp {

  // item: Q08.W2d S8
  /** **W2.** A small imperative language and its weakest precondition.

      Expressions `Expr` are integer constants, variables (numbered by `nat`),
      sums and differences; assertions `BExp` compare two expressions and
      combine with `And`, `Not` and `Imp` (implication); commands `Cmd` are
      assignment, sequence and `If` (no loops: their rule stays on paper). A
      state maps every variable to an integer. `Eval` and `Holds` give
      expressions and assertions their meaning in a state; `Exec` runs a
      command. `Update(s, x, v)` is the state `s` with variable `x` set to
      `v`; it is opaque, and its one lemma `UpdateApply` says what it holds.

      `Wp(c, q)` computes, by syntax alone, an assertion that holds before `c`
      exactly when `q` holds after it: an assignment substitutes its
      expression for the variable in `q` (`SubstB`, built on `SubstE`), a
      sequence composes, and `If` takes each branch under its condition.
      `SubstBOk` lifts the substitution lemma for expressions (H8d) to
      assertions; H9d proves `Wp` sound, and H10d uses that to verify a
      program by computing its precondition. */
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr) | Minus(a: Expr, b: Expr)

  datatype BExp = Le(l: Expr, r: Expr) | And(p: BExp, q: BExp) | Not(p: BExp) | Imp(p: BExp, q: BExp)

  datatype Cmd = Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd) | If(b: BExp, c1: Cmd, c2: Cmd)

  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
    case Minus(a, b) => Eval(a, s) - Eval(b, s)
  }

  predicate Holds(p: BExp, s: State)
  {
    match p
    case Le(l, r) => Eval(l, s) <= Eval(r, s)
    case And(p1, p2) => Holds(p1, s) && Holds(p2, s)
    case Not(p1) => !Holds(p1, s)
    case Imp(p1, p2) => Holds(p1, s) ==> Holds(p2, s)
  }

  opaque function Update(s: State, x: nat, v: int): State
  {
    (y: nat) => if y == x then v else s(y)
  }

  lemma UpdateApply(s: State, x: nat, v: int, y: nat)
    ensures Update(s, x, v)(y) == if y == x then v else s(y)
  {
    reveal Update();  // did: unfolds the opaque Update for this one lemma
  }

  function Exec(c: Cmd, s: State): State
  {
    match c
    case Assign(x, e) => Update(s, x, Eval(e, s))
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
    case If(b, c1, c2) => if Holds(b, s) then Exec(c1, s) else Exec(c2, s)
  }

  function SubstE(t: Expr, x: nat, e: Expr): Expr
  {
    match t
    case Const(n) => Const(n)
    case Var(y) => if y == x then e else Var(y)
    case Plus(a, b) => Plus(SubstE(a, x, e), SubstE(b, x, e))
    case Minus(a, b) => Minus(SubstE(a, x, e), SubstE(b, x, e))
  }

  function SubstB(p: BExp, x: nat, e: Expr): BExp
  {
    match p
    case Le(l, r) => Le(SubstE(l, x, e), SubstE(r, x, e))
    case And(p1, p2) => And(SubstB(p1, x, e), SubstB(p2, x, e))
    case Not(p1) => Not(SubstB(p1, x, e))
    case Imp(p1, p2) => Imp(SubstB(p1, x, e), SubstB(p2, x, e))
  }

  function Wp(c: Cmd, q: BExp): BExp
  {
    match c
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => Wp(c1, Wp(c2, q))
    case If(b, c1, c2) => And(Imp(b, Wp(c1, q)), Imp(Not(b), Wp(c2, q)))
  }

  // The substitution lemma for assertions, given: one case per constructor,
  // each by the lemma for expressions (H8d) or by recursion.
  lemma SubstBOk(p: BExp, x: nat, e: Expr, s: State)
    ensures Holds(SubstB(p, x, e), s) == Holds(p, Update(s, x, Eval(e, s)))
    decreases p
  {
    match p
    case Le(l, r) =>
      SubstEOk(l, x, e, s);
      SubstEOk(r, x, e, s);
    case And(p1, p2) =>
      SubstBOk(p1, x, e, s);
      SubstBOk(p2, x, e, s);
    case Not(p1) =>
      SubstBOk(p1, x, e, s);
    case Imp(p1, p2) =>
      SubstBOk(p1, x, e, s);
      SubstBOk(p2, x, e, s);
  }

  // The program H10d verifies: three assignments that swap variables 0 and 1.
  function Swap(): Cmd
  {
    Seq(Assign(0, Plus(Var(0), Var(1))),
        Seq(Assign(1, Minus(Var(0), Var(1))),
            Assign(0, Minus(Var(0), Var(1)))))
  }

  // item: Q08.H8d S8
  /** **H8d.** The substitution lemma for expressions: evaluating `t` with `e`
      substituted for `x` is evaluating `t` in the state where `x` holds the
      value of `e`. Which case of `t` is the only one that looks into the
      state? */
  lemma SubstEOk(t: Expr, x: nat, e: Expr, s: State)
    ensures Eval(SubstE(t, x, e), s) == Eval(t, Update(s, x, Eval(e, s)))
    decreases t
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): one case per constructor of `Expr`; the operands of a sum or a
  //    difference need the lemma itself.
  // Hint(2): `Update` is opaque: what does the verifier know about
  //    `Update(s, x, v)(y)`, and from which lemma?

  // item: Q08.H9d S8
  /** **H9d.** `Wp` is sound: if `Wp(c, q)` holds before `c` runs, `q` holds
      after it. For a sequence, which postcondition does the first command
      need? For `If`, which half of the precondition applies, and when? */
  lemma WpSound(c: Cmd, q: BExp, s: State)
    requires Holds(Wp(c, q), s)
    ensures Holds(q, Exec(c, s))
    decreases c
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): one case per constructor of `Cmd`; an assignment is the
  //    substitution lemma for assertions.
  // Hint(2): in the `If` case, split on whether the condition holds; in the
  //    branch where it does not, state what holds of `Not(b)`.

  // item: Q08.H10d S8
  /** **H10d.** After `Swap()`, the two variables are in the other order.
      Prove it through `WpSound`, not by running `Exec`: which assertion is the
      postcondition, and what does its weakest precondition say about `s`? */
  lemma SwapOrders(s: State)
    requires s(0) <= s(1)
    ensures Exec(Swap(), s)(1) <= Exec(Swap(), s)(0)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint: the postcondition can be written as a `BExp`, and `Wp` of a
  //    concrete program is a concrete `BExp` the verifier can unfold.
}

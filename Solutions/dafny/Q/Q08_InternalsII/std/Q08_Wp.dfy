/*!
# Q08 — Internals II: a verified weakest precondition (Reference Solution)

Hole-free reference for `dafny/Q/Q08_InternalsII/std/Q08_Wp.dfy` (author-only;
never learner-visible). Same module, names, statements, item markers and order
as the exercise file; every hole is proved. Silent under `scripts/vcheck
--ref`.
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
      value of `e`.

      Reference: structural recursion on `t` (the `decreases t` that ships).
      Constants need nothing; a variable is the one case that looks into
      `Update`, through `UpdateApply` (the variable is `x` or it is not); a sum
      and a difference follow from the lemma on both operands. */
  lemma SubstEOk(t: Expr, x: nat, e: Expr, s: State)
    ensures Eval(SubstE(t, x, e), s) == Eval(t, Update(s, x, Eval(e, s)))
    decreases t
  {
    match t
    case Const(n) =>
    case Var(y) =>
      UpdateApply(s, x, Eval(e, s), y);
    case Plus(a, b) =>
      SubstEOk(a, x, e, s);
      SubstEOk(b, x, e, s);
    case Minus(a, b) =>
      SubstEOk(a, x, e, s);
      SubstEOk(b, x, e, s);
  }

  // item: Q08.H9d S8
  /** **H9d.** `Wp` is sound: if `Wp(c, q)` holds before `c` runs, `q` holds
      after it.

      Reference: structural recursion on `c`. An assignment is `SubstBOk`
      itself. A sequence applies the lemma to `c1` with the postcondition
      `Wp(c2, q)`, then to `c2` from the intermediate state. In `If`, the
      precondition is a conjunction of two implications: the branch that runs
      is the one whose condition holds, and the else branch needs
      `Holds(Not(b), s)` stated before the recursive call, so that its
      implication fires. */
  lemma WpSound(c: Cmd, q: BExp, s: State)
    requires Holds(Wp(c, q), s)
    ensures Holds(q, Exec(c, s))
    decreases c
  {
    match c
    case Assign(x, e) =>
      SubstBOk(q, x, e, s);
    case Seq(c1, c2) =>
      WpSound(c1, Wp(c2, q), s);
      WpSound(c2, q, Exec(c1, s));
    case If(b, c1, c2) =>
      if Holds(b, s) {
        WpSound(c1, q, s);
      } else {
        assert Holds(Not(b), s);
        WpSound(c2, q, s);
      }
  }

  // item: Q08.H10d S8
  /** **H10d.** After `Swap()`, the two variables are in the other order.

      Reference: name the postcondition as an assertion, `Le(Var(1), Var(0))`,
      and ask the verifier to check that its weakest precondition holds in
      `s`: `Wp` is computed by syntax, so that assertion unfolds to a
      comparison of sums and differences of `s(0)` and `s(1)`, which follows
      from the requirement. `WpSound` then carries the postcondition through
      `Exec`, which never has to be unfolded (`Update` stays opaque). */
  lemma SwapOrders(s: State)
    requires s(0) <= s(1)
    ensures Exec(Swap(), s)(1) <= Exec(Swap(), s)(0)
  {
    var post := Le(Var(1), Var(0));
    assert Holds(Wp(Swap(), post), s);
    WpSound(Swap(), post, s);
  }
}

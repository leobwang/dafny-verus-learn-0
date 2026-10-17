/*!
# Q11 — Practice I-B: one case of a soundness proof (Reference Solution)

Hole-free reference for `dafny/Q/Q11_PracticeIB/std/Q11_Wp.dfy` (author-only;
never learner-visible). Same module, names, statements, item markers and
order as the exercise file; the hole is proved. Silent under `scripts/vcheck
--ref`.
*/
module {:disableNonlinearArithmetic} Q11_Wp {

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
      `q` (the first `requires`), so is `IfThen(b, c)`.

      Reference: unfold the precondition into its two implications with one
      assertion; when `b` fails, assert that `Not(b)` holds, so the second
      implication gives `q` in the unchanged state. When `b` holds, the
      hypothesis applies to `s` directly. */
  lemma WpSoundIfThen(b: BExp, c: Cmd, q: BExp, s: State)
    requires forall t :: Holds(Wp(c, q), t) ==> Holds(q, Exec(c, t))
    requires Holds(Wp(IfThen(b, c), q), s)
    ensures Holds(q, Exec(IfThen(b, c), s))
  {
    assert Holds(Imp(b, Wp(c, q)), s) && Holds(Imp(Not(b), q), s);
    if !Holds(b, s) {
      assert Holds(Not(b), s);
    }
  }
}

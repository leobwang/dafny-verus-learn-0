/*!
# Q14 — Practice II-B: the loop rule (Reference Solution)

Hole-free reference for `dafny/Q/Q14_PracticeIIB/std/Q14_Loop.dfy` (author-only;
never learner-visible). Same module, names, statements, item markers and
order as the exercise file; the hole is proved. Silent under `scripts/vcheck
--ref`.
*/
module {:disableNonlinearArithmetic} Q14_Loop {

  // item: Q14.W2d S8
  /** **W2.** Q11's small language with a loop. */
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
  /** **H4.** Reference: induction on the fuel. With no fuel or a false
      guard the run is stuck or stops at once (the second side condition, at
      `s`); with a true guard the first side condition gives the body's
      precondition at `s`, the body's soundness the invariant after it, and
      the recursive call the rest of the loop with one fuel less. */
  lemma WpSoundWhile(b: BExp, inv: BExp, c: Cmd, q: BExp, s: State, fuel: nat)
    requires forall u: State, f: nat ::
               Holds(Wp(c, inv), u) && Exec(c, u, f).Done? ==> Holds(inv, Exec(c, u, f).s)
    requires forall p :: p in Vcs(While(b, inv, c), q) ==> Valid(p)
    requires Holds(Wp(While(b, inv, c), q), s)
    ensures Exec(While(b, inv, c), s, fuel).Done? ==> Holds(q, Exec(While(b, inv, c), s, fuel).s)
    decreases fuel
  {
    var w := While(b, inv, c);
    assert Holds(inv, s);
    if fuel > 0 && Holds(b, s) {
      assert Imp(And(inv, b), Wp(c, inv)) in Vcs(w, q);
      assert Holds(Imp(And(inv, b), Wp(c, inv)), s);
      assert Holds(And(inv, b), s);
      var r := Exec(c, s, fuel - 1);
      if r.Done? {
        assert Holds(inv, r.s);
        assert Exec(w, s, fuel) == Exec(w, r.s, fuel - 1);
        WpSoundWhile(b, inv, c, q, r.s, fuel - 1);
      }
    } else if fuel > 0 {
      assert Imp(And(inv, Not(b)), q) in Vcs(w, q);
      assert Holds(Imp(And(inv, Not(b)), q), s);
      assert Holds(Not(b), s);
      assert Holds(And(inv, Not(b)), s);
    }
  }
}

/*!
# Q17 — Practice III-B: the VC generator (Reference Solution)

Hole-free reference for `dafny/Q/Q17_PracticeIIIB/std/Q17_Vcgen.dfy`
(author-only; never learner-visible). Same module, names, statements, item
markers and order as the exercise file. STATEMENTS holds the reference
statement with the proof a correct metatheory run delivers and the helper
lemmas it adds (marked `// reference-only`), as the learner copies them back
after the run; the corollary's checks are live and the witness is written.
Silent under `scripts/vcheck --ref`.
*/
module Q17_Vcgen {

  // item: Q17.W2d S8
  /** **W2.** A small language with annotated loops and its VC generator. */
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
  /** **H3.** Reference: the side conditions valid (in every state) and the
      precondition true in the start state give `q` in every final state of
      a run that ends. The metatheory run proves it by recursion on the fuel
      and the command, with the substitution lemma for assignment; the loop
      case uses its first side condition in the start state of an
      iteration and its second at the exit, so neither can be weakened to
      the start state of the whole run. */
  // STATEMENTS (Q17.H3d): your statements, here, as lemmas with no body.
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

  // reference-only: the statement (the learner's) and the run's proof
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

  lemma CountCorrect(s: State, fuel: nat)
    requires s(0) >= 0
    ensures Exec(Count, s, fuel).Done? ==> Exec(Count, s, fuel).s(1) == Exec(Count, s, fuel).s(0)
  {
    CountVcsValid();
    assert Holds(Pre(Count, CountPost), s);
    VcSound(Count, CountPost, s, fuel);
  }

  /** Your non-vacuity witness for `VcSound`: one call whose `requires` hold
      and whose run ends. */
  lemma VcSoundWitness(s: State)
  {
    var c := Assign(0, Const(1));
    var q := Lt(Const(0), Var(0));
    assert Vcs(c, q) == {};
    assert Holds(Pre(c, q), s);
    VcSound(c, q, s, 0);
    assert Exec(c, s, 0).Done?;
  }
}

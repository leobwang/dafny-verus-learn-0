/*!
# Q08 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q08_InternalsII/exit/Q08_Exit.dfy`
(author-only; never learner-visible). Same modules, imports, names,
statements, item markers, `need:` lines and order as the exit file, with both
exit items answered. Silent under `scripts/vcheck --ref`.
*/

// A refinement of L4's QG_L4_Spec that stores the limbs most significant
// first: the reversal of L4's order.
module {:disableNonlinearArithmetic} Q08_ExitRev refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  // Given: reversal and its two lemmas.
  function Rev(x: seq<nat>): seq<nat>
    decreases |x|
  {
    if |x| == 0 then [] else Rev(x[1..]) + [x[0]]
  }

  lemma RevAppend(x: seq<nat>, y: seq<nat>)
    ensures Rev(x + y) == Rev(y) + Rev(x)
    decreases |x|
  {
    if |x| == 0 {
      assert x + y == y;
    } else {
      assert (x + y)[1..] == x[1..] + y;
      RevAppend(x[1..], y);
    }
  }

  lemma RevRev(x: seq<nat>)
    ensures Rev(Rev(x)) == x
    decreases |x|
  {
    if |x| != 0 {
      RevAppend(Rev(x[1..]), [x[0]]);
      RevRev(x[1..]);
      assert Rev([x[0]]) == [x[0]];
      assert [x[0]] + x[1..] == x;
    }
  }

  // Given: the limbs of n, most significant first, and their reversal.
  function FromNatMsf(n: nat): seq<nat>
    decreases n
  {
    if n == 0 then [] else FromNatMsf(n / L1.BASE) + [n % L1.BASE]
  }

  lemma FromNatMsfRev(n: nat)
    ensures Rev(FromNatMsf(n)) == L2.FromNat(n)
    decreases n
  {
    if n != 0 {
      FromNatMsfRev(n / L1.BASE);
      RevAppend(FromNatMsf(n / L1.BASE), [n % L1.BASE]);
      assert Rev([n % L1.BASE]) == [n % L1.BASE];
    }
  }

  ghost function Val(x: BigNat): nat { L1.ToNat(Rev(x)) }
  ghost predicate Wf(x: BigNat) { L1.Valid(Rev(x)) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { FromNatMsf(n) }
  function Add(a: BigNat, b: BigNat): BigNat { Rev(L4.Add(Rev(a), Rev(b))) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(Rev(a), Rev(b)) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    FromNatMsfRev(n);
    L3.FromNatCorrect(n);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(Rev(a), Rev(b));
  }

  // item: Q08.X1d S6
  // uses: refines
  // need: lemma AddCorrect(a: BigNat, b: BigNat)
  /** **X1.** The inherited statement of `AddCorrect`, for this refinement:
          requires Wf(a) && Wf(b)
          ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)

      Reference: `Add(a, b)` is `Rev` of L4's sum of the reversals, and `Val`
      and `Wf` look at the reversal of their argument; `RevRev` says that
      reversing `Add(a, b)` gives back L4's sum, about which L4's
      `AddCorrect` (on the valid reversals) says everything. The call alone
      fails: the verifier does not see that `Rev(Rev(x))` is `x`. */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    RevRev(L4.Add(Rev(a), Rev(b)));
    L4.AddCorrect(Rev(a), Rev(b));
  }
}

// A small command language, and a function that right-associates its
// sequences.
module {:disableNonlinearArithmetic} Q08_ExitFlat {
  datatype Expr = Const(n: int) | Var(x: nat) | Plus(a: Expr, b: Expr)

  datatype Cmd = Skip | Assign(x: nat, e: Expr) | Seq(c1: Cmd, c2: Cmd)

  type State = nat -> int

  function Eval(e: Expr, s: State): int
  {
    match e
    case Const(n) => n
    case Var(x) => s(x)
    case Plus(a, b) => Eval(a, s) + Eval(b, s)
  }

  function Exec(c: Cmd, s: State): State
  {
    match c
    case Skip => s
    case Assign(x, e) => (y: nat) => if y == x then Eval(e, s) else s(y)
    case Seq(c1, c2) => Exec(c2, Exec(c1, s))
  }

  function Size(c: Cmd): nat
  {
    match c
    case Skip => 1
    case Assign(_, _) => 1
    case Seq(c1, c2) => Size(c1) + Size(c2) + 1
  }

  function LeftSize(c: Cmd): nat
  {
    match c
    case Seq(c1, _) => Size(c1)
    case _ => 0
  }

  // Given: rotating a left-nested sequence keeps the size and shrinks the
  // left part.
  lemma RotateSmaller(a: Cmd, b: Cmd, d: Cmd)
    ensures Size(Seq(a, Seq(b, d))) == Size(Seq(Seq(a, b), d))
    ensures LeftSize(Seq(a, Seq(b, d))) < LeftSize(Seq(Seq(a, b), d))
  {
    assert Size(Seq(b, d)) == Size(b) + Size(d) + 1;
    assert Size(Seq(a, b)) == Size(a) + Size(b) + 1;
  }

  // Given: right-associate every sequence.
  function Flat(c: Cmd): Cmd
    decreases Size(c), LeftSize(c)
  {
    match c
    case Skip => Skip
    case Assign(x, e) => Assign(x, e)
    case Seq(c1, d) =>
      match c1
      case Seq(a, b) =>
        RotateSmaller(a, b, d);
        Flat(Seq(a, Seq(b, d)))
      case _ => Seq(c1, Flat(d))
  }

  // item: Q08.X2d S7
  // need: lemma FlatSame(c: Cmd, s: State)
  // need: ensures Exec(Flat(c), s) == Exec(c, s)
  /** **X2.** Right-associating a command does not change what it does.

      Reference: the proof follows `Flat`'s own recursion, so it needs
      `Flat`'s measure, `decreases Size(c), LeftSize(c)`: under Dafny's
      default measure for a lemma (its parameters) the recursive call at the
      rotation does not go down, because the command's size stays the same
      there and only its left part shrinks (`RotateSmaller`). The rotation case
      calls the proof on the rotated command; the other `Seq` case on the
      second command, from the state after the first; `Skip` and `Assign`
      need nothing. The direct answer adds that `decreases` clause to
      `FlatSame` itself (verified, the code notes); this twin keeps
      `FlatSame`'s header as shipped and puts the recursion into a helper with
      the measure, because the statement freeze compares a lemma's
      `decreases` clause (the code notes record the tools issue). */
  lemma FlatSame(c: Cmd, s: State)
    ensures Exec(Flat(c), s) == Exec(c, s)
  {
    FlatSameBy(c, s);
  }

  // reference-only: the recursion, under Flat's measure
  lemma FlatSameBy(c: Cmd, s: State)
    ensures Exec(Flat(c), s) == Exec(c, s)
    decreases Size(c), LeftSize(c)
  {
    match c
    case Skip =>
    case Assign(x, e) =>
    case Seq(c1, d) =>
      match c1
      case Seq(a, b) =>
        RotateSmaller(a, b, d);
        FlatSameBy(Seq(a, Seq(b, d)), s);
      case _ =>
        FlatSameBy(d, Exec(c1, s));
  }
}

/*
EXPLAIN-BACK (learner-owned; advisory: no script reads this block and no gate
depends on it). After the exit is scored, choose one Dafny exit item above
that passed, and write in at most 120 words what the verifier needed and why
each step of your proof is there. The detailed-tier viva (/viva Q09) opens on
this block.
  item:
  explanation:
*/

/*!
# Q03 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy`
(author-only): every block answered, every `need:` fragment present in its
code, the commented check of X2 live. Silent: `scripts/vcheck --ref` on it
prints only the summary line.
*/
module Q03_Exit {

  // Given (not an item): the option type of X3.
  datatype Opt<T> = None | Some(value: T)

  // item: Q03.X1d S7
  // uses: ghost, witness
  // need: method FindAtLeast(s: seq<nat>, b: nat) returns (found: bool, ghost w: nat)
  // need: ensures found ==> w < |s| && s[w] >= b
  // need: ensures !found ==> forall j | 0 <= j < |s| :: s[j] < b
  // pair: Q03.X1v
  /** **X1.** Search for a limb at least `b`. Reference: a linear search whose
      invariant says every limb read so far is below `b`; on a hit the ghost
      out-parameter `w` records the index, which is the witness the first
      `ensures` needs. */
  method FindAtLeast(s: seq<nat>, b: nat) returns (found: bool, ghost w: nat)
    ensures found ==> w < |s| && s[w] >= b
    ensures !found ==> forall j | 0 <= j < |s| :: s[j] < b
  {
    found, w := false, 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant forall j | 0 <= j < i :: s[j] < b
      decreases |s| - i
    {
      if s[i] >= b {
        found, w := true, i;
        return;
      }
      i := i + 1;
    }
  }

  // item: Q03.X2d S7
  // uses: subset-type, witness
  // need: type Odd
  // need: method OddCheck(o: Odd) { assert o % 2 == 1; }
  // ### X2 · S7 — Declare the subset type `Odd` of the odd naturals, with whatever Dafny needs to accept it; then uncomment the check below.
  // Reference: Dafny tries 0 as the inhabitant; 0 is even, so `Odd` needs an explicit witness.
  type Odd = x: nat | x % 2 == 1 witness 1  // reference-only: the learner declares it (X2)
  method OddCheck(o: Odd) { assert o % 2 == 1; }  // reference-only: the learner uncomments it (X2)

  // item: Q03.X3d S7
  // uses: exec-check
  // need: method CheckedSub(a: nat, b: nat) returns (r: Opt<nat>)
  // need: ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)
  // pair: Q03.X3v
  /** **X3.** Checked subtraction on naturals. Reference: the runtime test
      `b <= a` is the fact that makes `a - b` a `nat`. */
  method CheckedSub(a: nat, b: nat) returns (r: Opt<nat>)
    ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)
  {
    if b <= a {
      r := Some(a - b);
    } else {
      r := None;
    }
  }
}

/*!
# RG_A5 — the VM and the emitter, layer A5 (PROVIDED, frozen)

Frozen infrastructure, not an exercise. Declared by R16, imported by R16 only
(PLAN.md §2.2, §2.5 step 7; DVR4 step 7's reconciliation). The VM: `Inst`
(`IChar`, `ISplit`, `IJmp`, `IMatch`), the fuelled acceptance `Accepts` (opaque:
use the four one-step lemmas and `AcceptsInside`, never a reveal) and
`AcceptsFrom` (some fuel). The emitter: `Emit` (the code for a regex placed at
an address, falling through to the address after it), `EmitProg`, `CodeAt` and
the layout lemmas of each constructor's code. No correctness lemma of the
emitter is here: stating and proving them is R16's work.
*/
module RG_A5_VM {
  import opened RG_A1_Re

  datatype Inst = IChar(c: char) | ISplit(x: int, y: int) | IJmp(x: int) | IMatch
  type Prog = seq<Inst>

  opaque predicate Accepts(p: Prog, pc: int, w: seq<char>, fuel: nat)
    decreases fuel
  {
    fuel > 0 && 0 <= pc < |p| &&
    match p[pc]
    case IChar(c) => |w| > 0 && w[0] == c && Accepts(p, pc + 1, w[1..], fuel - 1)
    case ISplit(x, y) => Accepts(p, x, w, fuel - 1) || Accepts(p, y, w, fuel - 1)
    case IJmp(x) => Accepts(p, x, w, fuel - 1)
    case IMatch => w == []
  }

  ghost predicate AcceptsFrom(p: Prog, pc: int, w: seq<char>)
  {
    exists fuel: nat :: Accepts(p, pc, w, fuel)
  }

  lemma AcceptsChar(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IChar?
    ensures Accepts(p, pc, w, fuel) <==>
            fuel > 0 && |w| > 0 && w[0] == p[pc].c && Accepts(p, pc + 1, w[1..], fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsSplit(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].ISplit?
    ensures Accepts(p, pc, w, fuel) <==>
            fuel > 0 && (Accepts(p, p[pc].x, w, fuel - 1) || Accepts(p, p[pc].y, w, fuel - 1))
  {
    reveal Accepts();
  }

  lemma AcceptsJmp(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IJmp?
    ensures Accepts(p, pc, w, fuel) <==> fuel > 0 && Accepts(p, p[pc].x, w, fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsMatch(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc] == IMatch
    ensures Accepts(p, pc, w, fuel) <==> fuel > 0 && w == []
  {
    reveal Accepts();
  }

  lemma AcceptsInside(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires Accepts(p, pc, w, fuel)
    ensures fuel > 0 && 0 <= pc < |p|
  {
    reveal Accepts();
  }

  function Emit(r: Re, pc: int): seq<Inst>
    decreases r
  {
    match r
    case Empty => [IJmp(pc)]
    case Eps => []
    case Chr(c) => [IChar(c)]
    case Alt(a, b) =>
      var ca := Emit(a, pc + 1);
      var cb := Emit(b, pc + 2 + |ca|);
      [ISplit(pc + 1, pc + 2 + |ca|)] + ca + [IJmp(pc + 2 + |ca| + |cb|)] + cb
    case Cat(a, b) =>
      var ca := Emit(a, pc);
      ca + Emit(b, pc + |ca|)
    case Star(a) =>
      var ca := Emit(a, pc + 1);
      [ISplit(pc + 1, pc + 2 + |ca|)] + ca + [IJmp(pc)]
  }

  function EmitProg(r: Re): Prog
  {
    Emit(r, 0) + [IMatch]
  }

  predicate CodeAt(p: Prog, pc: int, code: seq<Inst>)
  {
    0 <= pc && pc + |code| <= |p| && forall k | 0 <= k < |code| :: p[pc + k] == code[k]
  }

  lemma LayoutOne(p: Prog, pc: int, r: Re)
    requires r.Empty? || r.Chr?
    requires CodeAt(p, pc, Emit(r, pc))
    ensures p[pc] == Emit(r, pc)[0]
  {
  }

  lemma LayoutAlt(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    ensures var ca := Emit(a, pc + 1);
            var cb := Emit(b, pc + 2 + |ca|);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc + 2 + |ca| + |cb|) && CodeAt(p, pc + 2 + |ca|, cb)
  {
    var code := Emit(Alt(a, b), pc);
    var ca := Emit(a, pc + 1);
    var cb := Emit(b, pc + 2 + |ca|);
    assert p[pc] == code[0];
    assert p[pc + 1 + |ca|] == code[1 + |ca|];
    forall k | 0 <= k < |ca| ensures p[pc + 1 + k] == ca[k] {
      assert code[1 + k] == ca[k];
    }
    forall k | 0 <= k < |cb| ensures p[pc + 2 + |ca| + k] == cb[k] {
      assert code[2 + |ca| + k] == cb[k];
    }
  }

  lemma EmitLenAlt(a: Re, b: Re, pc: int)
    ensures var ca := Emit(a, pc + 1);
            |Emit(Alt(a, b), pc)| == 2 + |ca| + |Emit(b, pc + 2 + |ca|)|
  {
  }

  lemma LayoutCat(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    ensures var ca := Emit(a, pc);
            var cb := Emit(b, pc + |ca|);
            CodeAt(p, pc, ca) && CodeAt(p, pc + |ca|, cb)
  {
    var code := Emit(Cat(a, b), pc);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    forall k | 0 <= k < |ca| ensures p[pc + k] == ca[k] {
      assert code[k] == ca[k];
    }
    forall k | 0 <= k < |cb| ensures p[pc + |ca| + k] == cb[k] {
      assert code[|ca| + k] == cb[k];
    }
  }

  lemma LayoutStar(p: Prog, pc: int, a: Re)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    ensures var ca := Emit(a, pc + 1);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc)
  {
    var code := Emit(Star(a), pc);
    var ca := Emit(a, pc + 1);
    assert p[pc] == code[0];
    assert p[pc + 1 + |ca|] == code[1 + |ca|];
    forall k | 0 <= k < |ca| ensures p[pc + 1 + k] == ca[k] {
      assert code[1 + k] == ca[k];
    }
  }
}

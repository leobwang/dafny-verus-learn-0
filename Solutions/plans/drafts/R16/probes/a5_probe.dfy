// Probe: A5 reconciled (word-relative VM, opaque Accepts, one-step lemmas, Emit, CodeAt,
// layout lemmas) + R16 reference proofs of the fuel-free generalized statements.
module RG_A5_VM_Probe {
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

module R16_Probe {
  import opened RG_A1_Re
  import opened RG_A5_VM_Probe

  // ---- H1 reference: completeness ----
  lemma CompleteFuel(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(r, pc))
    requires Matches(r, u)
    requires Accepts(p, pc + |Emit(r, pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases r, |u|, 1
  {
    match r
    case Eps =>
      assert u + v == v;
      f2 := f;
    case Chr(c) =>
      LayoutOne(p, pc, r);
      assert (u + v)[1..] == v;
      f2 := f + 1;
      AcceptsChar(p, pc, u + v, f2);
    case Alt(a, b) =>
      f2 := CompleteAlt(p, a, b, pc, u, v, f);
    case Cat(a, b) =>
      f2 := CompleteCat(p, a, b, pc, u, v, f);
    case Star(a) =>
      f2 := CompleteStar(p, a, pc, u, v, f);
  }

  lemma {:isolate_assertions} CompleteAlt(p: Prog, a: Re, b: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    requires Matches(Alt(a, b), u)
    requires Accepts(p, pc + |Emit(Alt(a, b), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Alt(a, b), |u|, 0
  {
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    var cb := Emit(b, pc + 2 + |ca|);
    EmitLenAlt(a, b, pc);
    var f1;
    if Matches(a, u) {
      AcceptsJmp(p, pc + 1 + |ca|, v, f + 1);
      f1 := CompleteFuel(p, a, pc + 1, u, v, f + 1);
    } else {
      f1 := CompleteFuel(p, b, pc + 2 + |ca|, u, v, f);
    }
    f2 := f1 + 1;
    AcceptsSplit(p, pc, u + v, f2);
  }

  lemma CompleteCat(p: Prog, a: Re, b: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    requires Matches(Cat(a, b), u)
    requires Accepts(p, pc + |Emit(Cat(a, b), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Cat(a, b), |u|, 0
  {
    LayoutCat(p, pc, a, b);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    assert |Emit(Cat(a, b), pc)| == |ca| + |cb|;
    var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
    var f1 := CompleteFuel(p, b, pc + |Emit(a, pc)|, u[k..], v, f);
    f2 := CompleteFuel(p, a, pc, u[..k], u[k..] + v, f1);
    assert u[..k] + (u[k..] + v) == u + v;
  }

  lemma CompleteStar(p: Prog, a: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    requires Matches(Star(a), u)
    requires Accepts(p, pc + |Emit(Star(a), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Star(a), |u|, 0
  {
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    if u == [] {
      assert u + v == v;
      f2 := f + 1;
    } else {
      var k :| 0 < k <= |u| && Matches(a, u[..k]) && Matches(Star(a), u[k..]);
      var f1 := CompleteFuel(p, Star(a), pc, u[k..], v, f);
      AcceptsJmp(p, pc + 1 + |ca|, u[k..] + v, f1 + 1);
      var f3 := CompleteFuel(p, a, pc + 1, u[..k], u[k..] + v, f1 + 1);
      assert u[..k] + (u[k..] + v) == u + v;
      f2 := f3 + 1;
    }
    AcceptsSplit(p, pc, u + v, f2);
  }

  lemma EmitComplete(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>)
    requires CodeAt(p, pc, Emit(r, pc))
    requires Matches(r, u)
    requires AcceptsFrom(p, pc + |Emit(r, pc)|, v)
    ensures AcceptsFrom(p, pc, u + v)
  {
    var f: nat :| Accepts(p, pc + |Emit(r, pc)|, v, f);
    var f2 := CompleteFuel(p, r, pc, u, v, f);
  }

  // ---- H2 reference: soundness ----
  lemma SoundFuel(p: Prog, r: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(r, pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(r, w[..k]) && Accepts(p, pc + |Emit(r, pc)|, w[k..], f2)
    decreases f, r, 1
  {
    match r
    case Empty =>
      LayoutOne(p, pc, r);
      AcceptsJmp(p, pc, w, f);
      k, f2 := SoundFuel(p, r, pc, w, f - 1);
    case Eps =>
      assert w[..0] == [] && w[0..] == w;
      k, f2 := 0, f;
    case Chr(c) =>
      LayoutOne(p, pc, r);
      AcceptsChar(p, pc, w, f);
      assert w[..1] == [c];
      k, f2 := 1, f - 1;
    case Alt(a, b) =>
      k, f2 := SoundAlt(p, a, b, pc, w, f);
    case Cat(a, b) =>
      k, f2 := SoundCat(p, a, b, pc, w, f);
    case Star(a) =>
      k, f2 := SoundStar(p, a, pc, w, f);
  }

  lemma {:isolate_assertions} SoundAlt(p: Prog, a: Re, b: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Alt(a, b), w[..k]) && Accepts(p, pc + |Emit(Alt(a, b), pc)|, w[k..], f2)
    decreases f, Alt(a, b), 0
  {
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    var cb := Emit(b, pc + 2 + |ca|);
    EmitLenAlt(a, b, pc);
    AcceptsSplit(p, pc, w, f);
    if Accepts(p, pc + 1, w, f - 1) {
      var f1;
      k, f1 := SoundFuel(p, a, pc + 1, w, f - 1);
      AcceptsJmp(p, pc + 1 + |ca|, w[k..], f1);
      f2 := f1 - 1;
      assert Accepts(p, pc + 2 + |ca| + |cb|, w[k..], f2);
    } else {
      k, f2 := SoundFuel(p, b, pc + 2 + |ca|, w, f - 1);
      assert Accepts(p, pc + 2 + |ca| + |cb|, w[k..], f2);
    }
  }

  lemma SoundCat(p: Prog, a: Re, b: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Cat(a, b), w[..k]) && Accepts(p, pc + |Emit(Cat(a, b), pc)|, w[k..], f2)
    decreases f, Cat(a, b), 0
  {
    LayoutCat(p, pc, a, b);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    assert |Emit(Cat(a, b), pc)| == |ca| + |cb|;
    var k1, f1 := SoundFuel(p, a, pc, w, f);
    var k2;
    k2, f2 := SoundFuel(p, b, pc + |Emit(a, pc)|, w[k1..], f1);
    k := k1 + k2;
    assert w[..k][..k1] == w[..k1];
    assert w[..k][k1..] == w[k1..][..k2];
    assert w[k1..][k2..] == w[k..];
  }

  lemma SoundStar(p: Prog, a: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Star(a), w[..k]) && Accepts(p, pc + |Emit(Star(a), pc)|, w[k..], f2)
    decreases f, Star(a), 0
  {
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    AcceptsSplit(p, pc, w, f);
    if Accepts(p, pc + 1, w, f - 1) {
      var k1, f1 := SoundFuel(p, a, pc + 1, w, f - 1);
      AcceptsJmp(p, pc + 1 + |ca|, w[k1..], f1);
      var k2;
      k2, f2 := SoundFuel(p, Star(a), pc, w[k1..], f1 - 1);
      k := k1 + k2;
      assert w[k1..][k2..] == w[k..];
      if k1 > 0 {
        assert w[..k][..k1] == w[..k1];
        assert w[..k][k1..] == w[k1..][..k2];
      } else {
        assert w[..k] == w[k1..][..k2];
      }
    } else {
      assert w[..0] == [] && w[0..] == w;
      k, f2 := 0, f - 1;
    }
  }

  lemma EmitSound(p: Prog, r: Re, pc: int, w: seq<char>)
    requires CodeAt(p, pc, Emit(r, pc))
    requires AcceptsFrom(p, pc, w)
    ensures exists k | 0 <= k <= |w| :: Matches(r, w[..k]) && AcceptsFrom(p, pc + |Emit(r, pc)|, w[k..])
  {
    var f: nat :| Accepts(p, pc, w, f);
    var k, f2 := SoundFuel(p, r, pc, w, f);
  }

  // ---- the whole-program theorem (rexc item) ----
  lemma EmitCorrect(r: Re, s: seq<char>)
    ensures AcceptsFrom(EmitProg(r), 0, s) <==> Matches(r, s)
  {
    var p := EmitProg(r);
    var code := Emit(r, 0);
    assert CodeAt(p, 0, code) by {
      forall k | 0 <= k < |code| ensures p[k] == code[k] {
      }
    }
    assert p[|code|] == IMatch;
    if AcceptsFrom(p, 0, s) {
      EmitSound(p, r, 0, s);
      var k :| 0 <= k <= |s| && Matches(r, s[..k]) && AcceptsFrom(p, |code|, s[k..]);
      var f: nat :| Accepts(p, |code|, s[k..], f);
      AcceptsMatch(p, |code|, s[k..], f);
      assert s[..k] == s;
    }
    if Matches(r, s) {
      AcceptsMatch(p, |code|, [], 1);
      EmitComplete(p, r, 0, s, []);
      assert s + [] == s;
    }
  }
}

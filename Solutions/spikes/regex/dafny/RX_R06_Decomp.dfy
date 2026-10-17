// DVR0 reference (author-only): the R06 decomposer's top statement BackwardsCorrect and
// the reference decomposition (R06.A1d; author notes §7.4). Over layers A1 and A1b.
module RX_R06_Decomp {
  import opened RG_A1_Re
  import opened RG_A1b_Facts

  lemma BackwardsStrLength(s: seq<char>)
    ensures |BackwardsStr(s)| == |s|
    decreases |s|
  {
    // @hole-begin R06.BackwardsStrLength
    if s != [] {
      BackwardsStrLength(s[1..]);
    }
    // @hole-end R06.BackwardsStrLength
  }

  lemma BackwardsStrAppend(u: seq<char>, v: seq<char>)
    ensures BackwardsStr(u + v) == BackwardsStr(v) + BackwardsStr(u)
    decreases |u|
  {
    // @hole-begin R06.BackwardsStrAppend
    if u == [] {
      assert u + v == v;
    } else {
      assert (u + v)[1..] == u[1..] + v;
      assert (u + v)[0] == u[0];
      BackwardsStrAppend(u[1..], v);
    }
    // @hole-end R06.BackwardsStrAppend
  }

  lemma BackwardsStrInvolution(s: seq<char>)
    ensures BackwardsStr(BackwardsStr(s)) == s
    decreases |s|
  {
    // @hole-begin R06.BackwardsStrInvolution
    if s != [] {
      BackwardsStrAppend(BackwardsStr(s[1..]), [s[0]]);
      assert BackwardsStr([s[0]]) == [s[0]] by {
        assert [s[0]][1..] == [];
      }
      BackwardsStrInvolution(s[1..]);
      assert s == [s[0]] + s[1..];
    }
    // @hole-end R06.BackwardsStrInvolution
  }

  lemma BackwardsInvolution(r: Re)
    ensures Backwards(Backwards(r)) == r
    decreases r
  {
    // @hole-begin R06.BackwardsInvolution
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      BackwardsInvolution(a);
      BackwardsInvolution(b);
    case Cat(a, b) =>
      BackwardsInvolution(a);
      BackwardsInvolution(b);
    case Star(a) =>
      BackwardsInvolution(a);
    // @hole-end R06.BackwardsInvolution
  }

  lemma BackwardsSound(r: Re, s: seq<char>)
    requires Matches(r, s)
    ensures Matches(Backwards(r), BackwardsStr(s))
    decreases r, |s|
  {
    // @hole-begin R06.BackwardsSound
    match r
    case Empty =>
    case Eps =>
    case Chr(c) =>
      assert s[1..] == [];
    case Alt(a, b) =>
      if Matches(a, s) {
        BackwardsSound(a, s);
      } else {
        BackwardsSound(b, s);
      }
    case Cat(a, b) =>
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b, s[i..]);
      BackwardsSound(a, s[..i]);
      BackwardsSound(b, s[i..]);
      assert s == s[..i] + s[i..];
      BackwardsStrAppend(s[..i], s[i..]);
      var w := BackwardsStr(s);
      var j := |BackwardsStr(s[i..])|;
      assert w[..j] == BackwardsStr(s[i..]) && w[j..] == BackwardsStr(s[..i]);
    case Star(a) =>
      if s != [] {
        var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
        BackwardsSound(a, s[..i]);
        StarOne(Backwards(a), BackwardsStr(s[..i]));
        BackwardsSound(Star(a), s[i..]);
        StarConcat(Backwards(a), BackwardsStr(s[i..]), BackwardsStr(s[..i]));
        assert s == s[..i] + s[i..];
        BackwardsStrAppend(s[..i], s[i..]);
      }
    // @hole-end R06.BackwardsSound
  }

  lemma BackwardsCorrect(r: Re, s: seq<char>)
    ensures Matches(Backwards(r), BackwardsStr(s)) <==> Matches(r, s)
  {
    // @hole-begin R06.BackwardsCorrect
    if Matches(r, s) {
      BackwardsSound(r, s);
    }
    if Matches(Backwards(r), BackwardsStr(s)) {
      BackwardsSound(Backwards(r), BackwardsStr(s));
      BackwardsInvolution(r);
      BackwardsStrInvolution(s);
    }
    // @hole-end R06.BackwardsCorrect
  }
}

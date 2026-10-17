/* CONTRACT — R06 decomposer, R-v0
goal: prove the one top statement by decomposition, preserving its contract
allowed-files:
  - dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy
acceptance:
  - first add each new helper as a typed hole; rerun green with only leaf holes before proving a helper
  - after every edit scripts/vcheck dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy shows no error; holes are allowed only until the final delivery
  - scripts/vcheck --gate dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy exits 0 with zero counted holes on the whole file
  - scripts/specfreeze --against <snapshot> dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy keeps the original top statement unchanged
  - scripts/vaudit dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy reports no finding; no new assumptions or weakened claims
  - retain the transcript, each green leaf stage and the delivered dependency tree
*/
/* R06 decomposer (Reference Solution). Save the original snapshot before /contract R06.
A1/A1b only; no earlier learner file is imported. */
module R06_AgentDecomposer {
  import opened RG_A1_Re
  import opened RG_A1b_Facts



  lemma BackwardsStrAppend(u: seq<char>, v: seq<char>)
    ensures BackwardsStr(u + v) == BackwardsStr(v) + BackwardsStr(u)
    decreases |u|
  {
    if u == [] {
      assert u + v == v;
    } else {
      assert (u + v)[1..] == u[1..] + v;
      assert (u + v)[0] == u[0];
      BackwardsStrAppend(u[1..], v);
    }
  }

  lemma BackwardsStrInvolution(s: seq<char>)
    ensures BackwardsStr(BackwardsStr(s)) == s
    decreases |s|
  {
    if s != [] {
      BackwardsStrAppend(BackwardsStr(s[1..]), [s[0]]);
      assert BackwardsStr([s[0]]) == [s[0]] by {
        assert [s[0]][1..] == [];
      }
      BackwardsStrInvolution(s[1..]);
      assert s == [s[0]] + s[1..];
    }
  }

  lemma BackwardsInvolution(r: Re)
    ensures Backwards(Backwards(r)) == r
    decreases r
  {
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
  }

  lemma BackwardsSound(r: Re, s: seq<char>)
    requires Matches(r, s)
    ensures Matches(Backwards(r), BackwardsStr(s))
    decreases r, |s|
  {
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
  }

  // item: R06.A1d
  lemma BackwardsCorrect(r: Re, s: seq<char>)
    ensures Matches(Backwards(r), BackwardsStr(s)) <==> Matches(r, s)
  {
    if Matches(r, s) {
      BackwardsSound(r, s);
    }
    if Matches(Backwards(r), BackwardsStr(s)) {
      BackwardsSound(Backwards(r), BackwardsStr(s));
      BackwardsInvolution(r);
      BackwardsStrInvolution(s);
    }
  }
}

/* DECOMPOSITION — learner-owned,22 min after the run.
   Draw helper nodes and caller edges. For every helper state its job and the
   transcript step when it first appeared as a hole. Mark any edit after which
   verification was not green, and the final full gate's count and scope.
   Delete one helper/step in an independent scratch copy to test necessity;
   record the actual observation without claiming unique minimality.
   AGENT DASHBOARD — goal / leaf stages / final gate / audit / freeze /
   transcript / correction: ...
*/

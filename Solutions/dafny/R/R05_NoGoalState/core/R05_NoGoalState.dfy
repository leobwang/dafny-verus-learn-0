/*! R05 — No goal state (Reference Solution).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
For H4 keep the given branch, choice, recursive call and measure: add facts.
Done: all native/Python gates, audit, freeze, strict firsttry, variance and
LATENCY logs, written work, OBLIGATION LOG, fourth bench card and viva.
*/
module R05_NoGoalState {
  import opened RG_A1_Re
  // item: R05.P3dv verdict
  // Ten sequential --json --measures runs of the unchanged W1 copy at the
  // pinned seed: does resource_count repeat, and does wall_s repeat?
  // D:<same|varies>,<same|varies> V:<same|varies>,<same|varies>
  // CHECK P3dv
  // item: R05.P4dv verdict
  // First is correct; Second contains a false assert. Predict --symbol First
  // in each exact specimen: D:<v> V:<v>.
  // CHECK P4dv

  // item: R05.W1d
  lemma SliceBridge(s: seq<char>, i: int)
    requires 0 <= i < |s|
    ensures s[i..] == [s[i]] + s[i+1..]
  {
    var tail := s[i..];
    assert |tail| > 0;
    assert tail[0] == s[i];
    assert tail[1..] == s[i+1..];
    assert tail == [tail[0]] + tail[1..];
    assert s[i..] == [s[i]] + s[i+1..];
  }
  // item: R05.W2d
  @IsolateAssertions
  lemma ScopedArithmetic(n: int)
    requires n >= 0
    ensures n + 3 > n
  {
    assert n + 1 > n by { assert 1 > 0; }
    assert n + 3 > n;
  }
  // item: R05.C1d write:assert-by
  // An assertion-by block proves and exports its assertion; local facts stay local.
  // item: R05.C2d write:isolate-assertions
  // @IsolateAssertions splits a lemma's obligations for diagnosis.
  // item: R05.C4dv recognise:rlimit
  // {:resource_limit N} and #[verifier::rlimit(N)] alter solver work budgets.
  // The pinned wrapper owns course limits; do not change them for a gate.

  // item: R05.H1d
  // pair: R05.H1v
  // uses: assert-by, isolate-assertions
  @IsolateAssertions
  lemma CatAssocLR(a: Re, b: Re, c: Re, s: seq<char>)
    requires Matches(Cat(Cat(a,b),c),s)
    ensures Matches(Cat(a,Cat(b,c)),s)
  {
    // @hole-begin R05.H1d

      var i :| 0 <= i <= |s| && Matches(Cat(a, b), s[..i]) && Matches(c, s[i..]);
      var u := s[..i];
      var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
      var v := s[k..];
      assert u[..k] == s[..k] by { }
      assert u[k..] == s[k..i];
      assert v[..i - k] == s[k..i];
      assert v[i - k..] == s[i..];
      assert Matches(Cat(b, c), v);

    // @hole-end R05.H1d
  }

  // item: R05.H2d
  // pair: R05.H2v
  // uses: assert-by
  lemma CatAssocRL(a: Re, b: Re, c: Re, s: seq<char>)
    requires Matches(Cat(a,Cat(b,c)),s)
    ensures Matches(Cat(Cat(a,b),c),s)
  {
    // @hole-begin R05.H2d

      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(Cat(b, c), s[k..]);
      var v := s[k..];
      var j :| 0 <= j <= |v| && Matches(b, v[..j]) && Matches(c, v[j..]);
      var u := s[..k + j];
      assert u[..k] == s[..k] by { }
      assert u[k..] == s[k..k + j];
      assert v[..j] == s[k..k + j];
      assert v[j..] == s[k + j..];
      assert Matches(Cat(a, b), u);

    // @hole-end R05.H2d
  }

  // item: R05.H3d
  // pair: R05.H3v
  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a,u)
    ensures Matches(Star(a),u)
  {
    // @hole-begin R05.H3d

    if u != [] {
      assert u[..|u|] == u && u[|u|..] == [];
    }

    // @hole-end R05.H3d
  }

  // item: R05.H4d
  // pair: R05.H4v
  // uses: assert-by, isolate-assertions
  @IsolateAssertions
  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a),u) && Matches(Star(a),v)
    ensures Matches(Star(a),u+v)
    decreases |u|
  {
    // @hole-begin R05.H4d
    assert u == [] ==> u+v == v by { }
    // @hole-end R05.H4d
    if u == [] {
    } else {
      var i :| 0 < i <= |u| && Matches(a,u[..i]) && Matches(Star(a),u[i..]);
      StarConcat(a,u[i..],v);
      // Put facts here (and in the empty case) as bisection directs you.
      // @hole-begin R05.H4d
      assert (u+v)[..i] == u[..i] by { }
      assert (u+v)[i..] == u[i..]+v;
      // @hole-end R05.H4d
    }
  }

  /* VARIANCE LOG: ten sequential runs per language on finished H1, pinned
     seed and unchanged inputs. Save each --json --measures document as one
     JSONL line, labelled with its language/task in separate log files if useful.
     LATENCY: fast channel versus whole-file gate, commands and times: ...
     OBLIGATION LOG: calls, failed obligations, facts added and deletion probes: ...
     CALIBRATION: estimated / actual minutes, first-try confidence, correction: ...
  */
  // item: R05.C5dv diverge:r05-c5
  // FINAL CARD: repeated measurements at fixed seed; sealed until P3dv.
}

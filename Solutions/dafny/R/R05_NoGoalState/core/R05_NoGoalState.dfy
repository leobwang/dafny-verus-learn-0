/*! R05 — No goal state (Reference Solution).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
File order: the prediction block, the worked examples (W1, W2), the cards
(C1, C2, C4), the holes (H1 to H4), the logs block, then the final divergence
card (C5). Each hole has a prompt with a guiding question and two hints.
For H4 keep the given branch, choice and measure: add the call and facts.
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

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: R05.W1d
  /** Bisection worked once: each assert states one fact, so a failure names
      the first step the solver could not take. */
  lemma SliceBridge(s: seq<char>, i: int)
    requires 0 <= i < |s|
    ensures s[i..] == [s[i]] + s[i + 1..]
  {
    var tail := s[i..];
    assert |tail| > 0;
    assert tail[0] == s[i];
    assert tail[1..] == s[i + 1..];
    assert tail == [tail[0]] + tail[1..];
    assert s[i..] == [s[i]] + s[i + 1..];
  }

  // item: R05.W2d
  /** `assert ... by` proves its assertion from a local block whose facts stay
      local; @IsolateAssertions gives each assertion its own solver run. */
  @IsolateAssertions
  lemma ScopedArithmetic(n: int)
    requires n >= 0
    ensures n + 3 > n
  {
    assert n + 1 > n by {
      assert 1 > 0;
    }
    assert n + 3 > n;
  }

  // ===========================================================================
  // Cards
  // ===========================================================================

  // item: R05.C1d write:assert-by
  // An assertion-by block proves and exports its assertion; local facts stay local.
  // EXPECT: card-c1d.dfy.specimen fails inside its by block.
  // item: R05.C2d recognise:isolate-assertions
  // @IsolateAssertions splits a lemma's obligations for diagnosis.
  // EXPECT: card-c2d.dfy.specimen names the one false assertion of two.
  // item: R05.C4dv recognise:rlimit
  // {:resource_limit N} and #[verifier::rlimit(N)] alter solver work budgets.
  // The pinned wrapper owns course limits; do not change them for a gate.

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R05.H1d
  // pair: R05.H1v
  /** **H1.** Concatenation re-associates left to right: a match of
      `Cat(Cat(a, b), c)` is a match of `Cat(a, Cat(b, c))`. Take the two
      splits the premise guarantees and build the one the goal needs. Which
      index splits `s` for the goal's outer `Cat`, and which slices of which
      strings must you prove equal for the inner `Cat(b, c)`? */
  @IsolateAssertions
  lemma CatAssocLR(a: Re, b: Re, c: Re, s: seq<char>)
    requires Matches(Cat(Cat(a, b), c), s)
    ensures Matches(Cat(a, Cat(b, c)), s)
  {
    // @hole-begin R05.H1d
    var i :| 0 <= i <= |s| && Matches(Cat(a, b), s[..i]) && Matches(c, s[i..]);
    var u := s[..i];
    var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
    var v := s[k..];
    assert u[..k] == s[..k];
    assert u[k..] == s[k..i];
    assert v[..i - k] == s[k..i];
    assert v[i - k..] == s[i..];
    assert Matches(Cat(b, c), v);
    // @hole-end R05.H1d
  }
  // Hint(1): take the outer split with `:|` (R04 §2.2), then the inner split of
  //    its prefix; write the two witnesses down before any assertion.
  // Hint(2): every slice fact relates a slice of a slice to a slice of `s`
  //    (the slice chain of §1.2); assert them one per line and bisect.

  // item: R05.H2d
  // pair: R05.H2v
  // uses: assert-by
  /** **H2.** The other direction: a match of `Cat(a, Cat(b, c))` is a match
      of `Cat(Cat(a, b), c)`. Which prefix of `s` does the goal's inner
      `Cat(a, b)` receive, and which index of `v` corresponds to an index of
      `s`? */
  lemma CatAssocRL(a: Re, b: Re, c: Re, s: seq<char>)
    requires Matches(Cat(a, Cat(b, c)), s)
    ensures Matches(Cat(Cat(a, b), c), s)
  {
    // @hole-begin R05.H2d
    var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(Cat(b, c), s[k..]);
    var v := s[k..];
    var j :| 0 <= j <= |v| && Matches(b, v[..j]) && Matches(c, v[j..]);
    var u := s[..k + j];
    assert u[..k] == s[..k] by {
    }
    assert u[k..] == s[k..k + j];
    assert v[..j] == s[k..k + j];
    assert v[j..] == s[k + j..];
    assert Matches(Cat(a, b), u);
    // @hole-end R05.H2d
  }
  // Hint(1): the mirror of H1: outer split first, then the split of its suffix.
  // Hint(2): an index `j` of `v` is the index `k + j` of `s`; state each
  //    slice equality that uses this shift.

  // item: R05.H3d
  // pair: R05.H3v
  /** **H3.** One match is a star match, as often as you like: if `a`
      matches `u`, then `Star(a)` matches `u + u + u`. Each chunk of the star
      is one copy of `u`. Where does the first chunk end, which string is left
      after it, and what ends the last one? */
  lemma StarThrice(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u + u + u)
  {
    // @hole-begin R05.H3d
    var t := u + u + u;
    var r := u + u;
    assert t[..|u|] == u;
    assert t[|u|..] == r;
    assert r[..|u|] == u;
    assert r[|u|..] == u;
    assert u[..|u|] == u;
    assert u[|u|..] == [];
    assert Matches(Star(a), u);
    assert Matches(Star(a), r);
    // @hole-end R05.H3d
  }
  // Hint(1): build the star from the back: the last copy of `u` is a star
  //    match (one chunk and the empty rest), then two copies, then three.
  // Hint(2): each step splits a string at `|u|`; state its two slices, and
  //    the star match of the rest.

  // item: R05.H4d
  // pair: R05.H4v
  /** **H4.** Bisect and repair: two star matches concatenate. The case split
      and the choice of the first chunk are given and must stay; the
      induction step and the facts the solver lacks are not. Run the lemma,
      read the obligation it names, and add one line at a time where the
      comments say. Which recursive call gives the rest of `u + v` its star
      match, and which facts connect `u + v` to the chunk and to that call's
      string? */
  @IsolateAssertions
  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(Star(a), v)
    ensures Matches(Star(a), u + v)
    decreases |u|
  {
    // @hole-begin R05.H4d
    assert u == [] ==> u + v == v;
    // @hole-end R05.H4d
    if u == [] {
    } else {
      var i :| 0 < i <= |u| && Matches(a, u[..i]) && Matches(Star(a), u[i..]);
      // Put the recursive call and the facts here (and in the empty case) as
      // bisection directs you.
      // @hole-begin R05.H4d
      StarConcat(a, u[i..], v);
      assert (u + v)[..i] == u[..i];
      assert (u + v)[i..] == u[i..] + v;
      // @hole-end R05.H4d
    }
  }
  // Hint(1): bisect: add `assert false;` at a point to learn whether the
  //    failure is before or after it, then replace it with the fact you need.
  // Hint(2): the first chunk of `u + v` is the first chunk of `u`, and the rest
  //    is `u[i..] + v`, a shorter case of the lemma itself (`decreases |u|`);
  //    call it, then state both slice facts about `u + v`.

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

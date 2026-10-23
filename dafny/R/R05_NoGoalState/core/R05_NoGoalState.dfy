/*! R05 — No goal state (Exercises).
Standalone R, layer A1 only. Do not import earlier learner proofs or A1b.
Four predictions first: commit P1d/P2v in their specimens and P3dv/P4dv in
slots/R05.slots; record scripts/firsttry.sh R05 --check before enabling them.
This file has four holes. The paired crate has four; variance.py has two.
File order: the prediction block, the worked examples (W1, W2), the cards
(C1, C2, C4), the holes (H1 to H4), the logs block, then the final divergence
card (C5). Each hole has a prompt with a guiding question and two hints.
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
  // SLOT: CHECK P3dv
  // item: R05.P4dv verdict
  // First is correct; Second contains a false assert. Predict --symbol First
  // in each exact specimen: D:<v> V:<v>.
  // SLOT: CHECK P4dv

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
  // item: R05.C2d write:isolate-assertions
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
  // uses: assert-by, isolate-assertions
  /** **H1.** Concatenation re-associates left to right: a match of
      `Cat(Cat(a, b), c)` is a match of `Cat(a, Cat(b, c))`. Take the two
      splits the premise guarantees and build the one the goal needs. Which
      index splits `s` for the goal's outer `Cat`, and which slices of which
      strings must you prove equal for the inner `Cat(b, c)`? */
  @IsolateAssertions
  lemma CatAssocLR(a: Re, b: Re, c: Re, s: seq<char>)
    requires Matches(Cat(Cat(a, b), c), s)
    ensures Matches(Cat(a, Cat(b, c)), s)
  // HOLE: write the proof body.
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
  // HOLE: write the proof body.
  // Hint(1): the mirror of H1: outer split first, then the split of its suffix.
  // Hint(2): an index `j` of `v` is the index `k + j` of `s`; state each
  //    slice equality that uses this shift.

  // item: R05.H3d
  // pair: R05.H3v
  /** **H3.** One match is a star match: if `a` matches `u`, `Star(a)` does.
      How many chunks does the star take, and what is left after the chunk
      when `u` is not empty? */
  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u)
  // HOLE: write the proof body.
  // Hint(1): the empty string is a star match by definition; only a non-empty
  //    `u` needs a witness.
  // Hint(2): the whole of `u` is the first chunk; name that split at `|u|`
  //    by its two slices.

  // item: R05.H4d
  // pair: R05.H4v
  // uses: assert-by, isolate-assertions
  /** **H4.** Bisect and repair: two star matches concatenate. The case split,
      the choice of the first chunk and the recursive call are given and must
      stay; the facts the solver lacks are not. Run the lemma, read the
      obligation it names, and add one fact at a time where the comments say.
      Which facts connect `u + v` to the chunk and to the recursive call's
      string? */
  @IsolateAssertions
  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(Star(a), v)
    ensures Matches(Star(a), u + v)
    decreases |u|
  {
    assume false;
    if u == [] {
    } else {
      var i :| 0 < i <= |u| && Matches(a, u[..i]) && Matches(Star(a), u[i..]);
      StarConcat(a, u[i..], v);
      // Put facts here (and in the empty case) as bisection directs you.

    }
  }
  // Hint(1): bisect: add `assert false;` at a point to learn whether the
  //    failure is before or after it, then replace it with the fact you need.
  // Hint(2): the first chunk of `u + v` is the first chunk of `u`, and the rest
  //    is the recursive call's string; both are slice facts about `u + v`.

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

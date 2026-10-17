/* CONTRACT
goal: implement Alphabet, StarHeight and MinLen (Rust: alphabet, star_height, min_len) according to their prose contracts, satisfying all six shipped checks
allowed-files:
  - dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy
acceptance:
  - between edits use only the fast channel: scripts/vcheck --symbol <qualified-symbol> dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy
  - exactly one full scripts/vcheck --gate dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy run, last; exit 0, summary line only
  - zero tool-counted holes; scripts/vaudit dafny/R/R02_Datatypes/agent/R02_AgentImplement.dfy reports zero findings
  - git diff changes only the three definition bodies and, in Verus, the three bound-lemma bodies; remove uninterp only to supply its definition
  - preserve signatures, partial contracts, decreases, prose, checks and headings; no assumptions or verification escape hatch
*/
/*! R02 implementer vs checks: spec-first, R-v0. The prose is the target;
the partial formal contracts and finite checks are incomplete specifications.
Use the fast channel while editing, one full gate last, then audit the artifact.
Do the latency, adversarial and property-test follow-up yourself. */
module R02_AgentImplement {
  import opened RG_A1_Re
  // item: R02.A1d

  /** Alphabet is the finite set of characters in Chr leaves. Empty and
      Eps contribute nothing; both binary constructors combine their children;
      Star retains every character of its body. The partial contract below
      checks just one constructor, not this whole prose contract. */
  function Alphabet(r: Re): set<char>
    ensures r.Empty? ==> Alphabet(r) == {}
    decreases r

  /** StarHeight is the largest number of nested Star constructors on
      any root-to-leaf path. Leaves have height zero. */
  function StarHeight(r: Re): nat
    ensures StarHeight(r) <= NodeCount(r)
    decreases r

  /** MinLen is the length of the shortest string the regex matches.
      Convention: return 0 for a regex matching no string. That convention is
      part of the prose, including concatenations with an impossible factor;
      the Eps-only formal contract is deliberately weaker. */
  function MinLen(r: Re): nat
    ensures r.Eps? ==> MinLen(r) == 0
    decreases r

  // Six shipped checks; two per definition. Preserve them all.
  lemma AlphabetLeafCheck() { assert Alphabet(Chr('q')) == {'q'}; }
  lemma AlphabetPairCheck() { assert Alphabet(Cat(Chr('q'), Chr('r'))) == {'q', 'r'}; }
  lemma StarHeightLeafCheck() { assert StarHeight(Star(Chr('q'))) == 1; }
  lemma StarHeightPairCheck() { assert StarHeight(Cat(Star(Chr('q')), Chr('r'))) == 1; }
  lemma MinLenLeafCheck() { assert MinLen(Chr('q')) == 1; }
  lemma MinLenPairCheck() { assert MinLen(Cat(Chr('q'), Chr('r'))) == 2; }

  /* LATENCY LOG — learner-owned, after /contract R02:
     symbol | wall time | fast or full | exit | transcript location
     ...
     Did the contractor spend its single full gate last? Compare the evidence,
     including failed edits; do not substitute a claimed latency for a run.

     ADVERSARIAL CHECKS — learner-owned, outside the contractor's scope:
     Add checks that follow from each prose contract but are not implied by
     the shipped suite. Explain which plausible wrong implementation they kill.
     Keep all six original checks and every formal contract.

     FIRST PROPERTY TESTS — after completing the hand exercises:
     Add @Test / #[test] code beside the hand exercise implementations in
     core/R02_Datatypes.dfy / src/lib.rs, where IsVoid / is_void is available.
     Use these samples: Empty, Eps, Chr('q'), Alt(Empty, Chr('r')),
     Cat(Empty, Chr('s')), Star(Empty), Cat(Eps, Chr('q')).
     Loop over them and test that nullable implies not void, compare Alt's
     voidness with its two children's results, and add one property of your own.
     Dafny uses a sequence of Re; Rust uses a Vec<Re> and references/Box.
     Run scripts/vcheck --test on the exercise unit/crate and record the result.
     These manual follow-up edits happen after the contractor has finished;
     they do not enlarge its allowed-files list. A passing finite sample is
     evidence about those runs, not a universal proof. Do not insert assume.
  */
}

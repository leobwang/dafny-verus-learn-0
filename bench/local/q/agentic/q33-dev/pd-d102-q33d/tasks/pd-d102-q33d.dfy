// Topic (e) Q33 dev pair pd-d102-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0015.dfy` at
// 387cd69 (MIT; HumanEval/16), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `count_distinct_characters`'s `requires` and `ensures` from its prose (HumanEval's
// prompt above the method), with any definition they need, and one call whose `requires` hold
// in `count_distinct_characters_witness`. You may add proof annotations; never change its
// executable code, and keep every other line.

function to_lower_char(c: char): char
{
    if 'A' <= c <= 'Z' then
        (c as int - 'A' as int + 'a' as int) as char
    else
        c
}
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def count_distinct_characters(string: str) -> int:
    """ Given a string, find out how many distinct characters (regardless of case) does it consist of
    >>> count_distinct_characters('xyzXYZ')
    3
    >>> count_distinct_characters('Jerry')
    4
    """
*/
method count_distinct_characters(s: string) returns (count: int)
// </vc-spec>
// <vc-code>
{
  /* code modified by LLM (iteration 2): Added invariant to prove |seen| <= i */
  var seen := {};
  var i := 0;
  while i < |s|
  {
    seen := seen + {to_lower_char(s[i])};
    i := i + 1;
  }
  count := |seen|;
}
// </vc-code>

/** A non-vacuity witness for `count_distinct_characters`: one call whose `requires` hold. */
method count_distinct_characters_witness()
{
}

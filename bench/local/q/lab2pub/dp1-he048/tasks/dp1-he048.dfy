// Lab 2 public task dp1-he048 (Q15; QPLAN §25.6): vericoding `DH0050.dfy` at 387cd69 (MIT;
// bench/local/q/lab2pub/NOTICE), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py (dafny-lab2-form).
// Write `is_palindrome`'s `requires` and `ensures` from its prose (HumanEval/48's prompt, as
// the HumanEval-Verus set ships it, above the method), with any definition they need, and one
// call whose `requires` hold in `is_palindrome_witness`. You may add proof annotations (loop
// invariants, assertions, proof blocks, lemmas); never change its executable code, and keep
// every other line of the file.
// <vc-preamble>

function to_lower(c: char): char
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
def is_palindrome(text: str):
    """
    Checks if given string is a palindrome
    >>> is_palindrome('')
    True
    >>> is_palindrome('aba')
    True
    >>> is_palindrome('aaaaa')
    True
    >>> is_palindrome('zbcd')
    False
    """
*/
method is_palindrome(text: string) returns (result: bool)
// </vc-spec>
// <vc-code>
{
  var i := 0;
  while i < |text| / 2
  {
    if to_lower(text[i]) != to_lower(text[|text| - 1 - i]) {
      return false;
    }
    i := i + 1;
  }
  return true;
}
// </vc-code>

/** A non-vacuity witness for `is_palindrome`: one call whose `requires` hold. */
method is_palindrome_witness()
{
}

// Lab 2 public task dp4-he159 (Q15; QPLAN §25.6): vericoding `DH0160.dfy` at 387cd69 (MIT;
// bench/local/q/lab2pub/NOTICE), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py (dafny-lab2-form).
// Write `eat`'s `requires` and `ensures` from its prose (HumanEval/159's prompt, as the
// HumanEval-Verus set ships it, above the method), with any definition they need, and one call
// whose `requires` hold in `eat_witness`. You may add proof annotations (loop invariants,
// assertions, proof blocks, lemmas); never change its executable code, and keep every other
// line of the file.
// <vc-preamble>

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def eat(number, need, remaining):
    """
    You're a hungry rabbit, and you already have eaten a certain number of carrots,
    but now you need to eat more carrots to complete the day's meals.
    you should return an array of [ total number of eaten carrots after your meals,
                                    the number of carrots left after your meals ]
    if there are not enough remaining carrots, you will eat all remaining carrots, but will still be hungry.

    Example:
    * eat(5, 6, 10) -> [11, 4]
    * eat(4, 8, 9) -> [12, 1]
    * eat(1, 10, 10) -> [11, 0]
    * eat(2, 11, 5) -> [7, 0]

    Variables:
    @number : integer
        the number of carrots that you have eaten.
    @need : integer
        the number of carrots that you need to eat.
    @remaining : integer
        the number of remaining carrots thet exist in stock

    Constrain:
    * 0 <= number <= 1000
    * 0 <= need <= 1000
    * 0 <= remaining <= 1000

    Have fun :)
    """
*/
method eat(number: int, need: int, remaining: int) returns (result: seq<int>)
// </vc-spec>
// <vc-code>
{
  var eaten := if need <= remaining then need else remaining;
  result := [number + eaten, remaining - eaten];
}
// </vc-code>

/** A non-vacuity witness for `eat`: one call whose `requires` hold. */
method eat_witness()
{
}

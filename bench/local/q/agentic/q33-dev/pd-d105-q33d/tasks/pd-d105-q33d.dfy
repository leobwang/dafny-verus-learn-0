// Topic (e) Q33 dev pair pd-d105-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0043.dfy` at
// 387cd69 (MIT; HumanEval/41), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `car_race_collision`'s `requires` and `ensures` from its prose (HumanEval's prompt
// above the method), with any definition they need, and one call whose `requires` hold in
// `car_race_collision_witness`. You may add proof annotations; never change its executable
// code, and keep every other line.

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def car_race_collision(n: int):
    """
    Imagine a road that's a perfectly straight infinitely long line.
    n cars are driving left to right;  simultaneously, a different set of n cars
    are driving right to left.   The two sets of cars start out being very far from
    each other.  All cars move in the same speed.  Two cars are said to collide
    when a car that's moving left to right hits a car that's moving right to left.
    However, the cars are infinitely sturdy and strong; as a result, they continue moving
    in their trajectory as if they did not collide.

    This function outputs the number of such collisions.
    """
*/
method car_race_collision(n: int) returns (result: int)
// </vc-spec>
// <vc-code>
{
  result := n * n;
}
// </vc-code>

/** A non-vacuity witness for `car_race_collision`: one call whose `requires` hold. */
method car_race_collision_witness()
{
}

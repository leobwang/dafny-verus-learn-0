// Topic (e) Q33 dev pair pd-d107-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0147.dfy` at
// 387cd69 (MIT; HumanEval/147), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `get_max_triples`'s `requires` and `ensures` from its prose (HumanEval's prompt above
// the method), with any definition they need, and one call whose `requires` hold in
// `get_max_triples_witness`. You may add proof annotations; never change its executable code,
// and keep every other line.

function array_element(i: int): int
  requires i >= 1
{
  i * i - i + 1
}

function count_elements_mod_0(n: int): int
  requires n >= 0
  ensures count_elements_mod_0(n) >= 0
{
  if n == 0 then 0
  else if n % 3 == 2 then 1 + count_elements_mod_0(n - 1)
  else count_elements_mod_0(n - 1)
}

function count_elements_mod_1(n: int): int
  requires n >= 0
  ensures count_elements_mod_1(n) >= 0
{
  if n == 0 then 0
  else if n % 3 != 2 then 1 + count_elements_mod_1(n - 1)
  else count_elements_mod_1(n - 1)
}

function combination(n: int, k: int): int
  requires n >= 0 && k >= 0
  ensures combination(n, k) >= 0
  ensures k > n ==> combination(n, k) == 0
  ensures k == 0 || k == n ==> combination(n, k) == 1
  ensures k == 1 ==> combination(n, k) == n
  ensures k == 2 && n >= 2 ==> combination(n, k) == n * (n - 1) / 2
  ensures k == 3 && n >= 3 ==> combination(n, k) == n * (n - 1) * (n - 2) / 6
{
  if k > n || k < 0 then 0
  else if k == 0 || k == n then 1
  else if k == 1 then n
  else if k == 2 then n * (n - 1) / 2
  else if k == 3 then n * (n - 1) * (n - 2) / 6
  else 0
}

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def get_max_triples(n):
    """
    You are given a positive integer n. You have to create an integer array a of length n.
        For each i (1 ≤ i ≤ n), the value of a[i] = i * i - i + 1.
        Return the number of triples (a[i], a[j], a[k]) of a where i < j < k,
    and a[i] + a[j] + a[k] is a multiple of 3.

    Example :
        Input: n = 5
        Output: 1
        Explanation:
        a = [1, 3, 7, 13, 21]
        The only valid triple is (1, 7, 13).
    """
*/
method get_max_triples(n: int) returns (result: int)
// </vc-spec>
// <vc-code>
{
  var count_0 := count_elements_mod_0(n);
  var count_1 := count_elements_mod_1(n);
  result := combination(count_0, 3) + combination(count_1, 3);
}
// </vc-code>

/** A non-vacuity witness for `get_max_triples`: one call whose `requires` hold. */
method get_max_triples_witness()
{
}

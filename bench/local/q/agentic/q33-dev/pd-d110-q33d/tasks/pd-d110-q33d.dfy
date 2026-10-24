// Topic (e) Q33 dev pair pd-d110-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0109.dfy` at
// 387cd69 (MIT; HumanEval/107), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `even_odd_palindrome`'s `requires` and `ensures` from its prose (HumanEval's prompt
// above the method), with any definition they need, and one call whose `requires` hold in
// `even_odd_palindrome_witness`. You may add proof annotations; never change its executable
// code, and keep every other line.

function DigitsOf(n: nat): seq<nat>
    requires n >= 0
{
    if n < 10 then [n]
    else DigitsOf(n / 10) + [n % 10]
}

function ReverseSeq<T>(s: seq<T>): seq<T>
{
    if |s| <= 1 then s
    else ReverseSeq(s[1..]) + [s[0]]
}

function IsPalindrome(n: nat): bool
    requires n >= 0
{
    var digits := DigitsOf(n);
    digits == ReverseSeq(digits)
}

function CountPalindromesInRange(start: nat, end: nat): nat
    requires start >= 1
    decreases end - start + 1
{
    if start > end then 0
    else if IsPalindrome(start) then 1 + CountPalindromesInRange(start + 1, end)
    else CountPalindromesInRange(start + 1, end)
}

function CountEvenPalindromesInRange(start: nat, end: nat): nat
    requires start >= 1
    decreases end - start + 1
{
    if start > end then 0
    else if IsPalindrome(start) && start % 2 == 0 then 1 + CountEvenPalindromesInRange(start + 1, end)
    else CountEvenPalindromesInRange(start + 1, end)
}

function CountOddPalindromesInRange(start: nat, end: nat): nat
    requires start >= 1
    decreases end - start + 1
{
    if start > end then 0
    else if IsPalindrome(start) && start % 2 == 1 then 1 + CountOddPalindromesInRange(start + 1, end)
    else CountOddPalindromesInRange(start + 1, end)
}
function CountPalindromes(n: nat, current: nat, even_count: nat, odd_count: nat): (nat, nat)
    requires current >= 1
    requires n >= 1
    requires current <= n + 1
    decreases n - current + 1
    ensures CountPalindromes(n, current, even_count, odd_count).0 >= even_count
    ensures CountPalindromes(n, current, even_count, odd_count).1 >= odd_count
    ensures CountPalindromes(n, current, even_count, odd_count).0 == even_count + CountEvenPalindromesInRange(current, n)
    ensures CountPalindromes(n, current, even_count, odd_count).1 == odd_count + CountOddPalindromesInRange(current, n)
    ensures CountPalindromes(n, current, even_count, odd_count).0 + CountPalindromes(n, current, even_count, odd_count).1 == even_count + odd_count + CountPalindromesInRange(current, n)
{
    if current > n then
        (even_count, odd_count)
    else if IsPalindrome(current) then
        if current % 2 == 0 then
            CountPalindromes(n, current + 1, even_count + 1, odd_count)
        else
            CountPalindromes(n, current + 1, even_count, odd_count + 1)
    else
        CountPalindromes(n, current + 1, even_count, odd_count)
}
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def even_odd_palindrome(n):
    """
    Given a positive integer n, return a tuple that has the number of even and odd
    integer palindromes that fall within the range(1, n), inclusive.

    Example 1:

        Input: 3
        Output: (1, 2)
        Explanation:
        Integer palindrome are 1, 2, 3. one of them is even, and two of them are odd.

    Example 2:

        Input: 12
        Output: (4, 6)
        Explanation:
        Integer palindrome are 1, 2, 3, 4, 5, 6, 7, 8, 9, 11. four of them are even, and 6 of them are odd.

    Note:
        1. 1 <= n <= 10^3
        2. returned tuple has the number of even and odd integer palindromes respectively.
    """
*/
method even_odd_palindrome(n: nat) returns (result: (nat, nat))
// </vc-spec>
// <vc-code>
{
  result := CountPalindromes(n, 1, 0, 0);
}
// </vc-code>

/** A non-vacuity witness for `even_odd_palindrome`: one call whose `requires` hold. */
method even_odd_palindrome_witness()
{
}

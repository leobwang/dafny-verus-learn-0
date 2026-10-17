# TRUST.md — what is proved, what is tested, what is assumed

Learner-owned: you write every section, when the module named in its heading asks for it; no AI session writes it. This is one shared file for both tracks (design D3): each version is a section, a later section adds to the earlier ones and never relaxes them, and where two sections conflict, the stricter rule wins. Presenting an unproved claim as proved fails the work it describes (`/review-code` grades it 1).

<!-- Section format, one section per version. Replace "(not written yet)" with the date when you write it:
     ## Q-v0 — Q06, YYYY-MM-DD
     Scope: <the artifact or artifacts this section covers>
     Proved: <claim> — evidence: <the command that re-checks it, and the output it must show>
     Tested: <claim> — evidence: <the test command and what it exercises>
     Assumed: <claim, or trusted component> — why it is trusted, and what would break if it were wrong
     Escape hatches: <each one, with its file:line and its justification; none is allowed unless listed here> -->

## Q-v0 — Q06 (not written yet)

<!-- What Q06 asks for here (its chapter's TRUST.md v0 step): your trusted-base inventory for Q04–Q06.
     Per language: the front end, the solver and its version, the standard library's trusted parts,
     the course wrappers and the given layers; for each entry, what would make a green run wrong. -->

## Q-v1 — Q18, final (not written yet)

<!-- What Q18 asks for here (its chapter's TRUST.md step, 15 minutes): the final section for the
     capstone crate bignat and its Dafny mirror. Per language: what is proved (each statement of
     research/q18_statements.*, with the command that re-checks it), what is tested (the
     differential check's sample rows), and what is assumed: the CLI's argument parsing and
     printing outside `verus!` (file:line), the given layers, the solver and its version, the
     course wrappers, and the gate v2 you built (its sha256) with its measured false-positive rate.
     A later section never relaxes this one. -->

## R-v0 — R13 (not written yet)

## R-v1 — R16, final (not written yet)

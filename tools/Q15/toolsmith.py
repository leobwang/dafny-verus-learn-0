"""CONTRACT
goal: build the automation this file's docstring and INTERFACE block specify for the twelve goals of tools/Q15/battery/ (each in its Dafny and its Verus form): a command-line tool that, for one goal file, finds the quantified step of the goal's last declaration, tries trigger choices for it, and writes a repaired copy that the done gate passes, changing triggers only
allowed-files:
  - tools/Q15/toolsmith.py
acceptance:
  - re-run the tool on a goal you changed and `scripts/vcheck --gate` its output after every edit of the tool; never stack unverified edits
  - for every goal file of tools/Q15/battery/battery.toml, the tool's output file passes `scripts/vcheck --gate` and `scripts/specfreeze --against` the shipped goal file reports no change
  - the tool never writes a statement line (signature, requires, ensures, decreases) and never edits a shipped battery file: it writes new files only, under the output directory it is given
  - the tool adds or changes trigger annotations only (Dafny `{:trigger …}`; Verus `#[trigger]`, `#![trigger …]`), and runs the verifier only through `scripts/vcheck`, one job at a time
  - the standard library only
"""
# Q15 — the toolsmith (rung 12; `/contract Q15`; QPLAN §25.3, §25.4)
#
# This file is the contract's only allowed file. It ships with no code: the
# contractor writes all of it, to the interface you write below.
#
# Before the run (you, about 8 minutes):
#   1. Write the INTERFACE block below: the command line (a goal file in, an
#      output directory; or the battery file and a directory), what the tool
#      prints per goal (the trigger it chose, the runs it made and their
#      verdicts), which trigger candidates it tries and in which order (for
#      example, each subterm of the step's body that mentions every bound
#      variable and holds no arithmetic at its top), how many runs it may
#      spend per goal, what it does with a goal that passes as shipped, and
#      its exit codes.
#   2. Commit it, then run `/contract Q15` on this file in a fresh session.
#
# After the run (you, about 12 minutes): review the tool's source (does it
# touch anything but a trigger? does it ever write over a battery file? does
# it judge a run from vcheck's output only?), then audit every one of the
# twelve goals in both languages: run the tool, `scripts/vcheck --gate` its
# output, and `scripts/specfreeze --against` the shipped goal; fill the AUDIT
# block at the end, one row per goal file.

# INTERFACE (learner-owned; written before the run, never by the contractor)
#   command line:
#   output (files, and what is printed):
#   trigger candidates, and their order:
#   runs per goal:
#   a goal that passes as shipped:
#   exit codes:

# AUDIT (learner-owned; after the contract run; one row per goal file)
#   goal file | trigger chosen | gate | specfreeze --against | anything but a trigger changed
#   dafny/G01 |                |      |                      |
#   verus/G01 |                |      |                      |
#   (… G02-G12, both languages)
#   the source review: what it touches, what it writes, how it judges a run:
#   the transcript moments these rest on:

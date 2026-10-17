"""CONTRACT
goal: implement this file to the INTERFACE block below its header: a command-line tool that reads `scripts/vcheck --json` and `scripts/vaudit --json` documents and prints one JSON object per file with its hole count by kind, its assumption findings by kind and its verdict, taken from the documents only
allowed-files:
  - tools/Q12/holecount.py
acceptance:
  - re-run `python3 tools/Q12/test_holecount.py` after every edit; never stack unverified edits
  - `python3 tools/Q12/test_holecount.py` exits 0
  - the tool reads documents only: it runs no verifier or course tool, starts no process, and never opens or scans a source file; every count it prints comes from a document's own fields
  - the standard library only; no file is written
"""
# Q12 — the toolwright (rung 10; `/contract Q12`; QPLAN §22.4)
#
# This file is the contract's only allowed file. It ships with no code: the
# contractor writes all of it, to the interface you write below.
#
# Before the run (you, about 8 minutes):
#   1. Write the INTERFACE block below: the input (one or more documents, as
#      `scripts/vcheck --json` and `scripts/vaudit --json` print them, read
#      from files named on the command line or from standard input; say
#      which), the output (one JSON object per file the documents are about,
#      with the hole count by kind, the assumption findings by kind and the
#      verdict), what it does with a document it cannot read, and its exit
#      codes.
#   2. Write the acceptance tests tools/Q12/test_holecount.py (standard
#      library `unittest`, run as `python3 tools/Q12/test_holecount.py`)
#      over fixtures you copy from earlier modules' recorded documents (for
#      example under harness/tests/q/fixtures/), each with the expected
#      object written out. The tests are yours, outside the contract: the
#      contractor never edits them.
#   3. Commit both, then run `/contract Q12` in a fresh session.
#
# After the run (about 7 minutes): run the tool on two documents the tests do
# not contain; audit its source (does it count from the source text? does it
# read a missing key as zero?); fill the AUDIT block at the end.

# INTERFACE (learner-owned; written before the run, never by the contractor)
#   input:
#   output:
#   unreadable input:
#   exit codes:

# AUDIT (learner-owned; after the contract run)
#   two documents outside the tests, and what the tool printed for each:
#   does it count from anything but a document's fields:
#   what it does with a missing key:
#   the transcript moments these rest on:

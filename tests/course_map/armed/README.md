# Armed-module fixture for scripts/test_course_map.py

A synthetic Q04 used only by the checker's regression suite. `Q04.toml` replaces Q04's
[[module]] table, and `tree/` is copied into each throwaway root. Every file here is a
wiring fixture: the declarations are placeholders that exercise the registry, the item
grammar, the import tiers and the unit generator. None of it is course content, an
exercise or an answer, and nothing here is ever verified.

"""
Tests for authority_splitter — covers splitting, signals, hereinafter, and Compare/with.
Run with: cd backend && python test_authority_splitter.py
"""

import sys
from authority_splitter import split_authorities


def check(condition, msg):
    if condition:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        sys.exit(1)


# ── Single citation ──────────────────────────────────────────────────────────

print("\n── Single citations ──────────────────────────────")

r = split_authorities("Miranda v. Arizona, 384 U.S. 436 (1966)")
check(len(r) == 1, "Single case → 1 authority")
check(r[0] == "Miranda v. Arizona, 384 U.S. 436 (1966)", f"  text='{r[0]}'")

r = split_authorities("42 U.S.C. § 1983 (2018)")
check(len(r) == 1, "Single statute → 1 authority")

r = split_authorities("Id. at 445")
check(len(r) == 1, "Single Id. → 1 authority")
check(r[0] == "Id. at 445", f"  text='{r[0]}'")

# ── Semicolon splitting ─────────────────────────────────────────────────────

print("\n── Semicolon splitting ───────────────────────────")

r = split_authorities(
    "Smith v. Jones, 384 U.S. 436 (1966); Brown v. Board, 347 U.S. 483 (1954)"
)
check(len(r) == 2, f"Two cases → 2 authorities (got {len(r)})")
check("Smith" in r[0], f"  first='{r[0]}'")
check("Brown" in r[1], f"  second='{r[1]}'")

r = split_authorities(
    "42 U.S.C. § 1983; Miranda v. Arizona, 384 U.S. 436 (1966); Id. at 445"
)
check(len(r) == 3, f"Three mixed → 3 authorities (got {len(r)})")

# Semicolons inside parentheses should NOT split
r = split_authorities(
    "Smith v. Jones, 384 U.S. 436 (1966) (citing Brown; also Jones)"
)
check(len(r) == 1, f"Semicolon inside parens → 1 authority (got {len(r)})")

# ── Introductory signals ────────────────────────────────────────────────────

print("\n── Introductory signals ──────────────────────────")

r = split_authorities("See Miranda v. Arizona, 384 U.S. 436 (1966)")
check(len(r) == 1, "'See' → 1 authority")
check("See" not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("See also 42 U.S.C. § 1983 (2018)")
check(len(r) == 1, "'See also' → 1 authority")
check("See also" not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("But see Smith v. Jones, 100 F.3d 200 (2000)")
check(len(r) == 1, "'But see' → 1 authority")
check("But" not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("Cf. Prosser, Handbook of Torts 23 (4th ed. 1971)")
check(len(r) == 1, "'Cf.' → 1 authority")
check("Cf." not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("E.g., Miranda v. Arizona, 384 U.S. 436 (1966)")
check(len(r) == 1, "'E.g.,' → 1 authority")
check("E.g." not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("Accord Brown v. Board, 347 U.S. 483 (1954)")
check(len(r) == 1, "'Accord' → 1 authority")
check("Accord" not in r[0], f"  signal stripped: '{r[0]}'")

r = split_authorities("Contra Smith v. Jones, 100 F.3d 200 (2000)")
check(len(r) == 1, "'Contra' → 1 authority")
check("Contra" not in r[0], f"  signal stripped: '{r[0]}'")

# Signal on each part of a semicolon list
r = split_authorities(
    "See Smith, 384 U.S. 436 (1966); But see Brown, 347 U.S. 483 (1954)"
)
check(len(r) == 2, f"Signal + semicolon → 2 authorities (got {len(r)})")
check("See" not in r[0], f"  first signal stripped: '{r[0]}'")
check("But see" not in r[1], f"  second signal stripped: '{r[1]}'")

# ── Hereinafter stripping ───────────────────────────────────────────────────

print("\n── Hereinafter stripping ─────────────────────────")

r = split_authorities(
    "Miranda v. Arizona, 384 U.S. 436 (1966) [hereinafter Miranda]"
)
check(len(r) == 1, "Hereinafter → 1 authority")
check("hereinafter" not in r[0], f"  stripped: '{r[0]}'")
check("Miranda v. Arizona" in r[0], f"  citation preserved: '{r[0]}'")

r = split_authorities(
    "See Smith, 100 F.3d 200 (2000) [hereinafter Smith]; Brown, 347 U.S. 483 (1954)"
)
check(len(r) == 2, f"Hereinafter + semicolon → 2 authorities (got {len(r)})")
check("hereinafter" not in r[0], f"  first stripped: '{r[0]}'")

# ── Compare / with ──────────────────────────────────────────────────────────

print("\n── Compare / with ────────────────────────────────")

r = split_authorities(
    "Compare Smith v. Jones, 384 U.S. 436 (1966), with Brown v. Board, 347 U.S. 483 (1954)"
)
check(len(r) == 2, f"Compare X, with Y → 2 authorities (got {len(r)})")
check("Smith" in r[0], f"  first='{r[0]}'")
check("Brown" in r[1], f"  second='{r[1]}'")

# Compare with semicolons on both sides
r = split_authorities(
    "Compare Smith, 384 U.S. 436 (1966); Jones, 100 F.3d 200 (2000), "
    "with Brown, 347 U.S. 483 (1954); Lee, 50 U.S.C. 100 (2010)"
)
check(len(r) == 4, f"Compare X; Y, with Z; W → 4 authorities (got {len(r)})")

# ── Edge cases ──────────────────────────────────────────────────────────────

print("\n── Edge cases ────────────────────────────────────")

r = split_authorities("")
check(len(r) == 1, f"Empty string → 1 authority (the original) (got {len(r)})")

r = split_authorities("   ")
check(len(r) == 1, f"Whitespace only → 1 authority (got {len(r)})")

# No splitting needed — single authority with no signals
r = split_authorities("not a citation at all")
check(len(r) == 1, "Non-citation text → 1 authority (passthrough)")
check(r[0] == "not a citation at all", f"  text preserved: '{r[0]}'")

# Trailing period stripping
r = split_authorities("See Smith, 384 U.S. 436 (1966).")
check(len(r) == 1, "Trailing period → 1 authority")

# ── Real-world patterns ─────────────────────────────────────────────────────

print("\n── Real-world patterns ───────────────────────────")

# String cite with signals
r = split_authorities(
    "See Miranda v. Arizona, 384 U.S. 436 (1966); "
    "see also Brown v. Board, 347 U.S. 483 (1954); "
    "but cf. Smith v. Jones, 100 F.3d 200 (2000)"
)
check(len(r) == 3, f"Three-authority string cite → 3 (got {len(r)})")
check("Miranda" in r[0], f"  first='{r[0]}'")
check("Brown" in r[1], f"  second='{r[1]}'")
check("Smith" in r[2], f"  third='{r[2]}'")

# Hereinafter + signal
r = split_authorities(
    "See Restatement (Second) of Contracts § 71 (1981) [hereinafter Restatement]"
)
check(len(r) == 1, "Signal + hereinafter → 1 authority")
check("hereinafter" not in r[0], f"  stripped: '{r[0]}'")
check("See" not in r[0], f"  signal stripped: '{r[0]}'")

print("\nAll authority_splitter tests passed.\n")

"""
Quick smoke tests for citation_parser and bluebook — no network calls needed.
Run with: python test_core.py
"""

import sys
import citation_parser as cp
import bluebook


def check(condition: bool, msg: str):
    if condition:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        sys.exit(1)


# ── Parser tests ──────────────────────────────────────────────────────────────

print("\n── Citation Parser ──────────────────────────────")

r = cp.parse("Miranda v. Arizona, 384 U.S. 436 (1966)")
check(r.citation_type == cp.CitationType.CASE, "CASE: Miranda v. Arizona detected")
check(r.parties == "Miranda v. Arizona", f"CASE: parties='{r.parties}'")
check(r.volume == "384", f"CASE: volume='{r.volume}'")
check(r.reporter == "U.S.", f"CASE: reporter='{r.reporter}'")
check(r.page == "436", f"CASE: page='{r.page}'")
check(r.year == "1966", f"CASE: year='{r.year}'")

r2 = cp.parse("Brown v. Bd. of Educ., 347 U.S. 483, 495 (1954)")
check(r2.citation_type == cp.CitationType.CASE, "CASE: Brown v. Board detected")
check(r2.pincite == "495", f"CASE: pincite='{r2.pincite}'")

r3 = cp.parse("42 U.S.C. § 1983 (2018)")
check(r3.citation_type == cp.CitationType.STATUTE, "STATUTE: 42 U.S.C. § 1983 detected")
check(r3.title == "42", f"STATUTE: title='{r3.title}'")
check(r3.section == "1983", f"STATUTE: section='{r3.section}'")
check(r3.year == "2018", f"STATUTE: year='{r3.year}'")

r4 = cp.parse(
    "Katharine T. Bartlett, Feminist Legal Methods, "
    "103 Harv. L. Rev. 829 (1990)"
)
check(r4.citation_type == cp.CitationType.ARTICLE, "ARTICLE: Bartlett detected")
check("Bartlett" in (r4.authors or ""), f"ARTICLE: authors='{r4.authors}'")
check(r4.volume == "103", f"ARTICLE: volume='{r4.volume}'")
check(r4.page == "829", f"ARTICLE: page='{r4.page}'")

r5 = cp.parse("William L. Prosser, Handbook of the Law of Torts 23 (4th ed. 1971)")
check(r5.citation_type == cp.CitationType.BOOK, "BOOK: Prosser detected")
check("Prosser" in (r5.authors or ""), f"BOOK: authors='{r5.authors}'")
check(r5.year == "1971", f"BOOK: year='{r5.year}'")

r6 = cp.parse("not a citation at all")
check(r6.citation_type == cp.CitationType.UNKNOWN, "UNKNOWN: unrecognised text")

# New types
r7 = cp.parse("Id. at 445")
check(r7.citation_type == cp.CitationType.ID, "ID: 'Id. at 445' detected")
check(r7.bluebook_rule == "Rule 4.1", f"ID: rule='{r7.bluebook_rule}'")

r8 = cp.parse("Id.")
check(r8.citation_type == cp.CitationType.ID, "ID: bare 'Id.' detected")

r9 = cp.parse("Smith, supra note 5, at 42")
check(r9.citation_type == cp.CitationType.SUPRA, "SUPRA: 'Smith, supra note 5' detected")
check(r9.supra_note == "5", f"SUPRA: note='{r9.supra_note}'")
check(r9.bluebook_rule == "Rule 4.2", f"SUPRA: rule='{r9.bluebook_rule}'")

r10 = cp.parse("U.S. Const. amend. XIV, § 1")
check(r10.citation_type == cp.CitationType.CONSTITUTION, "CONST: U.S. Const. amend. XIV detected")
check(r10.bluebook_rule == "Rule 11", f"CONST: rule='{r10.bluebook_rule}'")

r11 = cp.parse("Restatement (Second) of Contracts § 71 (1981)")
check(r11.citation_type == cp.CitationType.RESTATEMENT, "RESTATEMENT: detected")
check(r11.bluebook_rule == "Rule 12.9.4", f"RESTATEMENT: rule='{r11.bluebook_rule}'")

r12 = cp.parse("Model Penal Code § 2.02 (Official Draft 1962)")
check(r12.citation_type == cp.CitationType.RESTATEMENT, "RESTATEMENT: Model Penal Code detected")

r13 = cp.parse("H.R. 1234, 117th Cong. § 2 (2021)")
check(r13.citation_type == cp.CitationType.LEGISLATIVE, "LEGISLATIVE: H.R. bill detected")
check(r13.bluebook_rule == "Rule 13", f"LEGISLATIVE: rule='{r13.bluebook_rule}'")

r14 = cp.parse("S. Rep. No. 103-7, at 10 (1993)")
check(r14.citation_type == cp.CitationType.LEGISLATIVE, "LEGISLATIVE: Senate report detected")

r15 = cp.parse("Miranda, 384 U.S. at 444")
check(r15.citation_type == cp.CitationType.SHORT_CASE, "SHORT_CASE: 'Miranda, 384 U.S. at 444' detected")
check(r15.pincite == "444", f"SHORT_CASE: pincite='{r15.pincite}'")

r16 = cp.parse("In re Blockratize, Inc. d/b/a Polymarket, CFTC Docket No. 22-09 (Jan. 3, 2022)")
check(r16.citation_type == cp.CitationType.ADMINISTRATIVE, "ADMIN: CFTC order detected")
check(r16.bluebook_rule == "Rule 14.3", f"ADMIN: rule='{r16.bluebook_rule}'")
check(r16.year == "2022", f"ADMIN: year='{r16.year}'")

r17 = cp.parse("In re Coinbase, Inc., SEC Release No. 97990 (June 6, 2023)")
check(r17.citation_type == cp.CitationType.ADMINISTRATIVE, "ADMIN: SEC release detected")

r18 = cp.parse("In the Matter of XYZ Corp., FTC Docket No. C-1234 (2020)")
check(r18.citation_type == cp.CitationType.ADMINISTRATIVE, "ADMIN: FTC docket detected")

# ── Bluebook tests ─────────────────────────────────────────────────────────────

print("\n── Bluebook Validator ───────────────────────────")

bb = bluebook.validate_and_format(r)   # Miranda — should be valid
check(bb["is_valid"], f"BB: Miranda valid → '{bb['suggested']}'")

# Force a bad case: no year
bad_case = cp.ParsedCitation(
    raw="test", citation_type=cp.CitationType.CASE,
    parties="Smith v. Jones", volume="100", reporter="F.3d", page="200",
)
bb2 = bluebook.validate_and_format(bad_case)
check(not bb2["is_valid"], "BB: missing year flagged as invalid")
check(any("Year" in i for i in bb2["issues"]), f"BB: year issue listed: {bb2['issues']}")

# Court name in parenthetical check
bad_scotus = cp.ParsedCitation(
    raw="test", citation_type=cp.CitationType.CASE,
    parties="Roe v. Wade", volume="410", reporter="U.S.", page="113",
    court="U.S.", year="1973",
)
bb3 = bluebook.validate_and_format(bad_scotus)
check(not bb3["is_valid"], "BB: spurious court name in SCOTUS cite flagged")

statute_r = bluebook.validate_and_format(r3)
check(statute_r["is_valid"], f"BB: statute valid → '{statute_r['suggested']}'")
check("§" in statute_r["suggested"], "BB: § symbol present")

article_r = bluebook.validate_and_format(r4)
check(article_r["is_valid"], f"BB: article valid → '{article_r['suggested']}'")

print("\nAll tests passed.\n")

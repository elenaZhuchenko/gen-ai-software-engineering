# Skill: Research Quality Measurement

## Purpose

This skill defines a standardised rubric for assessing the quality of a
codebase-research document produced by a Bug Researcher agent.  The Research
Verifier MUST use this rubric when writing `verified-research.md`.

---

## Quality Levels

Apply the **highest** level whose criteria are fully satisfied.

| Level | Label | Criteria |
|-------|-------|----------|
| 4 | **VERIFIED** | All claims checked; all file:line references confirmed accurate; all code snippets match source verbatim; discrepancy rate ≤ 0 %. |
| 3 | **MOSTLY-VERIFIED** | All claims checked; discrepancy rate 1–10 % (minor line-number drift, trimmed snippets that are still materially accurate); no critical claim is wrong. |
| 2 | **PARTIAL** | Claims checked; discrepancy rate 11–30 %; OR at least one claim references a file that does not exist; OR a severity label is materially incorrect (e.g. CRITICAL downgraded to LOW). |
| 1 | **UNVERIFIED** | Discrepancy rate > 30 %; OR the researcher missed a clearly observable bug; OR a critical security finding is absent from the report. |

---

## Definitions

- **Claim**: Any statement in `codebase-research.md` that asserts a specific fact
  (file path, line number, code snippet, severity rating, behaviour description).
- **Discrepancy**: A claim that does not match the actual source file at the time
  of verification.  Minor discrepancies include off-by-one line numbers and
  truncated-but-accurate snippets.  Major discrepancies include wrong file paths,
  wrong function names, or materially incorrect code snippets.
- **Discrepancy rate**: `(number of discrepant claims) / (total verifiable claims) × 100`.

---

## Verification Procedure

The Research Verifier MUST follow these steps in order:

1. **Count total verifiable claims** — every file:line reference and every code snippet counts as one claim.
2. **Open each referenced file** — use the exact path stated in the research doc.
3. **Check line numbers** — navigate to the stated line; confirm the code matches.
4. **Check snippets** — compare the quoted code against the actual source byte-by-byte.  Record any difference.
5. **Tally discrepancies** — compute the discrepancy rate.
6. **Assign quality level** — apply the table above.
7. **Record findings** — include counts and the rate in the `verified-research.md`.

---

## Required Output Sections in `verified-research.md`

The verifier MUST include ALL of the following sections:

```
## Verification Summary
- Overall result: PASS / FAIL
- Total claims verified: N
- Discrepancies found: N  (rate: X %)
- Research Quality: <LEVEL LABEL>   ← from this skill's rubric

## Verified Claims
List of claims confirmed accurate (file, line, claim text).

## Discrepancies Found
List of discrepant claims:  original claim vs. actual source.
If none: write "None".

## Research Quality Assessment
- Quality level: <LEVEL LABEL>
- Reasoning: <explanation of why this level was assigned>
- Can the Bug Planner safely use this research? YES / NO / WITH CAVEATS

## References
- Source files inspected: [list]
- Research document read: context/bugs/001/research/codebase-research.md
```

---

## Guidance for Edge Cases

- If a referenced file does not exist, count that as a **major discrepancy**.
- If the researcher's line number is off by ≤ 2 (because of blank lines or
  comments), count it as a **minor discrepancy** — still log it.
- If the researcher omitted a clearly present bug visible in the source, set
  level to **UNVERIFIED** regardless of other metrics.
- The skill does not penalise the researcher for including *extra* findings
  beyond what the verifier expected — only incorrect or missing claims count
  against quality.

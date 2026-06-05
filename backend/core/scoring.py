"""Clean Record Score — an absolute (non-percentile) 0–100 integrity score
derived from an MP's *convictions* (not pending cases).

Rules:
  Start at 100.
  Major (serious) conviction: -50 for the first 3, -25 from the 4th onwards.
  Minor conviction:           -20 for the first 3, -10 from the 4th onwards.
  Floored at 0.

Counts are diminished per-category (the "first 3" is counted separately for
major and minor). Order does not matter. See tests/examples in the PR.
"""


def compute_clean_record_score(convictions_serious: int = 0, convictions_minor: int = 0) -> int:
    serious = max(int(convictions_serious or 0), 0)
    minor = max(int(convictions_minor or 0), 0)

    score = 100
    for i in range(serious):
        score -= 50 if i < 3 else 25
    for i in range(minor):
        score -= 20 if i < 3 else 10

    return max(score, 0)

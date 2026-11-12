# ADR 0001: Per-Conducted-Unit Denominator Rule

## Status
Accepted

## Context
Conventional university student information systems compute attendance percentages by dividing attended hours by the total scheduled hours on the academic calendar. When faculty cancel a lecture or when unexpected university holidays occur, unconducted hours are frequently coerced into 0 or omitted unpredictably, causing severe statistical distortion in official accreditation reports (NAAC, NBA, UGC, AICTE) and unfairly penalizing students.

## Decision
We enforce a strict mathematical invariant across all layers of K² FRS:
1. Attendance percentage is computed exclusively over the set of verified conducted units $U_c$ ($1 \le |U_c| \le 4$):
```math
\text{Attendance Rate (\%)} = 100 \times \frac{\sum_{u \in U_c} \mathbb{I}(\text{status}(s, u) = \text{PRESENT})}{|U_c|}
```
2. If $|U_c| = 0$ (no instructional units conducted), the attendance percentage strictly evaluates to **`N/A`** (`null` in JSON).
3. The system rejects any coercion of unconducted units to 0% or 100%.

## Consequences
### Positive
* True reflection of classroom attendance independent of cancellations or scheduling anomalies.
* Accreditation audit-proof calculations.
* Deterministic behavior across mobile client, API, and analytical dashboards.

### Negative
* UI must explicitly accommodate `N/A` rendering alongside numerical percentages.


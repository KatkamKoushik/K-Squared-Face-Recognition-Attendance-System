# ADR 0002: Immutable Roster Snapshot on Session Initialization

## Status
Accepted

## Context
In higher education environments, student enrolment changes (course adds/drops, cohort transfers, administrative suspensions) occur dynamically throughout the semester. If a session dynamically queries the live student table during review or commit, a student who dropped a course mid-session could alter the session's denominator retroactively, creating auditing inconsistencies.

## Decision
1. When a session transitions from `DRAFT` to `ROSTER_FROZEN`, the control plane takes an immutable point-in-time snapshot of all enrolled students actively registered in the subject offering or merged class group.
2. In the case of an authorized joint-class group (e.g. combined lecture across Sections A and B), the frozen roster is the deterministic union of eligible students across the member cohorts with deduplication on student roll number.
3. Mid-session database mutations, additions, or dropouts do not alter the session's frozen denominator.

## Consequences
### Positive
* Perfect repeatability and mathematical determinism for every session.
* Single-denominator fairness guaranteed for multi-section elective unions.
* Clear isolation between administrative registry changes and active classroom sessions.

### Negative
* If a newly enrolled student was added minutes before class, the faculty member must either restart the session or use manual attendance reconciliation.


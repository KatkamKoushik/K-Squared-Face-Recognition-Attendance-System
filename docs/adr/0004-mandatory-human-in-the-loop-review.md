# ADR 0004: Mandatory Human-in-the-Loop Faculty Review

## Status
Accepted

## Context
Computer vision algorithms are probabilistic and subject to physical constraints (extreme head poses, partial occlusions, motion blur, suboptimal ambient lighting). Autonomous biometric systems that automatically mark students absent when unrecogized create unacceptable false-negative penalties and violate university academic regulations, which require faculty authorization for official attendance records.

## Decision
1. Machine learning pipeline predictions are classified strictly as non-binding **Candidate Proposals**.
2. Sightings with cosine similarity $s < 0.45$ are classified as `UNKNOWN` (unassigned classroom attendee, e.g. guest auditor) and are never mapped to absent enrolled students.
3. Sightings with ambiguous lookalike margins ($\Delta s < 0.15$) are routed to an explicit faculty `REVIEW` triage state.
4. Attendance ledger entries cannot be committed without explicit review and confirmation by the assigned faculty instructor.
5. In the event of photo capture failure or students without biometric consent, faculty can switch to the Manual Attendance Roll-Call screen (`manual_attendance_screen.dart`).

## Consequences
### Positive
* Zero autonomous unverified student absences.
* Full alignment with legal liability and accreditation requirements placing attendance authority on faculty.
* Explicit handling of uncertainty, blur, and lighting edge cases.

### Negative
* Requires faculty interaction to finalize session proposals before official persistence.


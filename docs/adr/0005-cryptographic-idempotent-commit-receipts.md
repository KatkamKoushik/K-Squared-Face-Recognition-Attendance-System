# ADR 0005: Cryptographic Idempotent Commit Receipts

## Status
Accepted

## Context
Mobile clients operating in university classroom environments encounter intermittent Wi-Fi or cellular connectivity. A network drop during attendance finalization could prompt the instructor to press "Confirm Commit" repeatedly. Without robust idempotency and transactional integrity, duplicate ledger rows could be inserted, double-crediting conducted units or distorting analytical aggregations.

## Decision
1. Attendance finalization (`POST /api/v1/sessions/{session_id}/commit`) executes inside an atomic ACID database transaction.
2. Every commit request must provide a client-generated UUID `idempotency_key`.
3. If a request arrives with an existing `idempotency_key` for the session:
   * The database transaction returns the previously generated receipt immediately.
   * No additional attendance rows or audit events are written.
4. Each successful commit generates an immutable `CommitReceipt` with a deterministic SHA-256 hash:
```math
H_{\text{receipt}} = \text{SHA-256}(\text{id}_{\text{session}} \parallel \text{id}_{\text{faculty}} \parallel t_{\text{commit}} \parallel N_{\text{present}} \parallel N_{\text{absent}})
```
5. The session state transitions permanently to `FINALIZED`, preventing any subsequent mutations.

## Consequences
### Positive
* 100% protection against duplicate submissions and network replay storms.
* Immutable, cryptographically verifiable proof of attendance recording.
* Complete transactional integrity across multi-unit sessions ($1 \le \text{units} \le 4$).

### Negative
* Clients must generate and persist UUID idempotency keys across retry attempts.


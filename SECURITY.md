# Security & Vulnerability Reporting Policy

The **FRS V7.1 K²** engineering team takes the security of university systems, student records, and biometric data with the utmost seriousness.

---

## Supported Versions

Security updates and patches are actively applied to the following release lines:

| Version | Supported | Status |
| :--- | :--- | :--- |
| **7.1.x (Canonical Baseline)** | Yes | Active Primary Support |
| < 7.1.0 | No | End of Life / Superseded |

---

## Reporting a Security Vulnerability

If you discover a security vulnerability or potential privacy leak (particularly concerning biometric data exposure, presentation attacks, or unauthorized attendance ledger manipulation), please report it responsibly:

> **DO NOT file a public GitHub issue.**

Please report vulnerabilities via confidential communication to:
* **Primary Contact:** `security-frs@kucet.ac.in`
* **Subject Line:** `[SECURITY] FRS V7.1 Potential Vulnerability - <Brief Description>`

### Please Include:
1. Description of the vulnerability and attack vector.
2. Steps to reproduce or proof-of-concept script.
3. Affected components (`teacher_mobile`, `admin_console`, `backend`, or `worker`).
4. Potential impact on student records or biometric privacy.

---

## Response Timeline

* **Initial Acknowledgment:** Within 48 hours of receipt.
* **Triage & Severity Assessment:** Within 5 business days.
* **Remediation & Patch Deployment:** Critical vulnerabilities will be addressed via hotfix within 14 days prior to public disclosure.

---

## Biometric Privacy & Invariant Protections

Security audits should verify that the system strictly adheres to our privacy invariants:
* Irreversible 512-dimensional vector representations.
* Ephemeral photo frame purging following session finalization.
* Complete biometric redaction across administrative views and audit trails.
* Enforced role-based access control preventing non-faculty accounts from signing attendance receipts.


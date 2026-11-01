# FRS V7.1 K² — Admin Web Console

Institutional academic administration and attendance governance portal built on **Next.js 15.5**, **React 19**, and **Tailwind CSS**.

---

## Architectural Capabilities

* **Swiss Modernism UI:** Clean, content-focused typographic design without unnecessary gradients or non-standard UI paradigms.
* **Role-Gated Navigation:** Specialized views for Academic Deans, Department Heads, and System Administrators.
* **Audit Trail Browser:** Inspects immutable ledger events with biometric crops and embedding vectors redacted for student privacy.
* **Denominator Invariant:** Attendance percentages enforce the strict $\text{attended} / \text{conducted}$ ratio, rendering `N/A` when zero units have been conducted.
* **Incremental Static Regeneration (ISR):** Standalone pages revalidate with the FastAPI control plane on a 10-second cache window.

---

## Local Development

```bash
# Install dependencies
npm ci

# Typecheck TypeScript source
npm run typecheck

# Run Next.js local development server (http://localhost:3000)
npm run dev

# Compile standalone production build
npm run build
```


Production-Level Website & Application Engineering Checklist
A comprehensive, technology-neutral checklist for planning, building, launching, operating, and evolving production websites, web apps, APIs, mobile apps, SaaS products, and connected systems.

How to use this checklist
- Mark an item complete only when it has been implemented, reviewed, and verified where appropriate.
- Core means every production project should evaluate the concern; it does not mean every technology or control is mandatory.
- Conditional means apply it when the product, business model, users, data, or architecture require it.
- Advanced means it is generally relevant to large-scale, highly regulated, distributed, or otherwise complex systems.
- Record N/A with a short rationale rather than silently skipping relevant-looking items.
- Security, privacy, accessibility, reliability, and cost are lifecycle concerns—not final polish tasks.
Suggested status convention: [ ] Not started · [x] Verified · [~] In progress · [N/A] Not applicable

Table of Contents
1. Product strategy and requirements
2. Product design, UX research, and design systems
3. Domain modeling and business logic
4. Architecture and technical design
5. Frontend engineering
6. Backend engineering
7. API design and communication protocols
8. Database and persistence
9. Identity and authentication
10. Authorization and access control
11. Application, network, and platform security
12. Files, media, and object storage
13. Caching and data delivery
14. Background jobs and asynchronous processing
15. External services and integrations
16. Payments and financial workflows
17. E-commerce, inventory, orders, and fulfillment
18. Search, discovery, and recommendations
19. Notifications and communication
20. Real-time and collaborative features
21. Testing and quality assurance
22. Code quality and maintainability
23. Version control and team collaboration
24. Developer experience and local environments
25. Build systems, release engineering, and CI/CD
26. Hosting, infrastructure, networking, and DNS
27. Containers and orchestration
28. Serverless and edge computing
29. Configuration and secrets management
30. Performance engineering
31. Scalability and capacity planning
32. Reliability and fault tolerance
33. Observability: logs, metrics, traces, and alerts
34. Backup, recovery, and disaster readiness
35. Incident management and production operations
36. Data management, privacy, and governance
37. Data engineering, warehousing, and BI
38. Accessibility and inclusive design
39. Internationalization and localization
40. SEO and web discoverability
41. Product analytics and measurement
42. Growth, onboarding, and lifecycle marketing
43. Feature flags, experimentation, and progressive delivery
44. Admin tools and business operations
45. Multi-tenancy and organization boundaries
46. SaaS plans, subscriptions, and entitlements
47. Content management and moderation
48. Legal, regulatory, and contractual compliance
49. AI and machine-learning features
50. Security operations and software supply-chain security
51. Cost management and FinOps
52. Documentation and knowledge management
53. Customer support and service operations
54. Maintenance, upgrades, and technical debt
55. Mobile-specific engineering
56. Progressive web apps and advanced web platform
57. Hardware, IoT, and companion-device integrations
58. Advanced distributed systems
59. Operational governance and engineering management
60. Decommissioning and end-of-life
61. Cross-cutting production principles
62. Go-live readiness gate
1. Product strategy and requirements
Tier: Core
- [ ] Define the target users, their needs, and the problem being solved.
- [ ] Define product goals, business outcomes, and measurable success criteria.
- [ ] Identify primary user journeys, secondary journeys, and critical tasks.
- [ ] Document functional requirements and explicit non-goals.
- [ ] Document non-functional requirements: performance, availability, security, privacy, accessibility, scale, and cost.
- [ ] Define supported platforms, browsers, devices, locales, and network conditions.
- [ ] Identify business rules, constraints, dependencies, and assumptions.
- [ ] Prioritize features by user value, risk, effort, and business impact.
- [ ] Define MVP scope versus future capabilities.
- [ ] Identify stakeholders, decision-makers, owners, and approval paths.
- [ ] Create acceptance criteria and a definition of done.
- [ ] Identify critical failure modes and what users must be able to recover from.
- [ ] Map sensitive data, regulated workflows, and third-party dependencies early.
- [ ] Establish a process for requirement changes and scope control.
- [ ] Validate assumptions through interviews, prototypes, experiments, or usage evidence.
- [ ] Define launch criteria, rollback criteria, and post-launch success measures.
2. Product design, UX research, and design systems
Tier: Core
- [ ] Conduct user research appropriate to the product and risk.
- [ ] Map journeys, tasks, pain points, empty states, and edge cases.
- [ ] Create information architecture, navigation, and content hierarchy.
- [ ] Prototype and validate high-risk or high-frequency workflows before implementation.
- [ ] Define reusable design tokens for color, type, spacing, borders, elevation, and motion.
- [ ] Establish component patterns, variants, states, and usage guidance.
- [ ] Design loading, empty, success, error, offline, permission-denied, and destructive-action states.
- [ ] Define responsive behavior across small, medium, and large viewports.
- [ ] Specify interaction, keyboard, focus, hover, active, disabled, and validation states.
- [ ] Define content style, terminology, tone, and error-message guidance.
- [ ] Keep design and implementation systems synchronized.
- [ ] Validate usability with keyboard, touch, zoom, assistive technology, and real content.
- [ ] Plan for long text, translated strings, user-generated content, and unusual data.
- [ ] Review designs for cognitive load, clarity, consistency, and reduced-motion needs.
- [ ] Include design review and usability feedback in the release process.
3. Domain modeling and business logic
Tier: Core
- [ ] Identify core domain entities, value objects, relationships, and invariants.
- [ ] Define lifecycle states and allowed state transitions.
- [ ] Document business rules in a testable, maintainable form.
- [ ] Distinguish domain logic from transport, UI, persistence, and vendor-specific code.
- [ ] Define ownership and authority for each piece of data.
- [ ] Specify uniqueness, idempotency, ordering, and consistency requirements.
- [ ] Model money, quantities, units, time, dates, time zones, and rounding explicitly.
- [ ] Define handling for retries, duplicate events, partial completion, and compensation.
- [ ] Identify irreversible actions and require suitable confirmation or safeguards.
- [ ] Validate inputs at trust boundaries; never rely solely on client-side validation.
- [ ] Define behavior for missing, stale, contradictory, or invalid domain data.
- [ ] Write tests for invariants, boundary cases, and important business rules.
- [ ] Use domain events where they clarify meaningful state changes.
- [ ] Document business decisions that may otherwise be rediscovered through code.
4. Architecture and technical design
Tier: Core
- [ ] Choose architecture appropriate to current needs and expected growth.
- [ ] Prefer the simplest architecture that satisfies documented requirements.
- [ ] Define module, service, package, and deployment boundaries.
- [ ] Establish dependency direction and enforce boundaries where useful.
- [ ] Define contracts between frontend, backend, data stores, workers, and external systems.
- [ ] Identify synchronous versus asynchronous workflows.
- [ ] Map data flows, trust boundaries, failure modes, and sensitive-data paths.
- [ ] Decide where transactions and consistency guarantees are required.
- [ ] Record important architectural decisions and trade-offs.
- [ ] Avoid premature microservices, distributed complexity, and unnecessary abstractions.
- [ ] Identify single points of failure and critical shared dependencies.
- [ ] Plan migrations from the current architecture to plausible future states.
- [ ] Define service ownership and operational responsibility.
- [ ] Review architecture for security, cost, operability, performance, and developer productivity.
- [ ] Revisit decisions when assumptions or scale change.
5. Frontend engineering
Tier: Core for web products; otherwise N/A
- [ ] Define routing, page composition, and navigation behavior.
- [ ] Establish component boundaries and state-management conventions.
- [ ] Separate server state, local UI state, URL state, and persistent client state.
- [ ] Handle forms, validation, dirty state, submission, retries, and duplicate clicks.
- [ ] Implement loading, empty, error, success, offline, and permission states.
- [ ] Prevent stale requests and race conditions from corrupting the UI.
- [ ] Handle cancellation, navigation during requests, and component lifecycle correctly.
- [ ] Use semantic HTML and native platform behavior where possible.
- [ ] Implement keyboard navigation and visible focus.
- [ ] Support responsive layouts, touch targets, zoom, and reflow.
- [ ] Use CSS logical properties such as margin-inline and padding-inline for writing-direction-aware layouts.
- [ ] Support right-to-left (RTL) layouts where relevant; test mixed-direction text.
- [ ] Avoid unsafe HTML injection; sanitize untrusted rich content.
- [ ] Handle browser storage failures, quota limits, and unavailable APIs.
- [ ] Avoid putting secrets or authoritative business rules in client code.
- [ ] Control bundle size, code splitting, lazy loading, and dependency weight.
- [ ] Remove dead code, debug output, and development-only behavior from production builds.
- [ ] Avoid layout shifts and unnecessary re-renders.
- [ ] Test supported browsers, viewport sizes, and assistive technologies.
- [ ] Define error boundaries or equivalent recovery for rendering failures.
- [ ] Treat third-party scripts as performance, privacy, and security dependencies.
- [ ] Ensure analytics and advertising scripts do not block critical interactions.
- [ ] Use source maps and error reporting safely without exposing sensitive source details publicly.
6. Backend engineering
Tier: Core for server-backed products
- [ ] Define clear module and service responsibilities.
- [ ] Validate inputs, types, size limits, formats, and business constraints.
- [ ] Apply authorization checks on every protected operation.
- [ ] Keep business logic independent from HTTP handlers and framework glue.
- [ ] Use transactions where multi-step state changes must be atomic.
- [ ] Design retryable operations to be idempotent where appropriate.
- [ ] Apply request timeouts, cancellation, and bounded resource usage.
- [ ] Set safe limits for payload size, pagination, query complexity, and execution time.
- [ ] Handle errors consistently without leaking stack traces or secrets.
- [ ] Use structured error types and stable client-facing error codes.
- [ ] Avoid blocking event loops or request threads with long-running work.
- [ ] Move slow or retryable work to queues when appropriate.
- [ ] Implement graceful shutdown and stop accepting work before termination.
- [ ] Apply connection pooling and bounded concurrency.
- [ ] Separate liveness checks from readiness checks.
- [ ] Ensure health checks do not trigger expensive or destructive operations.
- [ ] Make application behavior deterministic enough to test.
- [ ] Enforce resource and tenant quotas where applicable.
7. API design and communication protocols
Tier: Core when APIs or service communication exist
- [ ] Define resource names, HTTP methods, status codes, and error formats consistently.
- [ ] Choose REST, GraphQL, RPC, events, or other protocols based on actual needs.
- [ ] Define request and response schemas and validate them.
- [ ] Publish an API contract or machine-readable specification where useful.
- [ ] Define authentication, authorization, scopes, and service identity.
- [ ] Implement pagination, filtering, sorting, and bounded query complexity.
- [ ] Define rate limits, quotas, burst behavior, and retry guidance.
- [ ] Use idempotency keys for operations that may be retried and create side effects.
- [ ] Plan API versioning, compatibility, deprecation, and removal.
- [ ] Set request, response, connection, and idle timeouts.
- [ ] Define correlation IDs and trace propagation.
- [ ] Support conditional requests, caching headers, and compression where appropriate.
- [ ] Prevent mass assignment and excessive data exposure.
- [ ] Keep error messages useful but free of secrets and internal details.
- [ ] Verify webhook signatures and protect against replay.
- [ ] Document webhook event schemas, retries, ordering, and delivery guarantees.
- [ ] Use gRPC/Protocol Buffers when typed high-performance service RPC is justified.
- [ ] Consider an API gateway for centralized routing, policy, quotas, and observability when warranted.
- [ ] Consider a backend-for-frontend (BFF) when clients have materially different needs.
- [ ] Define streaming semantics, backpressure, reconnect behavior, and partial failure handling.
- [ ] Restrict CORS to required origins and methods; do not treat CORS as authorization.
- [ ] Test contracts and backward compatibility between producers and consumers.
8. Database and persistence
Tier: Core when persistent data exists
- [ ] Choose storage based on query patterns, integrity, consistency, and operational needs.
- [ ] Define schemas, constraints, indexes, foreign keys, and uniqueness rules.
- [ ] Use migrations that are reviewed, versioned, repeatable where feasible, and tested.
- [ ] Prefer backward-compatible expand/migrate/contract migrations for zero-downtime changes.
- [ ] Define transaction boundaries and isolation requirements.
- [ ] Avoid N+1 queries and unbounded table scans.
- [ ] Inspect query plans and measure slow queries.
- [ ] Configure connection pools and connection limits.
- [ ] Define pagination strategy and stable ordering.
- [ ] Use optimistic or pessimistic concurrency controls where needed.
- [ ] Define data retention, archival, deletion, and anonymization behavior.
- [ ] Store timestamps consistently and make timezone interpretation explicit.
- [ ] Define backup coverage, restore procedures, and recovery objectives.
- [ ] Encrypt data in transit and at rest according to risk.
- [ ] Restrict database network access and privileges.
- [ ] Avoid using production personal data in development or test environments without safeguards.
- [ ] Test migrations and restoration with realistic data volumes.
- [ ] Define replication, read replicas, partitioning, or sharding only when justified.
- [ ] Monitor storage growth, connections, locks, deadlocks, replication lag, and saturation.
- [ ] Validate consistency across replicas, caches, search indexes, and derived stores.
- [ ] Define safe operational procedures for destructive queries and data repair.
9. Identity and authentication
Tier: Core for accounts or protected access
- [ ] Choose a trusted identity approach appropriate to the product.
- [ ] Store passwords only with an appropriate modern password-hashing algorithm and configuration.
- [ ] Support secure password reset and account recovery without revealing account existence.
- [ ] Verify email addresses or phone numbers when needed.
- [ ] Use secure, unpredictable session identifiers.
- [ ] Set cookies with appropriate Secure, HttpOnly, and SameSite attributes.
- [ ] Rotate or invalidate sessions after login, privilege changes, and sensitive events.
- [ ] Protect against brute force, credential stuffing, and automated abuse.
- [ ] Offer multi-factor authentication for elevated-risk accounts or actions.
- [ ] Use OAuth/OIDC correctly for federated identity; validate issuer, audience, state, nonce, and redirect URI.
- [ ] Avoid storing long-lived bearer tokens in unsafe browser storage.
- [ ] Implement logout, session revocation, and device/session management as needed.
- [ ] Define account deletion, suspension, recovery, and identity-change workflows.
- [ ] Avoid security questions and predictable recovery secrets.
- [ ] Log security-relevant events without logging credentials, tokens, or recovery codes.
- [ ] Test authentication flows for enumeration, fixation, replay, and privilege escalation.
10. Authorization and access control
Tier: Core for protected resources
- [ ] Define roles, permissions, ownership, and resource-level access rules.
- [ ] Enforce authorization on the server or trusted service boundary.
- [ ] Deny access by default.
- [ ] Check object-level permissions to prevent IDOR/BOLA vulnerabilities.
- [ ] Check function-level permissions for privileged operations.
- [ ] Separate authentication (who you are) from authorization (what you can do).
- [ ] Use least privilege for users, services, jobs, and infrastructure.
- [ ] Define admin, support, impersonation, and emergency-access permissions.
- [ ] Require re-authentication or step-up verification for high-risk actions where appropriate.
- [ ] Ensure tenant boundaries apply to every read, write, export, search, and background job.
- [ ] Test horizontal and vertical privilege escalation scenarios.
- [ ] Review permission changes and privileged access periodically.
- [ ] Record security-sensitive administrative actions in an audit trail.
11. Application, network, and platform security
Tier: Core
- [ ] Maintain a threat model for critical assets, actors, trust boundaries, and abuse cases.
- [ ] Use HTTPS/TLS for public and internal communication where appropriate.
- [ ] Enforce safe security headers, including CSP and clickjacking protections.
- [ ] Protect against injection, XSS, CSRF, SSRF, path traversal, request smuggling, and unsafe deserialization.
- [ ] Use parameterized database queries and context-aware output encoding.
- [ ] Apply CSRF protection to cookie-authenticated state-changing requests.
- [ ] Validate redirect targets and prevent open redirects.
- [ ] Restrict outbound network access for components that process untrusted input.
- [ ] Validate uploaded file type, size, content, and storage location.
- [ ] Scan or quarantine risky uploads when appropriate.
- [ ] Apply rate limits and abuse controls to expensive or sensitive operations.
- [ ] Defend against brute force, scraping, credential stuffing, spam, and automated abuse.
- [ ] Use WAF/CDN protections where useful; understand their limits.
- [ ] Add bot mitigation, challenge flows, and reputation controls when risk warrants it.
- [ ] Prevent secrets and sensitive data from entering logs, URLs, analytics, or error messages.
- [ ] Establish security review for sensitive architectural or feature changes.
- [ ] Perform dependency, static, dynamic, and infrastructure security checks proportionate to risk.
- [ ] Conduct penetration testing or independent security assessment where justified.
- [ ] Define vulnerability intake, triage, remediation SLAs, and disclosure handling.
- [ ] Maintain a security contact and incident escalation route.
- [ ] Use secure defaults and fail closed for security-critical failures.
- [ ] Test security controls continuously rather than relying only on launch review.
12. Files, media, and object storage
Tier: Conditional
- [ ] Define allowed file types, sizes, dimensions, and upload counts.
- [ ] Validate file signatures and inspect actual content; do not trust filenames or MIME headers alone.
- [ ] Use randomized storage keys and keep original filenames as metadata when needed.
- [ ] Store files outside executable application paths.
- [ ] Use private-by-default storage and scoped, short-lived signed URLs where appropriate.
- [ ] Scan, quarantine, transcode, or sanitize files according to threat model.
- [ ] Strip sensitive metadata such as EXIF GPS where appropriate.
- [ ] Generate thumbnails and previews asynchronously.
- [ ] Define lifecycle, retention, archival, and deletion policies.
- [ ] Protect against decompression bombs and oversized image/document processing.
- [ ] Ensure file access follows resource and tenant permissions.
- [ ] Configure CDN caching and invalidation safely.
- [ ] Test interrupted uploads, duplicate uploads, retries, and partial failures.
- [ ] Track storage usage and egress costs.
13. Caching and data delivery
Tier: Core concern; specific cache layers are conditional
- [ ] Identify what can be cached, where, and for how long.
- [ ] Define freshness, invalidation, and consistency expectations.
- [ ] Use appropriate browser, CDN, reverse-proxy, application, and database caches.
- [ ] Set Cache-Control, ETag, and conditional request behavior intentionally.
- [ ] Prevent private or tenant-specific responses from leaking through shared caches.
- [ ] Design cache keys to include relevant identity, locale, query, and version dimensions.
- [ ] Handle cache stampedes, thundering herds, and cold starts.
- [ ] Use stale-while-revalidate or stale-if-error only where product semantics allow it.
- [ ] Define behavior when the cache is unavailable.
- [ ] Avoid treating cache contents as the only durable source of truth.
- [ ] Monitor hit rates, evictions, latency, memory use, and invalidation failures.
14. Background jobs and asynchronous processing
Tier: Conditional
- [ ] Identify work that should not block user-facing requests.
- [ ] Define queue semantics, delivery guarantees, and ordering needs.
- [ ] Make job handlers idempotent or deduplicate repeated deliveries.
- [ ] Configure bounded retries with backoff and jitter.
- [ ] Define dead-letter handling, replay, and manual recovery.
- [ ] Set timeouts, concurrency limits, payload limits, and resource quotas.
- [ ] Track job status, progress, attempts, latency, and terminal failures.
- [ ] Define cancellation and user-visible status for long-running work.
- [ ] Handle poison messages and schema changes safely.
- [ ] Ensure jobs respect current authorization, tenant boundaries, and data retention rules.
- [ ] Use transactional outbox or equivalent patterns when database changes and event publication must stay consistent.
- [ ] Prevent duplicate side effects during retries.
- [ ] Ensure workers handle graceful shutdown and visibility/lease timeouts correctly.
- [ ] Define scheduled job timezone, daylight-saving, overlap, and missed-run behavior.
15. External services and integrations
Tier: Conditional
- [ ] Inventory third-party dependencies, owners, data shared, and business criticality.
- [ ] Review provider security, privacy, reliability, pricing, and contractual terms.
- [ ] Store credentials securely and scope them to minimum permissions.
- [ ] Set connect, read, and total timeouts.
- [ ] Retry only safe operations; use backoff, jitter, and retry budgets.
- [ ] Use circuit breakers, bulkheads, or fallbacks where justified.
- [ ] Validate third-party response schemas and handle provider changes.
- [ ] Verify webhook signatures, timestamps, replay protection, and event IDs.
- [ ] Handle duplicate, delayed, missing, and out-of-order webhooks.
- [ ] Track provider quotas, rate limits, latency, failures, and costs.
- [ ] Provide sandbox/test modes and test fixtures.
- [ ] Define reconciliation for critical integrations.
- [ ] Have a degradation or manual process for provider outages.
- [ ] Avoid tight coupling to a vendor when switching costs are material.
- [ ] Document data residency and subprocessors where relevant.
16. Payments and financial workflows
Tier: Conditional
- [ ] Use a reputable payment processor; avoid handling raw card data unless specifically qualified and necessary.
- [ ] Keep payment secrets and privileged keys server-side.
- [ ] Verify payment-provider webhook signatures.
- [ ] Model payment intent, authorization, capture, settlement, refund, dispute, and failure states.
- [ ] Make checkout and payment operations idempotent.
- [ ] Never trust client-reported payment success as authoritative.
- [ ] Reconcile internal records with provider records.
- [ ] Handle partial payments, refunds, chargebacks, and asynchronous settlement.
- [ ] Store amounts in integer minor units or a rigorously defined money type.
- [ ] Define currency, rounding, tax, fee, and exchange-rate behavior.
- [ ] Prevent duplicate charges and duplicate refunds.
- [ ] Keep an auditable financial ledger or transaction history appropriate to the product.
- [ ] Separate payment status from order fulfillment status.
- [ ] Test declined, pending, timed-out, duplicated, reversed, and disputed payments.
- [ ] Meet applicable payment security and consumer-protection requirements.
- [ ] Define refund approvals, reconciliation exceptions, and finance access controls.
17. E-commerce, inventory, orders, and fulfillment
Tier: Conditional
- [ ] Model products, variants, SKUs, bundles, categories, attributes, and product status.
- [ ] Model prices, promotions, coupons, tax, shipping, and currency explicitly.
- [ ] Define cart persistence, expiration, merging, and pricing refresh rules.
- [ ] Revalidate stock, price, eligibility, and shipping constraints at checkout.
- [ ] Define inventory reservation, release, adjustment, and reconciliation behavior.
- [ ] Prevent overselling under concurrent purchases.
- [ ] Define inventory source of truth and synchronization with warehouses or external systems.
- [ ] Model order lifecycle states and allowed transitions.
- [ ] Separate order, payment, shipment, refund, return, and cancellation state machines.
- [ ] Ensure order creation and payment events are idempotent.
- [ ] Handle partial fulfillment, split shipments, backorders, preorders, and substitutions if needed.
- [ ] Track shipment creation, carrier updates, delivery failures, and lost packages.
- [ ] Support cancellations, returns, exchanges, refunds, and restocking rules.
- [ ] Keep an immutable or auditable order history for support and financial reconciliation.
- [ ] Define address validation, shipping zones, delivery estimates, and restricted items.
- [ ] Handle price changes between cart, checkout, and payment confirmation.
- [ ] Test concurrency, duplicate webhooks, payment timeout, stock depletion, and partial failures.
- [ ] Provide operational tooling for order search, fulfillment exceptions, and inventory corrections.
- [ ] Define fraud review and high-risk transaction handling where relevant.
18. Search, discovery, and recommendations
Tier: Conditional
- [ ] Define search requirements, ranking goals, filters, facets, and sort order.
- [ ] Choose database search or a dedicated search engine based on scale and relevance needs.
- [ ] Keep indexes synchronized with authoritative data.
- [ ] Define indexing, reindexing, backfill, deletion, and recovery procedures.
- [ ] Handle typo tolerance, synonyms, stemming, and locale-specific behavior where useful.
- [ ] Protect search from expensive or abusive queries.
- [ ] Apply permissions and tenant filters to search results.
- [ ] Provide useful empty, partial, and no-result experiences.
- [ ] Measure search quality, latency, zero-result rate, and conversion where relevant.
- [ ] Make recommendation behavior explainable and safe enough for the product context.
- [ ] Avoid leaking deleted or unauthorized content through stale indexes.
19. Notifications and communication
Tier: Conditional
- [ ] Define notification types, priorities, channels, and user preferences.
- [ ] Separate transactional messages from marketing communications.
- [ ] Prevent duplicate, contradictory, or out-of-order notifications where it matters.
- [ ] Use templates with localization, escaping, and preview/testing support.
- [ ] Track delivery, bounce, complaint, suppression, and engagement where appropriate.
- [ ] Respect opt-outs, consent, quiet hours, and channel-specific legal rules.
- [ ] Configure SPF, DKIM, and DMARC for sending domains.
- [ ] Protect sender reputation and manage bounce/complaint lists.
- [ ] Use a reputable email delivery provider and monitor deliverability.
- [ ] Handle push-token expiry, device changes, and invalid destinations.
- [ ] Avoid sensitive information in subject lines, lock-screen notifications, and analytics.
- [ ] Support retry, deduplication, rate limiting, and provider outage behavior.
- [ ] Make notification preferences understandable and accessible.
- [ ] Ensure account, security, and billing messages follow required delivery policies.
20. Real-time and collaborative features
Tier: Conditional
- [ ] Choose WebSockets, Server-Sent Events, polling, or a managed service based on requirements.
- [ ] Define authentication, authorization, and tenant checks for persistent connections.
- [ ] Handle reconnects, heartbeats, stale connections, and backpressure.
- [ ] Define event ordering, duplication, replay, and missed-event recovery.
- [ ] Use sequence numbers, cursors, or snapshots when clients need gap detection.
- [ ] Define presence and typing indicators as best-effort unless stronger guarantees are needed.
- [ ] Resolve concurrent edits and conflicts using explicit rules.
- [ ] Use CRDTs or operational transformation only when collaborative semantics warrant the complexity.
- [ ] Bound connection counts, message sizes, and per-client rates.
- [ ] Monitor connection churn, fan-out, queue lag, and message delivery.
- [ ] Test reconnect storms, network changes, and partial regional outages.
21. Testing and quality assurance
Tier: Core
- [ ] Define a test strategy based on risk and system boundaries.
- [ ] Unit-test business rules and important edge cases.
- [ ] Integration-test databases, queues, caches, and external-service adapters.
- [ ] End-to-end test critical user journeys.
- [ ] Contract-test APIs, events, webhooks, and service boundaries.
- [ ] Test authorization for every meaningful role and resource boundary.
- [ ] Test validation, errors, timeouts, retries, cancellation, and partial failure.
- [ ] Test migrations against realistic schemas and data volumes.
- [ ] Use deterministic fixtures and isolate tests from shared mutable state.
- [ ] Avoid relying only on mocks for behavior that depends on real infrastructure.
- [ ] Test supported browsers, devices, viewports, and assistive technologies.
- [ ] Add visual regression tests for high-value screens where useful.
- [ ] Run accessibility checks and manual assistive-technology testing.
- [ ] Perform load, stress, soak, and spike tests where relevant.
- [ ] Test recovery from dependency outage, queue backlog, and database saturation.
- [ ] Use fuzz testing for parsers, input boundaries, and complex protocol handlers where useful.
- [ ] Use mutation testing selectively to assess whether important tests catch faults.
- [ ] Test security controls and common vulnerability classes.
- [ ] Test backup restoration and disaster-recovery procedures.
- [ ] Use shadow traffic or production-like replay for risky changes when justified.
- [ ] Ensure test failures are actionable and flaky tests are tracked.
- [ ] Define quality gates without making delivery depend on meaningless coverage targets.
- [ ] Test feature flags in both enabled and disabled states.
- [ ] Include regression tests for production incidents and customer-reported bugs.
22. Code quality and maintainability
Tier: Core
- [ ] Define language, formatting, linting, and static-analysis conventions.
- [ ] Use types and schemas to make invalid states harder to represent.
- [ ] Keep modules cohesive and dependencies explicit.
- [ ] Avoid duplication where it causes inconsistent behavior; do not abstract prematurely.
- [ ] Keep functions, classes, and modules understandable and reasonably sized.
- [ ] Use consistent error handling and resource cleanup.
- [ ] Remove dead code, obsolete flags, and unused dependencies.
- [ ] Make concurrency, retries, and side effects explicit.
- [ ] Use code review for correctness, security, maintainability, and operability.
- [ ] Document non-obvious decisions, not every line of code.
- [ ] Track technical debt with impact and remediation context.
- [ ] Use static analysis and automated checks as assistance, not substitutes for review.
- [ ] Keep public interfaces small and stable.
- [ ] Ensure logs and diagnostics do not reveal secrets or personal data.
23. Version control and team collaboration
Tier: Core
- [ ] Use version control for all application and infrastructure code.
- [ ] Protect important branches and require appropriate review.
- [ ] Define commit, branch, pull-request, and release conventions.
- [ ] Require automated checks before merge.
- [ ] Keep changes small enough to review where feasible.
- [ ] Use code ownership for critical paths when useful.
- [ ] Never commit secrets, private keys, production exports, or personal data.
- [ ] Provide a safe secret-revocation and history-cleanup procedure.
- [ ] Record decisions and meaningful trade-offs.
- [ ] Define emergency changes and post-incident review expectations.
- [ ] Maintain repository access controls and remove stale access.
- [ ] Make onboarding instructions reproducible.
24. Developer experience and local environments
Tier: Core
- [ ] Provide a clear, current README and quick-start guide.
- [ ] Define supported runtime, package-manager, compiler, and tool versions.
- [ ] Pin dependencies and use reproducible lockfiles.
- [ ] Provide example environment configuration without real secrets.
- [ ] Automate local setup with scripts, dev containers, or equivalent when useful.
- [ ] Provide safe local services, mocks, or disposable development dependencies.
- [ ] Use synthetic or sanitized data rather than production data by default.
- [ ] Make database migration, seed, reset, and test commands discoverable.
- [ ] Document common commands and troubleshooting steps.
- [ ] Ensure onboarding works on supported operating systems.
- [ ] Keep local and CI behavior sufficiently consistent.
- [ ] Provide fast feedback loops and incremental test commands.
- [ ] Make environment-specific behavior explicit.
- [ ] Avoid requiring undocumented manual setup or personal machine state.
25. Build systems, release engineering, and CI/CD
Tier: Core
- [ ] Automate build, lint, type checks, tests, and security scans.
- [ ] Use reproducible and traceable build artifacts.
- [ ] Separate development, test, staging, and production environments appropriately.
- [ ] Use short-lived credentials and least-privilege CI permissions.
- [ ] Protect build and release pipelines from untrusted pull-request code.
- [ ] Generate release identifiers and link artifacts to source revisions.
- [ ] Deploy through reviewed, repeatable processes.
- [ ] Use rolling, blue/green, canary, or other staged rollout methods when appropriate.
- [ ] Define rollback and roll-forward procedures.
- [ ] Ensure database changes are compatible with mixed application versions during deployment.
- [ ] Add health checks and automated rollout verification.
- [ ] Stop or roll back releases when defined health criteria fail.
- [ ] Support preview environments where they improve feedback.
- [ ] Manage feature flags and migrations as part of releases.
- [ ] Keep deployment credentials and signing keys protected.
- [ ] Track build duration, failure rate, deployment frequency, and change lead time.
- [ ] Verify the deployed artifact—not merely the source branch—is the expected version.
- [ ] Avoid mutable tags or untraceable artifacts in critical production paths.
26. Hosting, infrastructure, networking, and DNS
Tier: Core
- [ ] Choose hosting based on availability, latency, compliance, operations, and cost.
- [ ] Define network boundaries and private/public exposure.
- [ ] Configure DNS, domain ownership, certificate renewal, and domain expiration monitoring.
- [ ] Enforce HTTPS and redirect unsafe HTTP traffic where appropriate.
- [ ] Configure TLS and certificate lifecycle management.
- [ ] Define ingress, egress, firewall, and service-to-service network rules.
- [ ] Keep databases, admin interfaces, and internal services private where possible.
- [ ] Configure health checks, graceful termination, and restart behavior.
- [ ] Set CPU, memory, disk, file-descriptor, and connection limits.
- [ ] Monitor capacity, saturation, network errors, and provider status.
- [ ] Define environment and region placement based on latency and data-residency needs.
- [ ] Use infrastructure as code for repeatable environments when appropriate.
- [ ] Review cloud permissions and network exposure periodically.
- [ ] Document custom domains, DNS records, certificates, and ownership.
- [ ] Test deploys, restarts, and infrastructure changes safely.
27. Containers and orchestration
Tier: Conditional
- [ ] Use minimal, maintained base images and multi-stage builds where useful.
- [ ] Run as a non-root user where possible.
- [ ] Pin base images and scan images for vulnerabilities.
- [ ] Avoid embedding secrets in images or build layers.
- [ ] Define CPU/memory requests, limits, and ephemeral storage needs.
- [ ] Configure liveness, readiness, and startup probes appropriately.
- [ ] Handle SIGTERM and graceful shutdown.
- [ ] Keep container filesystems immutable where possible.
- [ ] Define image provenance, registry access, retention, and cleanup.
- [ ] For orchestration, define service discovery, rollout, autoscaling, and policy controls.
- [ ] Apply network policies and workload identity where supported.
- [ ] Avoid adopting Kubernetes or orchestration complexity without a concrete need.
28. Serverless and edge computing
Tier: Conditional
- [ ] Evaluate cold starts, execution limits, concurrency, and platform constraints.
- [ ] Keep functions stateless or externalize durable state.
- [ ] Define retry and duplicate-execution behavior.
- [ ] Understand event-source delivery guarantees and timeout limits.
- [ ] Protect against unbounded fan-out and runaway invocation cost.
- [ ] Keep edge code small and compatible with its runtime APIs.
- [ ] Understand edge-region data processing and residency implications.
- [ ] Avoid placing secrets or privileged business operations in broadly distributed edge contexts without appropriate controls.
- [ ] Define observability and local testing for deployed functions.
- [ ] Plan vendor-specific limits and migration options.
29. Configuration and secrets management
Tier: Core
- [ ] Separate configuration from application code.
- [ ] Validate required configuration at startup.
- [ ] Keep secrets out of source control, logs, client bundles, and error reports.
- [ ] Use a secrets manager or platform secret facility appropriate to risk.
- [ ] Rotate credentials and revoke compromised secrets quickly.
- [ ] Use different credentials per environment and service.
- [ ] Apply least privilege and short-lived credentials where possible.
- [ ] Document configuration names, meanings, defaults, and owners.
- [ ] Avoid unsafe production defaults and fail clearly on missing critical settings.
- [ ] Track secret access and sensitive configuration changes.
- [ ] Ensure backups and diagnostics do not accidentally expose secrets.
30. Performance engineering
Tier: Core
- [ ] Set performance budgets for critical user journeys and APIs.
- [ ] Measure real-user performance and representative synthetic performance.
- [ ] Track Core Web Vitals and page responsiveness where relevant.
- [ ] Optimize LCP, INP, CLS, TTFB, and critical rendering paths as applicable.
- [ ] Use SSR, SSG, ISR, CSR, or streaming rendering based on page needs.
- [ ] Validate hydration behavior and avoid unnecessary client-side JavaScript.
- [ ] Optimize images, fonts, video, and other media.
- [ ] Use responsive images, modern formats, and lazy loading where appropriate.
- [ ] Minimize render-blocking resources and third-party scripts.
- [ ] Reduce bundle size and remove unused code.
- [ ] Profile CPU, memory, event-loop delay, database queries, and network calls.
- [ ] Apply compression and protocol optimizations appropriately.
- [ ] Optimize cache hit rates and avoid accidental cache bypass.
- [ ] Measure tail latency (p95/p99), not just averages.
- [ ] Test on lower-end devices and constrained networks.
- [ ] Set budgets for expensive APIs, queries, and background jobs.
- [ ] Re-measure after changes and guard against regressions.
31. Scalability and capacity planning
Tier: Core concern; advanced techniques are conditional
- [ ] Estimate expected users, traffic, concurrency, data volume, and growth.
- [ ] Identify bottlenecks and saturation points.
- [ ] Set capacity thresholds and scaling triggers.
- [ ] Use horizontal scaling only where state and architecture permit it.
- [ ] Bound concurrency and apply backpressure.
- [ ] Protect dependencies from traffic spikes and retry storms.
- [ ] Plan database connection, storage, queue, and egress capacity.
- [ ] Test realistic peak and burst traffic.
- [ ] Define graceful degradation and load shedding.
- [ ] Understand rate limits and quotas of critical providers.
- [ ] Plan for hot keys, uneven tenants, and skewed workloads.
- [ ] Revisit capacity assumptions as usage changes.
32. Reliability and fault tolerance
Tier: Core
- [ ] Define availability and latency objectives for critical user journeys.
- [ ] Define service-level indicators/objectives (SLIs/SLOs) when useful.
- [ ] Identify critical dependencies and failure domains.
- [ ] Set timeouts for network calls and database operations.
- [ ] Use retries with backoff, jitter, and bounded retry budgets.
- [ ] Prevent retry amplification and cascading failures.
- [ ] Apply circuit breakers, bulkheads, and load shedding where justified.
- [ ] Design degraded modes and useful fallbacks.
- [ ] Make critical operations idempotent.
- [ ] Define consistency and recovery behavior for partial failures.
- [ ] Avoid single points of failure where the business requirement warrants redundancy.
- [ ] Test failure scenarios, not just healthy operation.
- [ ] Track error budgets or equivalent reliability signals where appropriate.
- [ ] Define when to pause feature delivery to address reliability risk.
33. Observability: logs, metrics, traces, and alerts
Tier: Core
- [ ] Emit structured logs with consistent timestamps and severity.
- [ ] Add request, trace, job, and correlation identifiers.
- [ ] Instrument latency, traffic, errors, saturation, and business-critical events.
- [ ] Use distributed tracing for multi-service flows where appropriate.
- [ ] Redact credentials, tokens, payment details, and sensitive personal data.
- [ ] Define log retention, access, indexing, and deletion.
- [ ] Create dashboards for service health and key user journeys.
- [ ] Alert on user impact and actionable symptoms, not every transient event.
- [ ] Assign an owner and response guidance to each production alert.
- [ ] Test alert delivery and escalation.
- [ ] Monitor frontend errors and real-user performance where appropriate.
- [ ] Track queue depth, age of oldest job, failed jobs, and retry counts.
- [ ] Monitor database performance, connection pools, cache behavior, and provider errors.
- [ ] Avoid high-cardinality metrics and excessive log volume.
- [ ] Use sampling and retention policies to control cost.
- [ ] Ensure monitoring systems are themselves sufficiently reliable.
34. Backup, recovery, and disaster readiness
Tier: Core when data or service continuity matters
- [ ] Identify critical data and configuration that must be recoverable.
- [ ] Define recovery point objective (RPO) and recovery time objective (RTO).
- [ ] Configure automated backups and verify backup completion.
- [ ] Keep backups isolated from routine production credentials and destructive actions.
- [ ] Encrypt backups and restrict access.
- [ ] Define retention and deletion rules for backups.
- [ ] Test restore procedures regularly.
- [ ] Validate restored data integrity and application compatibility.
- [ ] Document recovery ordering and dependencies.
- [ ] Plan for accidental deletion, credential compromise, ransomware, and provider outage.
- [ ] Define regional recovery or failover only to match business requirements.
- [ ] Test failover and failback procedures.
- [ ] Understand recovery limits for queues, object storage, search indexes, and external services.
- [ ] Ensure recovery procedures do not violate privacy or retention obligations.
35. Incident management and production operations
Tier: Core
- [ ] Define incident severity, roles, escalation, and communication channels.
- [ ] Maintain runbooks for common failures and critical systems.
- [ ] Define who can pause releases, disable features, or fail over services.
- [ ] Establish a clear incident commander or coordinator for major incidents.
- [ ] Maintain customer-facing status communication when relevant.
- [ ] Record timeline, impact, mitigation, and follow-up actions.
- [ ] Conduct blameless post-incident reviews for meaningful incidents.
- [ ] Turn corrective actions into owned, prioritized work.
- [ ] Practice incident response and recovery for critical services.
- [ ] Ensure on-call expectations and escalation coverage are sustainable.
- [ ] Monitor external status pages and provider incident channels.
- [ ] Define emergency access with audit trails and expiry.
- [ ] Review alert quality and recurring incident patterns.
36. Data management, privacy, and governance
Tier: Core
- [ ] Inventory personal, sensitive, confidential, and regulated data.
- [ ] Define purpose, lawful basis/consent where applicable, ownership, and permitted uses.
- [ ] Minimize data collection and avoid collecting data without a defined need.
- [ ] Define retention, deletion, archival, export, and correction workflows.
- [ ] Apply data minimization to logs, analytics, support tools, and AI features.
- [ ] Define access controls and auditability for sensitive data.
- [ ] Encrypt sensitive data in transit and at rest where appropriate.
- [ ] Manage data residency and cross-border transfer constraints where applicable.
- [ ] Maintain a data inventory and map of processors/subprocessors as needed.
- [ ] Define subject access, portability, correction, and deletion workflows where required.
- [ ] Ensure deletion propagates to caches, search indexes, analytics, and derived data when required.
- [ ] Define safe use of production data in lower environments.
- [ ] Establish data quality, ownership, lineage, and classification conventions.
- [ ] Review analytics and third-party SDK collection for privacy impact.
- [ ] Keep consent records and honor preference changes.
- [ ] Ensure backups and retained records follow documented legal and operational policies.
37. Data engineering, warehousing, and BI
Tier: Conditional
- [ ] Define business metrics and authoritative definitions.
- [ ] Separate operational workloads from analytical workloads where appropriate.
- [ ] Design ingestion, transformation, and scheduled/streaming pipelines.
- [ ] Validate schemas and handle schema evolution.
- [ ] Make pipeline retries safe and transformations reproducible.
- [ ] Monitor freshness, completeness, volume, quality, and pipeline failures.
- [ ] Define lineage, ownership, and data contracts.
- [ ] Handle late, duplicate, missing, and out-of-order events.
- [ ] Use privacy-aware access controls and retention for analytical datasets.
- [ ] Reconcile critical reports against authoritative systems.
- [ ] Define warehouse costs, query budgets, and retention.
- [ ] Avoid using analytics data as an authoritative operational source unless explicitly designed for it.
- [ ] Document metric definitions and known limitations.
- [ ] Test data transformations and important business metrics.
38. Accessibility and inclusive design
Tier: Core
- [ ] Target a documented accessibility standard, commonly WCAG 2.2 AA where appropriate.
- [ ] Use semantic HTML and accessible native controls.
- [ ] Ensure complete keyboard operation and visible focus.
- [ ] Provide labels, instructions, and useful error associations for forms.
- [ ] Use sufficient contrast and do not convey meaning by color alone.
- [ ] Support screen readers, zoom, reflow, and text resizing.
- [ ] Give images appropriate alternative text; mark decorative images correctly.
- [ ] Provide captions/transcripts for meaningful audio and video.
- [ ] Respect reduced-motion preferences.
- [ ] Avoid inaccessible custom widgets or implement the required interaction patterns.
- [ ] Manage focus for dialogs, navigation, route changes, and dynamic updates.
- [ ] Announce important asynchronous status changes appropriately.
- [ ] Test automated tools plus manual keyboard and assistive-technology usage.
- [ ] Include people with disabilities in usability testing when feasible.
- [ ] Re-test accessibility after component and design-system changes.
39. Internationalization and localization
Tier: Conditional
- [ ] Separate user-facing strings from code.
- [ ] Use locale-aware date, time, number, currency, and measurement formatting.
- [ ] Avoid assuming a single date format, timezone, calendar, or week start.
- [ ] Support translated text expansion and font coverage.
- [ ] Support RTL layouts and bidirectional text where needed.
- [ ] Use CSS logical properties instead of left/right assumptions where possible.
- [ ] Avoid concatenating translated sentence fragments.
- [ ] Define pluralization, gender, and grammatical rules where relevant.
- [ ] Localize validation, emails, notifications, legal text, and generated documents.
- [ ] Define locale fallback and missing-translation behavior.
- [ ] Test localized layouts, sorting, search, and input methods.
- [ ] Distinguish language, locale, timezone, and currency preferences.
- [ ] Review local legal, tax, payment, and cultural requirements.
40. SEO and web discoverability
Tier: Conditional for public/indexable content
- [ ] Define indexable routes and canonical URL rules.
- [ ] Use meaningful titles, descriptions, headings, and semantic content.
- [ ] Generate and maintain XML sitemaps where appropriate.
- [ ] Configure robots directives intentionally; do not accidentally block production.
- [ ] Use redirects and status codes correctly.
- [ ] Avoid duplicate or thin pages and control faceted URL explosions.
- [ ] Add structured data only when accurate and supported.
- [ ] Ensure important content is discoverable without fragile client-only execution where possible.
- [ ] Choose SSR, SSG, ISR, or rendering strategy based on crawlability and freshness.
- [ ] Handle canonicalization across locales and domains.
- [ ] Monitor indexing, crawl errors, broken links, and search performance.
- [ ] Protect private, staging, and authenticated content from indexing.
- [ ] Keep social-sharing metadata accurate where useful.
- [ ] Ensure performance and accessibility support discoverability and usability.
41. Product analytics and measurement
Tier: Core concern; tooling is conditional
- [ ] Define a measurement plan tied to product goals.
- [ ] Define event names, properties, identity rules, and ownership.
- [ ] Track critical funnels, activation, retention, task completion, and failures where useful.
- [ ] Avoid collecting secrets or unnecessary personal data.
- [ ] Respect consent, opt-out, and regional privacy requirements.
- [ ] Prevent duplicate event emission and document delivery guarantees.
- [ ] Validate event schemas and monitor missing or malformed events.
- [ ] Keep metric definitions consistent across dashboards and teams.
- [ ] Distinguish user, account, device, and session identities carefully.
- [ ] Avoid misleading metrics caused by bots, internal traffic, or sampling.
- [ ] Define access controls and retention for analytics data.
- [ ] Use analytics to investigate outcomes, not as a substitute for user research.
- [ ] Review instrumentation after major product changes.
42. Growth, onboarding, and lifecycle marketing
Tier: Conditional
- [ ] Design onboarding around the user's first meaningful success.
- [ ] Minimize unnecessary signup and activation friction.
- [ ] Support invitation, referral, and sharing flows if part of the product.
- [ ] Define lifecycle messages and triggers with user controls.
- [ ] Separate marketing consent from service communications.
- [ ] Provide unsubscribe and preference management.
- [ ] Avoid deceptive patterns, fake urgency, and manipulative consent flows.
- [ ] Use a CMS or marketing site workflow where non-engineers need safe publishing.
- [ ] Define landing-page ownership, review, analytics, and release process.
- [ ] Test acquisition funnels, onboarding completion, and drop-off points.
- [ ] Prevent duplicate campaigns and excessive messaging.
- [ ] Protect referral and promotion systems from abuse.
- [ ] Keep marketing content consistent with product behavior and legal terms.
43. Feature flags, experimentation, and progressive delivery
Tier: Conditional; rollout control is a core concern
- [ ] Separate deployment from feature exposure where useful.
- [ ] Define flag owners, purpose, defaults, and expiry/review dates.
- [ ] Ensure security and authorization do not depend solely on client-side flags.
- [ ] Test enabled, disabled, and fallback states.
- [ ] Scope flags by user, tenant, region, or cohort safely.
- [ ] Define emergency kill switches for risky features.
- [ ] Avoid excessive flag combinations and hidden state.
- [ ] Remove obsolete flags after rollout.
- [ ] Define experiment hypothesis, primary metric, guardrails, and stopping rules.
- [ ] Avoid overlapping experiments that invalidate interpretation.
- [ ] Respect privacy and consent in experimentation.
- [ ] Monitor rollout health and automatically stop when guardrails fail.
44. Admin tools and business operations
Tier: Conditional
- [ ] Define admin roles and least-privilege permissions.
- [ ] Require stronger authentication for privileged access.
- [ ] Audit sensitive actions, data exports, impersonation, and configuration changes.
- [ ] Add confirmation and recovery safeguards for destructive actions.
- [ ] Provide safe search, filtering, pagination, and bulk-action limits.
- [ ] Prevent admin tools from bypassing domain invariants.
- [ ] Restrict bulk exports and redact sensitive fields.
- [ ] Provide support workflows for account recovery and user issues.
- [ ] Make manual overrides visible, attributable, and reversible where possible.
- [ ] Separate support impersonation from actual credential access.
- [ ] Track administrative changes and allow incident investigation.
- [ ] Protect internal tools from public exposure and cross-tenant leakage.
45. Multi-tenancy and organization boundaries
Tier: Conditional
- [ ] Define tenant identity, lifecycle, ownership, and membership.
- [ ] Enforce tenant isolation at every data-access and processing boundary.
- [ ] Test cross-tenant access, search, cache, export, and background-job scenarios.
- [ ] Define tenant-specific roles, settings, quotas, and policies.
- [ ] Decide shared versus isolated databases, schemas, or infrastructure based on risk.
- [ ] Include tenant identity in cache keys and observability context where safe.
- [ ] Prevent tenant data from leaking through logs, metrics, support tools, or AI context.
- [ ] Define tenant provisioning, suspension, migration, export, and deletion.
- [ ] Handle noisy-neighbor risks and per-tenant resource limits.
- [ ] Define tenant-specific data residency or encryption requirements where needed.
- [ ] Test offboarding and ensure tenant data is removed according to policy.
46. SaaS plans, subscriptions, and entitlements
Tier: Conditional
- [ ] Model plans, add-ons, trials, renewals, cancellations, and grace periods.
- [ ] Separate billing status from authorization/entitlement status.
- [ ] Define feature limits, usage quotas, seat counts, and overage behavior.
- [ ] Reconcile subscription changes from trusted billing-provider events.
- [ ] Make webhook handling idempotent and resilient to event ordering.
- [ ] Define failed-payment, dunning, suspension, and reactivation behavior.
- [ ] Handle plan changes, proration, refunds, taxes, and invoices.
- [ ] Enforce entitlements server-side.
- [ ] Provide clear user-facing billing history and cancellation workflows.
- [ ] Keep auditable records of entitlement changes.
- [ ] Test trial expiration, delayed webhooks, duplicate events, and provider outages.
47. Content management and moderation
Tier: Conditional
- [ ] Define content types, ownership, status, publication, and revision history.
- [ ] Support draft, review, scheduled publication, and rollback where needed.
- [ ] Sanitize user-generated HTML and rich text.
- [ ] Define moderation policies and prohibited-content categories.
- [ ] Provide reporting, review queues, appeals, and escalation paths where appropriate.
- [ ] Apply rate limits and spam/abuse prevention.
- [ ] Define takedown, retention, evidence preservation, and deletion processes.
- [ ] Respect copyright, attribution, and licensing requirements.
- [ ] Control who can publish, edit, or delete content.
- [ ] Audit high-impact moderation and editorial actions.
- [ ] Handle versioning, localization, and stale cached content.
- [ ] Use automated moderation as an aid with appropriate human review and error handling.
48. Legal, regulatory, and contractual compliance
Tier: Conditional based on markets and data
- [ ] Identify applicable privacy, consumer protection, accessibility, industry, and regional laws.
- [ ] Publish accurate terms, privacy notices, cookie notices, and relevant policies.
- [ ] Obtain and record consent where required.
- [ ] Define data processing agreements and subprocessor obligations where applicable.
- [ ] Review data residency and international transfer requirements.
- [ ] Define retention, legal hold, and deletion exceptions.
- [ ] Support required user rights and complaint handling.
- [ ] Review payment, health, financial, children’s, education, or other regulated data requirements where relevant.
- [ ] Maintain evidence of required controls and audits.
- [ ] Define breach assessment and notification procedures.
- [ ] Review third-party terms, licenses, and data-sharing practices.
- [ ] Get qualified legal/compliance advice for high-impact or ambiguous obligations.
- [ ] Avoid claiming compliance solely because a tool or provider is certified.
49. AI and machine-learning features
Tier: Conditional
- [ ] Define the user problem and evaluate whether AI is appropriate.
- [ ] Establish quality, latency, privacy, safety, and cost acceptance criteria.
- [ ] Evaluate model capabilities, limitations, terms, retention, and data use.
- [ ] Keep provider keys server-side and apply per-user/tenant budgets.
- [ ] Treat model output as untrusted input.
- [ ] Defend against prompt injection, data exfiltration, tool misuse, and unsafe retrieval.
- [ ] Enforce authorization outside the model; never let model text grant permissions.
- [ ] Validate tool arguments and require confirmation for consequential actions.
- [ ] Limit tool access, execution time, recursion, token usage, and total agent steps.
- [ ] Set hard spending ceilings, rate limits, circuit breakers, and kill switches to prevent runaway agent costs.
- [ ] Design for hallucinations, uncertainty, refusals, and graceful fallback.
- [ ] Evaluate quality against representative datasets and adversarial cases.
- [ ] Monitor model drift, quality regressions, latency, refusals, and cost.
- [ ] Define human review for high-impact or irreversible decisions.
- [ ] Protect prompts, context, retrieval results, and outputs from sensitive-data leakage.
- [ ] Respect user consent and opt-outs for training or secondary data use.
- [ ] Document training-data and content provenance where known and material.
- [ ] Review copyright, licensing, attribution, and intellectual-property risks for input and output.
- [ ] Define retention and deletion for prompts, embeddings, indexes, and model-related logs.
- [ ] Test retrieval permissions and prevent cross-user or cross-tenant context leakage.
- [ ] Disclose AI use where appropriate and provide a path to human support when needed.
- [ ] Avoid presenting probabilistic outputs as guaranteed facts.
- [ ] Version prompts, models, tools, and evaluations so behavior changes are traceable.
50. Security operations and software supply-chain security
Tier: Core concern; depth depends on risk
- [ ] Maintain an inventory of direct and transitive dependencies.
- [ ] Review dependency updates and monitor known vulnerabilities.
- [ ] Generate and retain a software bill of materials (SBOM) where useful or required.
- [ ] Pin dependencies and verify package provenance where supported.
- [ ] Protect package registries, signing keys, build identities, and release credentials.
- [ ] Scan source, dependencies, container images, infrastructure definitions, and built artifacts.
- [ ] Review CI/CD permissions and isolate untrusted workflows.
- [ ] Use signed artifacts or attestations for critical systems where appropriate.
- [ ] Define patch timelines by severity and exploitability.
- [ ] Monitor advisories for runtimes, operating systems, frameworks, and managed services.
- [ ] Maintain an asset inventory and ownership map.
- [ ] Define vulnerability disclosure and coordinated remediation.
- [ ] Rotate credentials after suspected compromise.
- [ ] Practice incident response for leaked secrets and compromised dependencies.
- [ ] Protect developer accounts with MFA and least privilege.
51. Cost management and FinOps
Tier: Core
- [ ] Estimate baseline, growth, and peak operating costs before launch.
- [ ] Assign ownership and budgets to major services and environments.
- [ ] Tag resources by environment, team, product, or tenant where possible.
- [ ] Set budgets, anomaly detection, and cost alerts.
- [ ] Monitor cost per active user, transaction, request, tenant, or workload where useful.
- [ ] Track database, storage, egress, logs, observability, third-party, and AI costs.
- [ ] Set quotas and spending limits for potentially unbounded operations.
- [ ] Expire temporary environments and clean up unused resources.
- [ ] Review reserved capacity, autoscaling, and commitment decisions against actual usage.
- [ ] Avoid cost optimization that violates reliability, privacy, or security requirements.
- [ ] Model the cost of backups, disaster recovery, and data retention.
- [ ] Include vendor price changes and lock-in in major design decisions.
52. Documentation and knowledge management
Tier: Core
- [ ] Document system purpose, architecture, dependencies, and major flows.
- [ ] Maintain setup, development, testing, deployment, and rollback instructions.
- [ ] Document APIs, schemas, events, and external integrations.
- [ ] Maintain runbooks for critical operations and common incidents.
- [ ] Record architecture decisions and important trade-offs.
- [ ] Document environment variables and secret ownership without exposing secret values.
- [ ] Keep diagrams and docs aligned with actual behavior.
- [ ] Define owners and review cadence for critical documentation.
- [ ] Document data classifications, retention, and recovery procedures.
- [ ] Provide onboarding material and troubleshooting guides.
- [ ] Keep customer-facing help and release notes current where relevant.
53. Customer support and service operations
Tier: Core for customer-facing products
- [ ] Provide a discoverable support channel appropriate to the product.
- [ ] Define support hours, response expectations, escalation, and ownership.
- [ ] Provide safe account recovery and identity verification procedures.
- [ ] Give support staff the minimum data and permissions needed.
- [ ] Redact sensitive information from tickets and support exports.
- [ ] Link support cases to relevant diagnostics without exposing secrets.
- [ ] Define complaint, refund, abuse, and account-appeal workflows where applicable.
- [ ] Provide accessible and understandable error messages and help content.
- [ ] Establish a process for turning recurring issues into product improvements.
- [ ] Track support volume, resolution time, and recurring causes.
- [ ] Ensure support tooling respects tenant boundaries and audit requirements.
- [ ] Define customer communications for incidents and service degradation.
54. Maintenance, upgrades, and technical debt
Tier: Core
- [ ] Keep runtimes, frameworks, operating systems, and dependencies supported.
- [ ] Schedule security updates and end-of-life remediation.
- [ ] Track deprecations and breaking changes from critical providers.
- [ ] Automate dependency update checks where useful.
- [ ] Test upgrades in representative environments before production.
- [ ] Maintain compatibility policies for APIs, clients, and integrations.
- [ ] Review recurring incidents and maintenance burden.
- [ ] Prioritize technical debt by risk, impact, and future cost.
- [ ] Remove obsolete features, flags, services, and dependencies.
- [ ] Test migration and rollback plans before high-risk upgrades.
- [ ] Keep certificates, domains, signing keys, and licenses from expiring unexpectedly.
- [ ] Review access, ownership, and vendor contracts periodically.
55. Mobile-specific engineering
Tier: Conditional for native or hybrid mobile apps
- [ ] Define supported OS versions, devices, screen sizes, and distribution channels.
- [ ] Follow platform navigation, accessibility, and interaction conventions.
- [ ] Handle lifecycle transitions, backgrounding, interruptions, and process termination.
- [ ] Handle intermittent networks, offline state, retries, and synchronization conflicts.
- [ ] Store tokens and sensitive data using platform-secure storage.
- [ ] Minimize permissions and explain why they are needed.
- [ ] Protect deep links and validate incoming intents/URLs.
- [ ] Configure push notifications, token rotation, and opt-in behavior.
- [ ] Manage signing keys, provisioning, store credentials, and release access.
- [ ] Test app upgrades, migrations, rollback constraints, and backward-compatible APIs.
- [ ] Monitor crashes, freezes, startup time, and app performance.
- [ ] Provide staged releases and crash-rate monitoring.
- [ ] Meet app-store privacy disclosures and permission policies.
- [ ] Test on real devices and lower-resource hardware.
- [ ] Define secure local cache and data removal on logout or account deletion.
56. Progressive web apps and advanced web platform
Tier: Conditional
- [ ] Decide whether offline capability is actually needed and define supported offline tasks.
- [ ] Configure service workers and cache versioning carefully.
- [ ] Prevent stale authenticated or private data from leaking between users.
- [ ] Define offline mutation queues, conflict handling, and retry behavior.
- [ ] Configure web app manifest, icons, install experience, and update messaging.
- [ ] Handle service-worker update and rollback behavior.
- [ ] Use browser storage APIs with quota, eviction, and private-browsing limitations in mind.
- [ ] Avoid storing highly sensitive information in persistent browser storage unless justified and protected.
- [ ] Test offline, slow, captive-portal, and intermittent network scenarios.
- [ ] Handle background sync and push support differences across browsers.
- [ ] Provide graceful fallback when advanced APIs are unavailable.
- [ ] Ensure cached assets and pages respect security and privacy requirements.
57. Hardware, IoT, and companion-device integrations
Tier: Conditional
- [ ] Define supported devices, firmware, protocols, and compatibility matrix.
- [ ] Authenticate devices and provision unique identities securely.
- [ ] Provide secure onboarding, pairing, ownership transfer, and revocation.
- [ ] Encrypt communications and protect device credentials.
- [ ] Define firmware update signing, verification, rollout, and recovery.
- [ ] Handle intermittent connectivity, offline operation, and eventual synchronization.
- [ ] Validate telemetry and command inputs.
- [ ] Apply rate limits and authorization to remote commands.
- [ ] Define safe states for disconnection, stale commands, and partial failure.
- [ ] Track device inventory, versions, health, and decommissioning.
- [ ] Consider physical access, tampering, battery, bandwidth, and resource constraints.
- [ ] Define privacy, consent, retention, and access for sensor data.
- [ ] Test compatibility, failure recovery, and firmware rollback.
58. Advanced distributed systems
Tier: Advanced
- [ ] Define consistency models and user-visible implications.
- [ ] Understand leader election, quorum behavior, split brain, and fencing where applicable.
- [ ] Define partition tolerance and failure behavior explicitly.
- [ ] Use event sourcing only when history/replay requirements justify it.
- [ ] Use CQRS only when read/write needs and complexity warrant it.
- [ ] Define event schemas, ownership, compatibility, and replay behavior.
- [ ] Handle duplicate and out-of-order events.
- [ ] Use sagas or compensating transactions for multi-service workflows where appropriate.
- [ ] Use transactional outbox/inbox or equivalent delivery patterns where required.
- [ ] Define consistency repair and reconciliation jobs.
- [ ] Avoid distributed transactions unless necessary and well understood.
- [ ] Design partitioning, rebalancing, and hot-key handling deliberately.
- [ ] Define multi-region data ownership, failover, conflict resolution, and recovery.
- [ ] Test network partitions, partial failures, delayed messages, and regional outages.
- [ ] Track replication lag, queue lag, event age, and reconciliation drift.
- [ ] Ensure operational complexity is justified by measurable requirements.
59. Operational governance and engineering management
Tier: Advanced, or Core for larger/high-risk organizations
- [ ] Define service ownership, on-call responsibility, and escalation paths.
- [ ] Maintain a service catalog and dependency map.
- [ ] Define production access review and separation of duties where appropriate.
- [ ] Establish change management proportional to risk.
- [ ] Track SLOs, error budgets, operational risks, and reliability work.
- [ ] Define security, privacy, architecture, and compliance review paths.
- [ ] Maintain evidence for audits and control testing where required.
- [ ] Establish incident, vulnerability, and disaster-recovery exercises.
- [ ] Define release approval and emergency change procedures.
- [ ] Track engineering health, delivery friction, and toil.
- [ ] Make risk acceptance explicit, owned, and time-bounded.
- [ ] Review vendor concentration, service dependencies, and exit strategies.
- [ ] Keep operational processes useful and proportional rather than bureaucratic.
60. Decommissioning and end-of-life
Tier: Core lifecycle concern
- [ ] Define product, feature, API, service, and dependency end-of-life procedures.
- [ ] Communicate changes and migration paths to affected users and integrations.
- [ ] Provide export or migration options where required.
- [ ] Revoke credentials, tokens, certificates, and external access.
- [ ] Remove DNS records, public endpoints, and unnecessary network exposure.
- [ ] Archive required records and delete data according to retention policy.
- [ ] Remove jobs, queues, webhooks, cron tasks, and scheduled integrations.
- [ ] Remove obsolete infrastructure, storage, domains, and cloud resources.
- [ ] Cancel unused subscriptions and vendor contracts.
- [ ] Preserve necessary audit records, source history, and operational evidence.
- [ ] Verify that decommissioned systems no longer receive sensitive data.
- [ ] Update documentation, service catalogs, dashboards, alerts, and dependency maps.
- [ ] Confirm cost and access cleanup after shutdown.
61. Cross-cutting production principles
Tier: Core
- [ ] Security: Treat all external input and inter-service boundaries as untrusted.
- [ ] Privacy: Collect, expose, retain, and share only what is needed.
- [ ] Reliability: Define failure behavior before failures occur.
- [ ] Observability: Make important behavior diagnosable without exposing sensitive data.
- [ ] Accessibility: Make core tasks usable by people with diverse abilities.
- [ ] Performance: Measure user impact and protect critical paths.
- [ ] Consistency: Make business invariants explicit and enforce them at trusted boundaries.
- [ ] Idempotency: Make retries and duplicate delivery safe where side effects exist.
- [ ] Least privilege: Grant the minimum access needed to people, services, jobs, and pipelines.
- [ ] Reversibility: Prefer changes that can be rolled back or safely compensated.
- [ ] Automation: Automate repeatable checks and operational tasks when it reduces risk.
- [ ] Simplicity: Do not adopt complexity without a concrete requirement.
- [ ] Ownership: Every critical service, data set, alert, and workflow has an owner.
- [ ] Documentation: Record decisions and procedures needed by future maintainers.
- [ ] Cost awareness: Measure and constrain expensive or unbounded workloads.
- [ ] Verification: A design or checklist item is not complete until it has been tested or otherwise evidenced.
- [ ] Continuous improvement: Feed incidents, support cases, analytics, and user research back into engineering priorities.
62. Go-live readiness gate
Tier: Core

Use this as a final release gate. Not every item applies to every product, but every exception should be deliberate.
Product and UX
- [ ] Critical user journeys work end to end.
- [ ] Acceptance criteria and launch requirements are met.
- [ ] Empty, loading, error, success, and recovery states are implemented.
- [ ] Help, support, and user-facing policies are ready.
- [ ] Accessibility and responsive behavior have been checked.
Security and privacy
- [ ] Authentication and authorization tests pass.
- [ ] Secrets are not committed or exposed in client bundles/logs.
- [ ] Sensitive data flows and retention rules have been reviewed.
- [ ] Dependencies and deployed artifacts have been checked for known high-risk issues.
- [ ] Abuse controls, rate limits, and administrative access are in place.
- [ ] Required privacy notices, consent, and compliance reviews are complete.
Data and business integrity
- [ ] Migrations are tested and compatible with deployment sequencing.
- [ ] Backup and restore have been verified.
- [ ] Critical financial, inventory, subscription, or workflow states reconcile correctly.
- [ ] Idempotency and duplicate-event behavior are tested for side-effecting flows.
- [ ] Data export, deletion, and recovery behavior is understood.
Quality and performance
- [ ] Unit, integration, contract, and critical end-to-end tests pass.
- [ ] Supported browsers/devices have been checked.
- [ ] Performance budgets and capacity assumptions have been validated.
- [ ] Critical accessibility checks have passed.
- [ ] High-risk failure and dependency-outage scenarios have been exercised.
Operations and release
- [ ] Production configuration and secrets are correct.
- [ ] Health checks, logs, metrics, traces, dashboards, and actionable alerts are ready.
- [ ] Deployment, rollback, and feature-disable procedures are documented.
- [ ] Runbooks and incident contacts are available.
- [ ] On-call/support ownership is clear.
- [ ] Cost budgets and alerts are configured.
- [ ] External service quotas, domains, TLS certificates, and webhook endpoints are verified.
- [ ] Rollout and post-release verification steps are defined.
- [ ] Known risks and accepted exceptions have owners and review dates.
Tailoring the checklist to a project
A practical way to use this list is to create a project-specific copy and classify every section as:
- Required now — needed for launch or safe operation.
- Required later — deliberately deferred with an owner and target milestone.
- Conditional — activated by a documented product, legal, scale, or architecture trigger.
- Not applicable — include a brief reason.
Do not confuse a production-ready product with one that uses every technology. A small, well-designed application can be production-grade without microservices, Kubernetes, event sourcing, a data warehouse, or AI. The goal is to make the relevant risks, controls, responsibilities, and operational behaviors explicit—and to verify them.
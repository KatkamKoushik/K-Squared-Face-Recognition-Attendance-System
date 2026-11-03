Exhaustive CI Workflow Testing Checklist for GitHub Actions — Expanded Edition
A comprehensive checklist of automated checks you can run in GitHub Actions for web applications, APIs, libraries, mobile apps, infrastructure, and production systems.
Important: No project needs every check. Treat this as a catalog: choose checks according to your stack, risk, user impact, data sensitivity, and compliance requirements. Mark items N/A with a reason rather than adding unnecessary complexity.
Suggested status convention: [ ] Not started · [x] Verified · [~] In progress · [N/A] Not applicable
How to use this checklist
Pull request CI: fast, deterministic checks required before merge.
Merge queue CI: include the merge_group event when required status checks must run for GitHub Merge Queues.
Push CI: run essential checks on protected branches and direct pushes where allowed.
Scheduled CI: run slower scans, broader compatibility matrices, flaky-test detection, fuzzing, and dependency audits.
Pre-release / staging: run end-to-end, performance, migration, security, and deployment verification against a production-like environment.
Post-deployment: smoke-test the deployed release and monitor health. These are usually CD/release checks adjacent to CI.
Keep credentials least-privileged, use isolated test data, and never expose production secrets to untrusted pull-request code.
Treat pull_request_target and privileged workflow_run workflows as special security boundaries; do not execute untrusted pull-request code in them.
Table of contents
Workflow triggers and policy
Workflow syntax, permissions, and security
Repository hygiene and change validation
Formatting, linting, and static quality
Type checks and compilation
Unit tests
Component and UI tests
Integration tests
End-to-end tests
API and protocol tests
Contracts and compatibility
Database and data integrity
Authentication, authorization, and sessions
Application security tests
Dependency and software supply-chain security
Secrets, configuration, and environment checks
Build, artifacts, packages, and containers
Frontend, browser, and accessibility checks
Performance and resource budgets
Concurrency, resilience, and reliability
Queues, jobs, events, and webhooks
External services and third-party integrations
Product-specific workflow tests
Mobile, PWA, and device testing
Infrastructure-as-code and cloud configuration
Documentation and developer experience
Data privacy, analytics, and compliance checks
AI/ML and agentic-system tests
Advanced testing techniques
Deployment and release verification
Observability and operational readiness
CI performance, quality, and maintenance
Suggested workflow tiers
Final merge and release gates
1. Workflow triggers and policy
Run required CI checks on pull requests targeting protected branches.
If using GitHub Merge Queues, include the merge_group trigger in workflows that produce required checks; verify the merge-group SHA is actually tested.
Test the merge_group path separately because it is distinct from pull_request and push events.
Run CI on pushes to protected branches.
Run CI for relevant release tags.
Add scheduled workflows for checks that are too slow for each pull request.
Add manual dispatch for maintenance, recovery, or controlled release workflows.
Use path filters only when they cannot accidentally skip required checks.
For monorepos, compute affected packages/apps from the dependency graph (for example with Nx, Turborepo, or Bazel) rather than relying only on hand-written file globs.
Ensure a shared-library change triggers CI for every downstream consumer that may be affected.
Fall back to broader/full CI when dependency-graph calculation fails or central build/workflow/configuration files change.
Ensure required status checks report reliably even if conditional jobs are skipped.
Define which checks are required for merging and which are advisory.
Cancel superseded pull-request runs when safe.
Avoid cancellation for jobs that perform non-idempotent operations or must finish.
Prevent duplicate workflow runs where practical.
Define timeouts for workflows and jobs.
Define matrix dimensions deliberately: supported OS, runtime versions, CPU architectures (amd64/`arm64`) where available, and locale/timezone cases where relevant.
Set strategy.fail-fast: false for compatibility matrices when you want to collect failures from all matrix combinations instead of cancelling siblings after the first failure.
Use concurrency groups to prevent conflicting deployments or destructive test runs.
Ensure untrusted pull requests cannot trigger privileged deployment workflows.
Test behavior for fork pull requests and missing secrets.
Keep CI policy consistent across repositories where practical.
Document exceptions to required checks and assign an owner.
Verify branch rules or repository rulesets actually require the intended checks.
2. Workflow syntax, permissions, and security
Validate workflow YAML syntax.
Lint GitHub Actions workflow files.
Check expressions for unsafe interpolation and injection risks.
Avoid placing untrusted PR titles, branch names, issue content, or user input directly into shell commands.
Use least-privilege GITHUB_TOKEN permissions.
Explicitly set workflow/job permissions instead of relying on broad defaults.
Pin third-party actions to reviewed immutable commit SHAs where required by policy.
Review action publishers, source code, maintenance status, and permission needs.
Prefer official or verified actions when practical.
Avoid deprecated actions and runtimes.
Keep actions and reusable workflows updated.
Restrict deployment environments and require approvals for production where appropriate.
Use environment protection rules for sensitive deployments.
Use OpenID Connect (OIDC) federation instead of long-lived cloud credentials where supported.
Protect signing keys, deployment keys, package tokens, and environment secrets.
Prevent secrets from being printed in logs, artifacts, or test reports.
Do not expose production secrets to forked or otherwise untrusted code.
Treat pull_request_target and privileged workflow_run workflows as high-risk: never check out and execute an untrusted PR head, run its package install/build scripts, or execute its tests in a privileged job.
For privileged PR automation (labels/comments/triage), use trusted base-branch code, minimal permissions, and treat PR contents as data only.
Do not assume github.event.pull_request.head.sha is safe to check out in a privileged workflow.
For build/test jobs that do not need authenticated Git operations, set actions/checkout persist-credentials: false where compatible with the action/version and workflow needs.
Review the credential-storage behavior of the exact actions/checkout version in use; do not assume every version stores the token in the same location.
Never write untrusted values directly to $GITHUB_ENV, $GITHUB_OUTPUT, or $GITHUB_PATH; validate/allowlist values and avoid multiline-command/file injection.
Prevent untrusted input from overriding environment variables, runtime options, or executable search paths for subsequent steps.
Treat restored caches as untrusted input where they may contain executable code or build artifacts; verify artifacts and isolate cache keys/scopes.
Understand cache visibility across default branches, feature branches, and pull-request merge refs; do not let untrusted cached binaries enter privileged jobs.
Monitor cache churn and eviction; GitHub documents a 10 GB repository cache limit in its cache documentation at the time of this checklist, but limits and policies can change.
Audit runner network egress where practical; use firewall rules, isolated runners, or a reviewed egress-monitoring control to detect unexpected outbound traffic from build/test steps.
Audit workflow changes in code review.
Validate reusable workflow inputs and outputs.
Ensure a workflow cannot alter required checks or protections without authorized review.
Test that cleanup steps run after failures when cleanup is important.
Avoid executing arbitrary code from artifacts produced by untrusted workflows.
Use artifact attestations or provenance where suitable for supply-chain requirements.
3. Repository hygiene and change validation
Check for accidental generated files, local caches, build outputs, or large binaries.
Detect committed secrets and private keys.
Validate .gitignore and repository ignore rules where relevant.
Check required metadata, license files, and notice files.
Validate version numbers and package metadata.
Validate changelog or release notes when required.
Check PR title, description, linked issue, and checklist where team policy requires them.
Validate commit message conventions when used.
Detect unwanted whitespace, merge markers, and conflict markers.
Check for accidental debug statements or temporary code.
Check that code owners or required reviewers are configured for sensitive areas.
Check that generated source or API clients are up to date.
Verify generated files are not unintentionally out of sync with their source.
Check for accidental changes to migrations, lockfiles, or generated artifacts.
Validate repository size and large-file policies if relevant.
Validate Git LFS pointers and run the applicable LFS integrity check; catch large files accidentally committed as raw blobs.
Detect case-insensitive filename collisions (for example Utils.ts and utils.ts) that behave differently across Linux, macOS, Windows, or developer filesystems.
Check for unsupported path names, file modes, symlink assumptions, or platform-specific path-length issues when cross-platform contributors are supported.
4. Formatting, linting, and static quality
Code formatting check.
Language-specific linting.
Framework-specific linting.
CSS/SCSS linting.
HTML/template linting.
Markdown linting.
YAML linting.
JSON validation.
TOML validation.
XML validation where used.
Shell script linting.
SQL linting.
Dockerfile linting.
Infrastructure configuration linting.
Static code analysis.
Dead-code and unused-export detection.
Unused dependency detection.
Duplicate-code analysis where beneficial.
Complexity and maintainability checks where useful.
Import-order and dependency-boundary checks.
Architecture rule checks.
Check for deprecated API use.
Validate ICU MessageFormat syntax in translation resources (including plural/select placeholders) where used.
Check for TODO/FIXME markers in release-critical paths if policy requires it.
Validate code ownership boundaries for protected modules.
Treat quality thresholds as meaningful signals, not as substitutes for code review.
5. Type checks and compilation
TypeScript or language type-check command.
Strict type checking for critical modules where feasible.
Nullability and unsafe-cast checks where supported.
Compile all relevant packages/modules.
Compile production targets, not only development targets.
Compile supported runtime versions where required.
Validate framework-generated types.
Validate schema-generated types and API client types.
Verify generated types match API/schema definitions.
Check for unsupported language/runtime features.
Check compiler warnings where policy treats them as failures.
Validate native extensions or platform-specific compilation if used.
In monorepos, validate affected-graph computation and package dependency edges; test that shared-code changes select all downstream consumers.
For published libraries/SDKs, validate declaration files under supported TypeScript resolution modes such as NodeNext and bundler where applicable.
Validate ESM/CommonJS entry points and conditional exports mappings for dual-format packages.
6. Unit tests
Unit-test core business logic.
Test normal/happy paths.
Test boundary values and edge cases.
Test invalid and malformed inputs.
Test missing, null, empty, and unexpected values.
Test error handling and error mapping.
Test rounding, currency, units, date, time, and timezone logic.
Test domain invariants and state transitions.
Test permission decision logic.
Test retry logic and backoff calculations.
Test idempotency and deduplication helpers.
Test utility functions and parsers.
Test serialization and deserialization.
Test deterministic behavior where expected.
Test cancellation and cleanup paths.
Test time-dependent behavior with controlled clocks.
Test random behavior with seeded randomness where possible.
Track coverage for important modules.
Set coverage thresholds only where meaningful and maintainable.
Ensure test failures are deterministic and actionable.
Track and reduce flaky tests.
Verify tests fail when the intended behavior is broken.
Run unit tests in a hermetic/no-network mode where practical, allowing only loopback or explicitly required local test services.
Detect accidental requests to live third-party APIs from unit tests; require mocks/fakes for external dependencies.
Ensure unit tests do not need production credentials or live payment, email, analytics, or identity-provider accounts.
7. Component and UI tests
Test component rendering.
Test props, parameters, and variant behavior.
Test user interactions and event handlers.
Test forms and validation.
Test disabled, loading, empty, success, and error states.
Test keyboard and focus behavior.
Test modal, dialog, popover, tooltip, and menu behavior.
Test optimistic UI and rollback after failure.
Test stale request and out-of-order response behavior.
Test component cleanup and lifecycle behavior.
Test error boundaries or equivalent rendering-failure recovery.
Test navigation and route transitions.
Test state persistence and reset behavior.
Test component behavior with long text and unusual data.
Use snapshots selectively, not as the only assertion.
Run visual component tests where the team maintains reliable baselines.
Run component tests with external network access disabled where practical so missing mocks and hidden live dependencies are exposed.
Add pseudo-localization layout checks with expanded strings (roughly 30–40% longer where useful) to reveal clipping, truncation, and layout overflow.
8. Integration tests
Test application-to-database integration.
Test application-to-cache integration.
Test application-to-queue integration.
Test worker-to-database integration.
Test database transaction boundaries.
Test actual serialization and schema validation.
Test application configuration against real dependencies.
Test startup and shutdown behavior.
Test authentication middleware and authorization filters.
Test file upload/download paths.
Test email/SMS/push adapters with test providers or fakes.
Test payment-provider adapters in sandbox mode.
Test cache invalidation and data propagation.
Test search indexing and removal flows.
Test transactions that publish events.
Test real infrastructure in disposable environments where mock-only tests would miss important behavior.
Ensure integration tests isolate data and clean up resources.
Test failures and timeouts of dependent components.
Restrict integration-test network egress to local containers and approved test endpoints where possible.
Fail or flag unexpected outbound requests so tests cannot silently depend on live third-party services.
Separate hermetic unit/component tests from explicitly networked integration tests and document the allowlist for the latter.
9. End-to-end tests
Test sign-up, verification, login, and logout where applicable.
Test password reset and account recovery.
Test the primary user journey from start to successful completion.
Test critical forms and validation messages.
Test navigation and deep links.
Test search, filtering, sorting, and pagination.
Test create, read, update, and delete flows.
Test file upload and download.
Test role-specific user journeys.
Test tenant or organization isolation.
Test checkout and payment in sandbox environments if applicable.
Test subscription changes and entitlement updates if applicable.
Test notification-triggering workflows where useful.
Test cancellation and recovery flows.
Test empty, error, and permission-denied journeys.
Test session expiration and reauthentication.
Test the most important workflows using realistic seeded data.
Run a small, stable smoke E2E suite on each PR.
Run the broader E2E suite on protected branches or staging.
Capture screenshots, traces, logs, and videos on failure without leaking secrets.
Ensure tests do not depend on execution order or shared accounts.
10. API and protocol tests
Endpoint status-code tests.
Request validation tests.
Response schema tests.
Error response shape tests.
API authentication tests.
Object-level authorization tests.
Pagination tests.
Filtering and sorting tests.
Request size and payload limits.
Rate limit and quota tests.
Idempotency-key tests for side-effecting requests.
Conditional request and caching-header tests.
Content negotiation tests where supported.
CORS behavior tests.
API versioning tests.
Timeout and cancellation behavior tests.
Compression and streaming tests where relevant.
Upload/download content-type and content-disposition tests.
gRPC method and Protobuf schema tests if used.
GraphQL schema, resolver, authorization, and query-complexity tests if used.
Diff GraphQL schemas against the base branch and detect breaking changes such as removed fields/arguments, removed enum values, tighter output nullability, newly required input fields, or incompatible input-type changes.
WebSocket/SSE connect, authorization, heartbeat, reconnect, and message tests where applicable.
Validate OpenAPI or other machine-readable API specifications.
Ensure API docs match the implementation.
11. Contracts and compatibility
Consumer-driven contract tests where appropriate.
Provider contract verification.
API backward-compatibility tests.
Event schema compatibility checks.
Protobuf/Avro/JSON Schema compatibility checks where used.
Generated client compatibility tests.
Database schema compatibility during rolling deployments.
Check that old and new application versions can coexist during a rollout.
Check deprecation and removal policies for public interfaces.
Test compatibility across supported runtime/library versions.
Validate third-party API assumptions using recorded fixtures or provider sandboxes.
Test data-format changes against existing stored data.
Validate compatibility of exported packages and public SDKs.
Test critical feature-flagged behavior in both ON and OFF states.
Test important flag combinations when interactions can change authorization, billing, data shape, or critical workflows; control combinatorial explosion by risk-based selection.
Include flag defaults and emergency kill-switch behavior in compatibility checks.
12. Database and data integrity
Schema validation.
Migration syntax and application tests.
Migration rollback or forward-recovery tests, depending on migration strategy.
Expand/migrate/contract compatibility checks for zero-downtime deployments.
Constraint and uniqueness tests.
Foreign-key and referential-integrity tests.
Transaction commit and rollback tests.
Isolation and locking tests.
Concurrent write tests.
Optimistic concurrency/version conflict tests.
Query correctness tests.
Query-plan or slow-query regression checks where practical.
N+1 query detection where supported.
Connection-pool limits and exhaustion tests.
Replication lag handling tests where applicable.
Cache/database consistency checks.
Search-index/database consistency checks.
Seed data and fixture validation.
Test data cleanup and isolation.
Data retention and deletion tests.
Export and portability tests.
Backup and restore tests in a disposable environment.
Large migration rehearsal using representative data volumes where needed.
Tenant isolation checks at the data-access layer.
Ensure test and CI databases cannot accidentally target production.
13. Authentication, authorization, and sessions
Login success/failure tests.
Password hashing and verification behavior tests.
Password reset tests.
Email/phone verification tests.
MFA enrollment, challenge, recovery, and disable tests when supported.
Session creation, renewal, expiry, and revocation tests.
Cookie flag tests (Secure, HttpOnly, SameSite) where relevant.
OAuth/OIDC state, nonce, issuer, audience, and redirect validation tests.
Logout and all-device logout behavior tests.
Account lockout, throttling, and anti-enumeration tests.
Role and permission matrix tests.
Object-level authorization tests to prevent IDOR/BOLA.
Privilege escalation tests.
Admin and support-access tests.
Tenant boundary tests.
Expired/revoked token tests.
Session fixation and replay-resistance tests where applicable.
Account suspension, deletion, and recovery tests.
Audit log coverage for security-sensitive actions.
Verify credentials, tokens, and recovery codes never appear in logs.
14. Application security tests
Static application security testing (SAST).
Dynamic application security testing (DAST) against an isolated running application.
SQL/NoSQL injection tests.
Cross-site scripting (XSS) tests.
Cross-site request forgery (CSRF) tests.
Server-side request forgery (SSRF) tests.
Path traversal tests.
Open redirect tests.
Unsafe deserialization tests.
XML external entity (XXE) tests if XML parsers are exposed.
Request smuggling and HTTP parser mismatch checks where relevant.
Mass-assignment tests.
Unrestricted resource consumption tests.
File-upload validation and malware-scanning flow tests.
Content-type and MIME-sniffing checks.
Security-header checks, including CSP where appropriate.
TLS and certificate configuration checks where practical.
CORS policy validation.
Rate-limit and abuse-control tests.
Bot, scraping, credential-stuffing, and brute-force controls where relevant.
SSRF egress restrictions for URL-fetching or document-processing features.
Verify stack traces and internal details are not exposed to users.
Verify sensitive fields are not unnecessarily returned by APIs.
Check that authorization is server-enforced rather than based on UI state.
Run penetration tests or independent assessments at an appropriate cadence for high-risk systems.
Test security failure paths, including unavailable identity or policy services.
15. Dependency and software supply-chain security
Scan direct and transitive dependencies for known vulnerabilities.
Review newly introduced dependencies in pull requests.
Detect outdated or unsupported dependencies.
Detect malicious or typosquatted package risks where tooling supports it.
Validate lockfile integrity and consistency.
Check package licenses against project policy.
Generate a Software Bill of Materials (SBOM) where useful or required.
Scan container base images and OS packages.
Scan artifacts for known vulnerabilities.
Scan infrastructure dependencies and provider modules.
Pin high-risk tooling and actions to reviewed versions or immutable SHAs.
Verify package provenance or signatures where available.
Generate build provenance/attestations where needed.
Check for dependencies with known end-of-life status.
Define vulnerability severity and remediation thresholds.
Avoid failing all builds on low-risk findings without a triage policy.
Ensure scanner databases and tools are updated appropriately.
Test the vulnerability-reporting process and remediation ownership.
Validate Dependabot (.github/dependabot.yml) or Renovate configuration, including ecosystems, schedules, grouping, and target branches.
Validate any policy that automatically updates GitHub Actions and reusable workflows.
16. Secrets, configuration, and environment checks
Run secret scanning on changed files and/or repository history as policy requires.
Detect API keys, credentials, private keys, and tokens in source.
Validate required environment variables.
Validate configuration schemas and defaults.
Ensure development/test configuration is separate from production configuration.
Fail safely when critical configuration is missing or invalid.
Ensure frontend builds do not contain server-side secrets.
Ensure logs, test output, and artifacts redact sensitive data.
Validate CORS origins, redirect URLs, and allowed hosts by environment.
Validate database and external-service endpoints point to the intended environment.
Check that CI jobs do not use production credentials unnecessarily.
Test secret rotation or credential-revocation procedures where practical.
Check that example environment files contain placeholders, not real secrets.
Validate certificate and key formats where relevant.
Ensure secrets are not passed to untrusted scripts or third-party actions.
17. Build, artifacts, packages, and containers
Clean dependency installation from lockfiles.
Production application build.
Development/test build if distinct.
Build all workspaces/packages in a monorepo as required.
Validate expected build outputs.
Validate package metadata and distributable contents.
Test package installation/consumption in a clean environment.
Ensure generated assets and source maps follow policy.
Check bundle size and build output size.
Build Docker/OCI images.
Validate Dockerfile best practices.
Scan images for vulnerabilities.
Test container startup and health checks.
Verify the image runs as a non-root user where intended.
Verify container signal handling and graceful shutdown.
Test image architecture/platform targets.
Validate package and container provenance where required.
Ensure artifacts are linked to the exact source revision.
Avoid mutable/untraceable artifacts for production deployment.
Test installation from the published package registry in release workflows.
Test signing and verification for releases where used.
Confirm artifacts do not contain test secrets, credentials, or private data.
For published JS/TS libraries, run package-surface validation tools such as publint or @arethetypeswrong/cli when appropriate.
Validate package exports, main, module, types, and conditional ESM/CommonJS entry points.
Test .d.ts declarations under the supported TypeScript resolution modes.
Verify tree-shaking behavior and sideEffects metadata where the package promises it.
Run npm pack or the equivalent and test the actual packed artifact from a clean consumer project.
Check that package contents exclude tests, fixtures, private files, local configs, and secrets unless intentionally distributed.
For CLIs, test exit codes, stdout/stderr separation, machine-readable output, argument validation, signal handling, and non-interactive behavior.
For signed desktop/CLI binaries where applicable, validate code-signing, notarization, signatures, and published checksums.
18. Frontend, browser, and accessibility checks
Frontend compilation and type checks.
Linting and formatting for JS/TS, styles, templates, and markup.
Unit/component tests.
Production bundle-size budgets.
Broken links and missing asset checks.
Console error detection in browser tests.
Responsive layout checks.
Cross-browser tests for supported browsers.
Device viewport matrix tests.
Visual regression screenshots.
Semantic HTML checks.
Automated accessibility scanning.
Keyboard navigation tests.
Focus management tests for dialogs and navigation.
Form label, name, role, and error-association checks.
Color contrast checks.
Screen-reader smoke tests where feasible.
Reduced-motion behavior checks.
Zoom and reflow checks.
Captions/transcripts checks for media where applicable.
RTL and bidirectional-text layout tests where applicable.
Localization and translation completeness checks.
Validate ICU MessageFormat syntax, required placeholders, plural/select branches, and missing translations before runtime.
Run pseudo-localization layout tests with long strings to reveal truncation and overflow.
Validate public pages' <title>, meta description, canonical URL, robots directives, and social Open Graph/Twitter card metadata.
Validate robots.txt, XML sitemap syntax/content, canonical URL consistency, and indexable route coverage.
Ensure staging/preview environments are not accidentally indexable (for example via authentication or appropriate noindex/`X-Robots-Tag` policy) while production remains crawlable as intended.
Validate JSON-LD structured data syntax and schema for pages that emit structured data.
Test SEO tags on server-rendered output, not only after client-side JavaScript executes.
SSR/SSG/ISR output checks where used.
Hydration mismatch checks where relevant.
Route-level loading and error-state checks.
Third-party script impact checks where practical.
Browser storage quota and unavailable-API fallback tests.
Service-worker and offline checks for PWAs.
Verify that critical UI works without relying on color alone.
Ensure accessibility automation is complemented by manual review.
19. Performance and resource budgets
Frontend JavaScript bundle-size budget.
CSS and asset-size budget.
Image optimization and image-dimension checks.
Lighthouse or equivalent performance audit where reliable.
Core Web Vitals measurement where appropriate.
API latency smoke tests.
Critical endpoint p95/p99 latency checks where stable and meaningful.
Database query performance checks.
Memory and CPU usage checks.
Startup and cold-start measurements where relevant.
Build-time performance budgets where useful.
Detect excessive dependency growth.
Load tests for expected traffic.
Stress tests for capacity limits.
Spike tests for sudden traffic bursts.
Soak tests for sustained resource leaks.
Test realistic payload sizes and data volumes.
Test expensive query and search limits.
Validate caching behavior and cache hit ratios where practical.
Test third-party script and API impact.
Track performance regressions over time.
Use stable environments and noise thresholds to avoid flaky performance gates.
20. Concurrency, resilience, and reliability
Test concurrent writes and race conditions.
Test idempotent behavior during duplicate requests.
Test timeouts and cancellation.
Test retries with bounded backoff and jitter.
Test retry exhaustion and dead-letter behavior.
Test circuit-breaker behavior where used.
Test graceful degradation when dependencies are unavailable.
Test backpressure and queue overload behavior.
Test connection pool exhaustion behavior.
Test partial failure in multi-step workflows.
Test compensation/rollback for incomplete operations.
Test process termination during work.
Test graceful shutdown and draining.
Test load shedding and per-tenant limits.
Test duplicate and out-of-order events.
Test cache outage or stale-cache handling.
Test service restart and recovery.
Test readiness and liveness probe behavior.
Test failure alerts and incident runbooks periodically.
Run resilience or chaos tests in isolated environments where warranted.
21. Queues, jobs, events, and webhooks
Test job enqueueing and payload validation.
Test worker success and failure behavior.
Test retry policy and backoff.
Test idempotent job execution.
Test duplicate delivery and deduplication.
Test dead-letter queue routing and replay.
Test poison-message handling.
Test visibility/lease timeout and worker crash recovery.
Test job cancellation and progress updates.
Test scheduled jobs, time zones, daylight-saving changes, and missed runs.
Test event schema compatibility.
Test transactional outbox/inbox behavior where applicable.
Test queue backlog and throughput under load.
Test ordering requirements.
Test webhook signature and timestamp validation.
Test webhook replay protection.
Test duplicate webhook delivery.
Test missing, delayed, and out-of-order webhook events.
Test provider retry behavior and eventual reconciliation.
Test queue and job observability without leaking payload secrets.
22. External services and third-party integrations
Test provider adapter behavior with sandbox accounts or controlled fakes.
Test provider timeout and retry behavior.
Test rate limits and quota exhaustion.
Test invalid credentials and credential revocation.
Test malformed or unexpected provider responses.
Test provider outage and fallback behavior.
Test webhook verification and event reconciliation.
Validate provider schema/version assumptions.
Test integration health checks.
Confirm no production side effects occur in test workflows.
Test e-mail delivery integration with a non-production account/domain.
Check SPF/DKIM/DMARC configuration in suitable release or scheduled checks.
Test payment provider sandbox flows without using live credentials.
Test cloud storage upload/download permissions.
Test OAuth integration configuration and redirect URIs.
Monitor provider API deprecations and quota changes.
Keep external calls mocked in unit tests but use realistic integration tests for critical behavior.
23. Product-specific workflow tests
Payments and financial workflows
Successful payment, declined payment, pending payment, timeout, and cancellation.
Duplicate payment request and idempotency behavior.
Webhook signature verification and delayed/duplicate events.
Capture, settlement, refund, partial refund, dispute, and chargeback flows as applicable.
Currency, rounding, tax, fee, and exchange-rate calculations.
Ledger/audit record integrity.
Reconciliation against provider transactions.
Ensure client-reported success cannot authorize fulfillment.
E-commerce, inventory, and fulfillment
Product/variant/SKU validation.
Cart persistence, expiration, and merge behavior.
Price and inventory revalidation at checkout.
Concurrent checkout and oversell prevention.
Inventory reservation, release, adjustment, and reconciliation.
Order lifecycle transitions.
Separate order, payment, shipment, cancellation, and refund statuses.
Partial fulfillment, backorder, preorder, and split-shipment cases where supported.
Shipping, tax, coupon, promotion, and discount calculations.
Return, exchange, restock, and refund workflows.
Carrier webhook handling and shipment reconciliation.
Duplicate order submission protection.
Order support/admin views and audit history.
SaaS plans, subscriptions, and entitlements
Trial start and expiration.
Plan upgrades/downgrades and proration.
Cancellation, renewal, grace period, and reactivation.
Failed payment/dunning behavior.
Delayed, duplicate, and out-of-order billing webhooks.
Entitlement updates and server-side enforcement.
Seat limits, usage quotas, and overage behavior.
Invoice/tax/refund behavior where applicable.
Subscription/provider reconciliation.
Clear user-facing billing history and cancellation flows.
Multi-tenant applications
Cross-tenant read/write denial.
Cross-tenant search and export denial.
Tenant-aware cache keys.
Tenant-safe background jobs and event handling.
Tenant-aware quotas and noisy-neighbor limits.
Tenant provisioning, suspension, export, migration, and deletion.
Support/admin tools cannot accidentally cross tenant boundaries.
Tenant-specific configuration and data-residency rules where applicable.
Notifications and messaging
Template rendering and variable escaping.
Unsubscribe and consent enforcement.
Duplicate notification prevention.
Bounce, complaint, and suppression handling.
Push-token expiry and invalid token handling.
Localization and timezone rules.
Rate limiting and quiet hours.
Provider outage and retry behavior.
Avoid sensitive data in subject lines and lock screens.
File uploads and media processing
Validate uploaded file type, dimensions, size, and content in the end-to-end processing path.
Verify EXIF/GPS metadata is stripped from images when the product's privacy policy requires it.
Test malicious or malformed image/document handling and resource limits.
Validate transcoding output and media metadata when transcoding is supported.
Validate HLS/DASH master and media playlists, segment references, codecs, durations, and expected variants where applicable.
Verify private media URLs and access controls cannot leak cross-user or cross-tenant content.
Feature flags and experiment combinations
Run critical tests with important flags both ON and OFF.
Test high-risk combinations of flags and ensure defaults are safe.
Verify kill switches disable the intended behavior without corrupting in-flight work.
Confirm flags do not bypass server-side authorization or entitlement enforcement.
Search and content
Index creation, update, backfill, and deletion.
Reindex and recovery workflow.
Permission-aware search results.
Search query limits and abuse protection.
Empty results, typo tolerance, filtering, and sorting.
Sanitization of rich content and user-generated HTML.
Content workflow transitions and revision history.
Moderation/report/appeal/takedown flows where applicable.
Deleted or unauthorized content is not exposed by stale indexes or caches.
24. Mobile, PWA, and device testing
Native/hybrid mobile
Build for supported operating systems and architectures.
Unit and UI tests on supported versions/devices.
Deep link and universal/app link validation.
Secure local storage and token handling.
Lifecycle, backgrounding, interruption, and process-kill behavior.
Offline and intermittent network behavior.
Push permission, token rotation, and opt-out behavior.
Upgrade and local-data migration tests.
Crash and startup smoke tests.
Signing and package validation in protected release workflows.
Store metadata/privacy disclosure checks where automated checks exist.
Test permission denial and revocation.
Progressive web apps
Service-worker install and update.
Cache versioning and stale asset handling.
Offline fallback routes.
Offline mutation queue and conflict handling.
Private data isolation and logout cache clearing.
Web app manifest and required icons.
Background sync/push fallbacks across browsers.
Quota and storage eviction handling.
IoT or companion devices
Device provisioning and authentication tests.
Command authorization and validation.
Firmware/package signature verification.
Firmware upgrade and rollback tests.
Intermittent connectivity and synchronization.
Telemetry validation and privacy handling.
Stale command and safe-state behavior.
Device revocation and decommissioning.
25. Infrastructure-as-code and cloud configuration
Syntax validation for Terraform, Pulumi, CloudFormation, Kubernetes, or equivalent.
Format and lint checks.
Policy-as-code checks for insecure configuration.
Plan/diff review for infrastructure changes.
Detect public exposure of databases, buckets, and internal services.
Check least-privilege IAM and role assignments.
Validate encryption and TLS settings.
Validate backup policies and retention.
Validate network rules and ingress/egress.
Validate resource tags, naming, and environment separation.
Detect hardcoded secrets.
Scan container and infrastructure images/configurations.
Test generated configuration and deployment manifests.
Validate health checks, autoscaling, and resource limits.
Verify infrastructure drift where supported.
Ensure CI plan steps do not apply production changes without explicit protected approval.
Test policy checks with intentionally insecure sample configurations.
Validate DNS and certificate configuration where feasible.
Estimate cloud-cost changes from infrastructure plans on pull requests (for example, Terraform/Pulumi plan deltas) where supported.
Surface estimated monthly cost increases/decreases and identify newly created high-cost resources.
Set review thresholds for large cost deltas; do not automatically apply infrastructure plans just to estimate cost.
Include often-overlooked resources such as NAT gateways, unattached/public IPs, idle databases, snapshots, egress, and oversized instances where the estimator supports them.
26. Documentation and developer experience
Markdown linting.
Spell checking for docs where useful.
Broken internal-link checking.
Broken external-link checking, preferably scheduled to avoid network flakes.
README and setup command validation.
Code examples compile/run where practical.
API documentation generation and validation.
Ensure generated docs are up to date.
Validate architecture and infrastructure diagrams where tooling permits.
Validate environment example files.
Test local bootstrap scripts in a clean runner/container.
Validate release notes/changelog.
Validate license and third-party notice files.
Check for deprecated commands or package references in docs.
Ensure runbooks list current command names and system ownership.
27. Data privacy, analytics, and compliance checks
Detect obvious personal data or secrets in logs and test artifacts.
Validate data-retention and deletion behavior.
Test account data export and deletion where required.
Check consent/opt-out enforcement for analytics and marketing.
Validate cookie or tracking-consent behavior where applicable.
Check analytics event schemas and required fields.
Detect duplicate or malformed event definitions.
Check that analytics does not include credentials or sensitive fields.
Validate data access and tenant isolation in reports/exports.
Check privacy notices, terms, or compliance documents are present where required.
Validate data processor/subprocessor configuration where tooling supports it.
Check retention settings for logs, recordings, traces, and analytics datasets.
Ensure test datasets are synthetic or appropriately sanitized.
Validate regulatory controls with qualified reviewers; CI checks alone do not prove legal compliance.
Data warehouse, ETL, dbt, and analytics pipeline CI
Run slim/affected CI for modified SQL models and their downstream dependents where the framework supports it.
Validate data-pipeline DAGs and detect circular dependencies.
Run SQL/model linting and compile-time validation.
Run source freshness, schema, uniqueness, not-null, referential-integrity, and business-rule tests where appropriate.
Detect schema drift between operational sources, ingestion layers, and warehouse models.
Validate data contracts and compatibility for upstream/downstream consumers.
Validate column-level classification/tags for PII or other sensitive data.
Check that sensitive columns are masked or access-restricted in non-production and analytical environments.
Verify lineage and impact analysis identify downstream models/reports affected by a change.
Test incremental models, late-arriving data, duplicate records, and backfills.
Keep CI fixtures small and synthetic; reserve full warehouse refreshes for suitable scheduled or isolated runs.
28. AI/ML and agentic-system tests
Validate model/provider configuration.
Validate prompt and template syntax.
Run evaluation datasets for quality, correctness, and regression.
Test refusal and unsafe-output behavior.
Test prompt-injection resistance.
Test tool permission boundaries and argument validation.
Ensure the model cannot grant itself authorization.
Test retrieval access controls and prevent cross-user/tenant leakage.
Test sensitive-data leakage from prompts, retrieved content, and responses.
Test output schema validation and malformed model responses.
Test timeout, retry, and provider outage behavior.
Test model fallback and version changes.
Test token, execution-step, recursion, and tool-call limits.
Test hard per-user, per-tenant, and global budget limits.
Test runaway-cost kill switches and circuit breakers.
Test human confirmation for consequential actions.
Test data retention, deletion, opt-out, and model-training settings as applicable.
Track content/source provenance and intellectual-property policy where relevant.
Test safety and performance against adversarial and edge-case inputs.
Version prompts, models, tools, and evaluation datasets.
Avoid relying on exact string matches for inherently nondeterministic outputs; use robust assertions.
29. Advanced testing techniques
Property-based testing for invariants over generated inputs.
Fuzz testing for parsers, serializers, protocols, and complex input surfaces.
Mutation testing to measure test-suite fault detection.
Differential testing between old and new implementations.
Metamorphic testing where a direct expected answer is difficult to define.
Snapshot/record-replay testing for complex integrations where appropriate.
Shadow-traffic replay in isolated environments.
Canary analysis comparing error rates, latency, and business metrics.
Chaos testing in non-production or tightly controlled environments.
Fault injection for network delay, dependency errors, and resource exhaustion.
Long-running soak tests.
High-volume load tests.
Regional failover and disaster-recovery exercises.
Backup restoration drills.
Data reconciliation and drift detection.
AI evaluation and adversarial testing.
Flaky-test detection across repeated runs.
Randomized test ordering to detect shared-state dependence.
Test sharding and parallel execution correctness.
Ensure high-cost or destructive experiments require protected environments and explicit controls.
30. Deployment and release verification
Deploy to an isolated preview environment where useful.
Deploy to staging using the intended release artifact.
Verify the deployed version matches the source commit/artifact.
Verify required environment variables and configuration.
Verify TLS, domains, routing, and redirect behavior.
Verify health and readiness endpoints.
Run post-deployment smoke tests.
Run critical end-to-end journeys against the deployed system.
Verify database migrations and job/worker compatibility.
Check logs for startup errors.
Verify required integrations and webhooks are reachable.
Validate scheduled tasks and worker processing.
Verify cache invalidation and frontend assets after release.
Test feature-flag defaults and emergency kill switches.
Verify rollback or roll-forward instructions.
Run progressive rollout health checks for canary/blue-green deployments.
Require approvals for production deployment where appropriate.
Ensure releases are traceable and artifacts cannot be silently replaced.
Publish release notes or changelog where required.
Run post-release monitoring and define rollback criteria.
31. Observability and operational readiness
Validate structured logging setup.
Verify correlation/request IDs propagate through critical flows.
Validate metrics and dashboards are present.
Verify traces for important cross-service operations where used.
Ensure sensitive fields are redacted.
Check alert rules for syntax and expected thresholds.
Verify alert routes and notification integrations.
Validate health checks and dependency readiness.
Test queue-lag, failed-job, and dead-letter alerts.
Test database saturation and error alerts.
Verify frontend error reporting where applicable.
Verify status-page and customer-notification workflows where appropriate.
Ensure runbooks exist for critical alerts.
Check log/metric cardinality and expected ingestion volume.
Test alerting with controlled faults in a non-production environment.
Confirm ownership for critical services and alerts.
32. CI performance, quality, and maintenance
Track workflow duration.
Track queue time and runner utilization.
Track flake rate and repeated test failures.
Track failure causes and time to diagnose.
Avoid unnecessary duplicate dependency installation.
Cache dependencies safely without trusting untrusted cache content.
Keep cache keys scoped to meaningful inputs (OS, runtime, lockfiles, architecture, and build configuration as applicable).
Avoid sharing executable build caches across trust boundaries; verify restored binaries/artifacts and prefer caching package-manager downloads over generated executables when risk is unclear.
Monitor cache usage, churn, and eviction; GitHub's documented repository cache limit can change, so verify current platform policy.
Parallelize independent jobs where it improves total duration.
Use explicit matrix settings (including fail-fast) and include the supported OS, architecture, timezone, and locale dimensions relevant to the product.
Run date/time-sensitive tests under UTC and at least one non-UTC offset when timezone behavior is important.
Record the matrix dimension that failed so platform-specific regressions are easy to diagnose.
Split large test suites into shards where appropriate.
Upload useful test reports and failure artifacts.
Keep artifact retention proportionate to debugging and compliance needs.
Define job and workflow timeouts.
Avoid excessively broad path filters and skipped required checks.
Ensure caches do not cause stale or non-reproducible builds.
Periodically update and validate action versions.
Remove unused workflows, secrets, environments, and runners.
Review self-hosted runner isolation and cleanup if used.
Ensure untrusted jobs cannot persist malicious state on shared runners.
Use ephemeral runners for sensitive workloads where practical.
Document required checks and how to reproduce them locally.
Ensure each required check has a clear owner and remediation path.
33. Suggested workflow tiers
Tier A — Every pull request (fast, high signal)
Dependency installation from lockfile.
Formatting check.
Linting.
Type checking/compilation.
Unit tests.
Core integration tests.
Production build.
Secret scanning.
Dependency vulnerability scan or dependency review.
Workflow and infrastructure configuration linting where changed.
API/schema/contract validation where relevant.
Fast accessibility/component tests for critical UI.
Minimal E2E smoke test for the most important flow where practical.
Required status checks enforced by branch rules.
Include merge_group when using merge queues.
Validate monorepo affected-graph selection, with a safe full-CI fallback if graph calculation is uncertain.
Hermetic unit/component tests do not make unexpected external network calls.
Tier B — Protected branch, merge, or nightly
Full integration suite.
Full E2E suite.
Broader browser/device matrix.
Visual regression suite.
Full security scans.
Database migration and backward-compatibility tests.
Container build and image scan.
License and SBOM checks where required.
Broader accessibility checks.
Flaky-test and randomized-order checks.
Dependency update and end-of-life reporting.
Documentation link checks.
Monorepo affected-graph and downstream-package checks.
GraphQL schema breaking-change diff where applicable.
Package/SDK/CLI artifact validation where applicable.
SEO metadata and sitemap checks for public websites.
Data pipeline slim CI, lineage, schema drift, and PII classification checks where applicable.
Cloud cost diff review for infrastructure changes where applicable.
Tier C — Scheduled, pre-release, or staging
DAST against an isolated environment.
Load, stress, spike, and soak tests.
Fuzz and property-based tests beyond the fast PR budget.
Mutation testing selectively.
Disaster-recovery and restore drills.
Chaos/fault-injection tests.
Multi-region failover tests where required.
Deep mobile/device matrix tests.
Shadow traffic or canary analysis.
AI adversarial, quality, and cost-limit evaluations.
Data reconciliation and analytics quality checks.
End-to-end release/rollback rehearsal.
34. Final merge and release gates
Before merging a pull request
All required CI checks passed.
Code review and any required specialist approvals are complete.
No unresolved high-risk security finding remains without explicit, documented risk acceptance.
Tests cover the important behavior changed by the PR.
Database migrations and API/event changes are backward compatible with the rollout strategy.
Secrets, private data, and unintended artifacts are not included.
Required documentation and release notes are updated.
Changes to workflow permissions or release controls have been reviewed.
Known failures or skipped tests are explained and assigned.
Before a production release
The release artifact is traceable to reviewed source.
Required security, license, and supply-chain checks passed.
Migrations and data changes have a tested recovery strategy.
Staging smoke and critical E2E tests passed.
Performance and capacity assumptions are acceptable.
Monitoring, dashboards, alerts, and runbooks are ready.
Backup and recovery expectations are met.
Deployment, rollback, and kill-switch procedures are ready.
Production credentials and environment protections are correctly configured.
Customer support, incident contacts, and release communications are prepared.
Post-deployment verification and rollback thresholds are defined.
Exceptions have named owners and review dates.
Example repository layout
A typical repository may organize workflows and automation configuration like this:
.github/ CODEOWNERS # Place under .github/ or repository root dependabot.yml # Or use renovate.json for Renovate actions/ # Versioned composite actions shared by workflows setup-project/ action.yml workflows/ ci.yml # Required PR/push checks; include merge_group if needed e2e.yml # Browser/end-to-end tests security.yml # Security and dependency scans scheduled.yml # Nightly/weekly slower checks reusable-test.yml # Example reusable workflow using workflow_call release.yml # Protected release/deployment workflow
CODEOWNERS may live at the repository root, .github/, or docs/; ensure the configured path is recognized by GitHub and protected by branch rules. A smaller project can keep checks in one workflow. Split files when permissions, triggers, environments, reuse, or runtime costs differ. Local composite actions should declare inputs/outputs and be reviewed like code; reusable workflows should have explicit inputs, secrets, and permissions.
Important implementation notes
A checklist is not a workflow by itself. Choose the applicable checks and implement them using your language, test runner, dependency manager, and deployment platform.
Do not run destructive tests against production. Use disposable databases, sandbox providers, preview environments, and synthetic data.
Keep required PR CI deterministic. Avoid brittle network-dependent checks in the merge-critical path unless they have controlled dependencies and reliable behavior.
Security scans need triage. Define severity thresholds, ownership, and exceptions instead of silently ignoring findings.
Do not rely on CI alone. Production readiness also requires monitoring, incident response, access reviews, backups, recovery drills, and appropriate human review.
A green build is evidence, not proof. Combine automated checks with code review, threat modeling, production monitoring, and periodic operational exercises.
GitHub Actions and tooling references
GitHub-hosted platform behavior, action inputs, security guidance, cache policies, and runner support evolve. Verify the current official documentation before enforcing a platform-specific assumption.
[GitHub Actions: Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
[GitHub Actions: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
[GitHub Actions: Workflow commands (GITHUB_ENV, GITHUB_OUTPUT, and GITHUB_PATH)](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands)
[GitHub Actions: Dependency caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
[actions/checkout repository and version-specific behavior](https://github.com/actions/checkout)
[actions/cache repository and current cache limits](https://github.com/actions/cache)
[Nx affected commands](https://nx.dev/ci/features/affected)
[Turborepo filtering](https://turbo.build/repo/docs/crafting-your-repository/running-tasks)
[Bazel test/build documentation](https://bazel.build/docs)
[publint package validation](https://publint.dev/)
[Are The Types Wrong?](https://arethetypeswrong.github.io/)
[Infracost](https://www.infracost.io/)
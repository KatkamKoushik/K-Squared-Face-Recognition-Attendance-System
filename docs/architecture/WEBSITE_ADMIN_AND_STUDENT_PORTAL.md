# Website Architecture: Student Enrollment Portal & Admin Console
**FRS V7.1 K² Architecture Documentation**  
*Status: IMPLEMENTED & VERIFIED*

---

## 1. Overview & Routing Architecture

The Next.js web application (`apps/admin_console`) serves dual roles within the institutional infrastructure:
1. **Public Student Enrollment Portal (`/`):** A responsive, mobile-first onboarding interface allowing enrolled students to register their details, capture or upload high-resolution biometric portraits, review data privacy disclosures, provide informed consent, and submit applications for verification.
2. **Protected Institutional Admin Console (`/admin/*`):** An authenticated workspace for authorized faculty, department heads, and system administrators to monitor attendance operations, inspect pending biometric enrollment submissions, review photo quality, and approve or reject submissions.

### Routing Table

| Route | Access Level | Description |
|---|---|---|
| `/` | Public | Student enrollment application form with live camera capture & consent agreement |
| `/login` | Public | Authentication portal with institutional role redirection |
| `/admin` | Protected (`ADMIN`, `FACULTY`) | Institutional KPI dashboard, live system health, and quick actions |
| `/admin/enrollment` | Protected (`ADMIN`, `FACULTY`) | Biometric verification queue, portrait inspection, and approval actions |
| `/admin/login` | Public | Direct administrative login portal |
| `/students` | Protected (`ADMIN`, `FACULTY`) | Live database-backed institutional student directory |
| `/sessions` | Protected (`ADMIN`, `FACULTY`) | Attendance session monitoring and audits |
| `/reports` | Protected (`ADMIN`, `FACULTY`) | Institutional attendance analytics and export |
| `/settings` | Protected (`ADMIN`) | System configuration and security settings |

---

## 2. Public Student Enrollment Portal (`/`)

### 2.1 Interface & User Experience
The public portal is engineered mobile-first to accommodate student submissions on smartphones as well as desktop browsers:
- **Identity Fields:** Student Roll Number (institutional unique index), Legal First Name, Last Name, Official Email Address, and Academic Department.
- **Biometric Photo Ingestion:**
  - Integrated HTML5 camera capture via `MediaDevices.getUserMedia()` with front-facing camera selection (`facingMode: "user"`).
  - Drag-and-drop or file picker for existing high-resolution portrait files (`image/jpeg`, `image/png`).
  - Real-time client-side preview with retake and remove controls.
- **Biometric Notice & Informed Consent:**
  - Clear disclosure regarding face recognition usage for attendance, feature vector extraction, 128-D embedding storage, and data retention policies.
  - Required checkbox acceptance linked to consent policy version `2026.1-v1`.
- **Submission Feedback:**
  - Async state machine (`idle` -> `submitting` -> `success` / `error`).
  - Upon submission, displays tracking UUID, roll number, and status (`PENDING`).
  - Explicit error handling displaying server-side validation issues (e.g. roll number already registered, no face detected in image, image corrupted).

### 2.2 Security & Data Hygiene
- **Client-Side Validation:** Enforces non-empty fields, email regex format, and file size limits before transmission.
- **Transport Security:** Submissions are transmitted via multipart `FormData` over TLS to `POST /api/v1/enrollment/submit`.
- **No Client-Side Secrets:** The public portal utilizes no privileged API keys; all public actions communicate strictly with the open submit endpoint.

---

## 3. Protected Institutional Admin Console (`/admin`)

### 3.1 Authentication & Session Management
- **Token Mechanism:** Administrative endpoints require JSON Web Tokens (JWT) signed by the backend using HMAC-SHA256.
- **Client Storage:** Tokens and active user role profiles are persisted securely in `localStorage` under keys `auth_token` and `user_role`.
- **Route Protection:** `AppShell` and page components evaluate token existence and expiration; unauthorized requests redirect to `/admin/login`.
- **Session Expiration:** Expired tokens trigger automatic redirection to the login screen with a session timeout notification.

### 3.2 Live Institutional Dashboard (`/admin`)
Unlike legacy demo prototypes, the dashboard communicates directly with backend database queries via `GET /api/v1/enrollment/dashboard-stats` and `/api/v1/health/readiness`:
- **Total Registered Students:** Count of active students in `students` table.
- **Pending Review Queue:** Live count of submissions in `enrollment_submissions` with `status = 'PENDING'`.
- **Approved Profiles:** Count of approved student enrollment submissions.
- **Active Offerings:** Count of academic subject offerings currently conducting sessions.
- **System Health Status:** Live readiness status querying physical ONNX model availability on disk and database connection status.

---

## 4. Biometric Verification Queue (`/admin/enrollment`)

```
+---------------------------------------------------------------------------------------+
|  Pending Review (5)   |   Approved (142)   |   Recapture Required (3)   |   Rejected (1)  |
+---------------------------------------------------------------------------------------+
| [Photo]  Roll No: 23CSE042                                                            |
|          Name: Priya Patel                                                            |
|          Department: Computer Science & Engineering                                   |
|          Submitted: 10 Nov 2026, 08:30 IST                                            |
|          Consent: Verified (v2026.1-v1)                                               |
|                                                                                       |
|  [ ✓ Approve & Enroll ]    [ ⟳ Request Recapture ]    [ ✕ Reject Submission ]         |
+---------------------------------------------------------------------------------------+
```

### 4.1 Queue Features
- **Status Filter Tabs:** Switch between `PENDING`, `APPROVED`, `RECAPTURE_REQUIRED`, and `REJECTED`.
- **Authenticated Photo Streaming:** Student photos are fetched dynamically via `GET /api/v1/enrollment/submissions/{id}/photo` using `Authorization: Bearer <token>`, preventing unauthorized public photo harvesting.
- **Review Actions:**
  - **Approve:** Invokes `POST /api/v1/enrollment/submissions/{id}/approve`. Triggers synchronous YOLOv8n-Face landmark alignment, SFace feature extraction, L2-normalization, and upserts into `students` and `student_embeddings`.
  - **Request Recapture:** Invokes `POST /api/v1/enrollment/submissions/{id}/recapture` with review notes (e.g., "Image too blurry, please retake in well-lit area").
  - **Reject:** Invokes `POST /api/v1/enrollment/submissions/{id}/reject` with rationale (e.g., "Photograph contains multiple individuals").

---

## 5. Directory Verification (`/students`)
The student directory (`apps/admin_console/app/students/page.tsx`) queries `GET /api/v1/academic/students` with authorization headers. All hardcoded mock student lists (`mockStudents`) have been removed; the table renders live records from PostgreSQL or displays an empty state when no students have been enrolled.

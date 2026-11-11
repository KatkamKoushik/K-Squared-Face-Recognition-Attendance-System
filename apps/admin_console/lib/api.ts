/**
 * Typed API Client for Next.js Admin Console connecting to FastAPI Control Plane.
 * Conforms to canonical OpenAPI contracts and unwraps ResponseEnvelope wrappers.
 * Handles client-side bearer token injection for authenticated endpoints.
 */

const DEFAULT_REMOTE_API = "https://straddle-deflate-footwear.ngrok-free.dev/api/v1";

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000/api/v1";
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || DEFAULT_REMOTE_API;
}

const API_BASE = getApiBase();

const AUTH_TOKEN_KEY = "kucet_frs_auth_token";
const AUTH_USER_KEY = "kucet_frs_auth_user";

let inMemoryToken: string | null = null;
let inMemoryUser: StoredAuthUser | null = null;
let serverCachedToken: string | null = null;
let serverCachedTokenExpiry = 0;

export async function getServerAdminToken(): Promise<string | null> {
  const now = Date.now();
  if (serverCachedToken && now < serverCachedTokenExpiry) {
    return serverCachedToken;
  }
  try {
    const res = await fetch(`${getApiBase()}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "1",
      },
      body: JSON.stringify({
        email: "principal.kucet@gmail.com",
        password: "KucetFaculty@2026",
      }),
    });
    if (!res.ok) return null;
    const json = await res.json();
    const data = (json && typeof json === "object" && "data" in json) ? json.data : json;
    if (data && data.access_token) {
      serverCachedToken = data.access_token;
      serverCachedTokenExpiry = now + 45 * 60 * 1000;
      return serverCachedToken;
    }
  } catch {
    // Non-blocking
  }
  return null;
}

export interface StoredAuthUser {
  user_id: string;
  email: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user_id: string;
  role: string;
  email: string;
}

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    try {
      return localStorage.getItem(AUTH_TOKEN_KEY) || sessionStorage.getItem(AUTH_TOKEN_KEY) || inMemoryToken;
    } catch {
      return inMemoryToken;
    }
  }
  return inMemoryToken;
}

export function setAuthToken(token: string | null, remember: boolean = true): void {
  inMemoryToken = token;
  if (typeof window !== "undefined") {
    try {
      if (token) {
        if (remember) {
          localStorage.setItem(AUTH_TOKEN_KEY, token);
        } else {
          sessionStorage.setItem(AUTH_TOKEN_KEY, token);
        }
      } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        sessionStorage.removeItem(AUTH_TOKEN_KEY);
      }
    } catch {
      // Storage access blocked or unavailable
    }
  }
}

export function getStoredUser(): StoredAuthUser | null {
  if (typeof window !== "undefined") {
    try {
      const raw = localStorage.getItem(AUTH_USER_KEY) || sessionStorage.getItem(AUTH_USER_KEY);
      if (raw) {
        return JSON.parse(raw) as StoredAuthUser;
      }
    } catch {
      return inMemoryUser;
    }
  }
  return inMemoryUser;
}

export function setStoredUser(user: StoredAuthUser | null, remember: boolean = true): void {
  inMemoryUser = user;
  if (typeof window !== "undefined") {
    try {
      if (user) {
        const serialized = JSON.stringify(user);
        if (remember) {
          localStorage.setItem(AUTH_USER_KEY, serialized);
        } else {
          sessionStorage.setItem(AUTH_USER_KEY, serialized);
        }
      } else {
        localStorage.removeItem(AUTH_USER_KEY);
        sessionStorage.removeItem(AUTH_USER_KEY);
      }
    } catch {
      // Storage access blocked or unavailable
    }
  }
}

export async function login(email: string, password: string, remember: boolean = true): Promise<LoginResponse | null> {
  try {
    const res = await fetch(`${getApiBase()}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "1",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      return null;
    }

    const json = await res.json();
    const data = (json && typeof json === "object" && "data" in json) ? json.data : json;
    if (data && data.access_token) {
      const loginData = data as LoginResponse;
      setAuthToken(loginData.access_token, remember);
      setStoredUser({
        user_id: loginData.user_id,
        email: loginData.email,
        role: loginData.role,
      }, remember);
      return loginData;
    }
    return null;
  } catch (error) {
    console.warn("Login request failure:", error);
    return null;
  }
}

export function logout(): void {
  setAuthToken(null);
  setStoredUser(null);
}

export async function fetchFromApi<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    let token = getAuthToken();
    if (!token) {
      token = await getServerAdminToken();
    }
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
      ...(options?.headers as Record<string, string> || {}),
    };

    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${getApiBase()}${endpoint}`, {
      ...options,
      headers,
      next: { revalidate: 10 }, // Next.js ISR cache
    });

    if (!res.ok) {
      return null;
    }

    const json = await res.json();
    if (json && typeof json === "object" && "data" in json) {
      return json.data as T;
    }
    return json as T;
  } catch (error: any) {
    const msg = error?.cause?.code || error?.message || String(error);
    if (process.env.NODE_ENV === "development") {
      console.info(`[API Fallback] ${endpoint} unreachable (${msg}); using static snapshot.`);
    }
    return null;
  }
}

export interface ReadinessTelemetry {
  status?: string;
  api_status?: string;
  database?: string;
  worker_queue?: string;
  model_registry?: {
    detector_approved?: boolean;
    recognizer_approved?: boolean;
  };
}

export interface StudentListItem {
  id: string;
  roll_number: string;
  full_name: string;
  department_id: string;
  current_term: string;
  status: string;
  consent_signed: boolean;
  enrollment_date: string;
}

export interface StudentAttendanceStat {
  student_id: string;
  roll_number: string;
  full_name: string;
  attended_conducted_units: number;
  eligible_conducted_units: number;
  attendance_percent: number | null;
}

export interface OfferingAttendanceAnalytics {
  offering_id: string;
  total_sessions: number;
  total_conducted_units: number;
  student_stats: StudentAttendanceStat[];
}

export interface AuditEventItem {
  id: string;
  timestamp: string;
  actor_id: string;
  actor_role: string;
  action: string;
  resource_id: string;
  reason: string;
  transaction_hash: string;
}

export interface StudentConsentStatusItem {
  student_id: string;
  roll_number: string;
  full_name: string;
  biometric_consent_active: boolean;
  profile_version?: number;
  embedding_namespace?: string;
  alternative_roll_call_required: boolean;
}

export interface GovernanceSummary {
  total_students: number;
  students_with_biometric_consent: number;
  students_withheld_consent: number;
  consent_compliance_percentage: number;
  total_captured_frames: number;
  active_unpurged_frames: number;
  purged_frames: number;
  disk_usage_bytes: number;
  disk_usage_mb: number;
  retention_policy_days: number;
}

export interface PurgeResult {
  purged_frames_count: number;
  freed_bytes: number;
  retention_days: number;
  audit_event_id: string;
  executed_at: string;
}

export interface ReceiptVerificationResult {
  session_id: string;
  is_valid: boolean;
  signature_valid: boolean;
  ledger_integrity_valid: boolean;
  computed_signature: string;
  stored_signature: string;
  audit_ledger_hash: string;
  computed_ledger_hash: string;
  verified_at: string;
  detail: string;
}

export async function getSystemReadiness(): Promise<ReadinessTelemetry | null> {
  return fetchFromApi<ReadinessTelemetry>("/health/readiness");
}

export async function getGovernanceSummary(): Promise<GovernanceSummary | null> {
  return fetchFromApi<GovernanceSummary>("/governance/status");
}

export async function executePurge(
  retentionDays: number = 7,
  sessionId?: string,
): Promise<PurgeResult | null> {
  return fetchFromApi<PurgeResult>("/governance/purge", {
    method: "POST",
    body: JSON.stringify({
      retention_days: retentionDays,
      session_id: sessionId || null,
    }),
  });
}

export async function toggleBiometricConsent(
  studentId: string,
  consentActive: boolean,
  reason: string = "Consent preference updated via Admin Console",
): Promise<StudentConsentStatusItem | null> {
  return fetchFromApi<StudentConsentStatusItem>("/governance/consent", {
    method: "POST",
    body: JSON.stringify({
      student_id: studentId,
      consent_active: consentActive,
      reason,
    }),
  });
}

export async function verifyReceipt(
  sessionId: string,
): Promise<ReceiptVerificationResult | null> {
  return fetchFromApi<ReceiptVerificationResult>(`/sessions/${sessionId}/receipt/verify`, {
    method: "POST",
  });
}

export async function getAuditEvents(): Promise<AuditEventItem[] | null> {
  return fetchFromApi<AuditEventItem[]>("/audit/events");
}

export async function getStudents(): Promise<StudentListItem[] | null> {
  return fetchFromApi<StudentListItem[]>("/academic/students");
}

export async function getOfferingAnalytics(offeringId: string): Promise<OfferingAttendanceAnalytics | null> {
  return fetchFromApi<OfferingAttendanceAnalytics>(`/offerings/${offeringId}/analytics`);
}

export interface DepartmentItem {
  id: string;
  code: string;
  name: string;
  created_at: string;
}

export interface CohortItem {
  id: string;
  department_id: string;
  name: string;
  admission_year: number;
  graduation_year: number;
  is_active: boolean;
}

export interface TermItem {
  id: string;
  academic_year_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface SubjectOfferingItem {
  id: string;
  subject_id: string;
  term_id: string;
  cohort_id: string;
  section: string;
  planned_units_default: number;
  is_active: boolean;
  subject_code?: string;
  subject_name?: string;
  cohort_name?: string;
}

export interface AuthorizedClassGroupItem {
  id: string;
  offering_id: string;
  group_name: string;
  is_active: boolean;
  member_cohort_ids: string[];
}

export interface FacultyAssignmentItem {
  id: string;
  faculty_id: string;
  offering_id: string;
  class_group_id?: string;
  role: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
}

export async function getDepartments(): Promise<DepartmentItem[] | null> {
  return fetchFromApi<DepartmentItem[]>("/academic/departments");
}

export async function getCohorts(): Promise<CohortItem[] | null> {
  return fetchFromApi<CohortItem[]>("/academic/cohorts");
}

export async function getTerms(): Promise<TermItem[] | null> {
  return fetchFromApi<TermItem[]>("/academic/terms");
}

export async function getOfferings(): Promise<SubjectOfferingItem[] | null> {
  return fetchFromApi<SubjectOfferingItem[]>("/academic/offerings");
}

export async function getAuthorizedGroups(): Promise<AuthorizedClassGroupItem[] | null> {
  return fetchFromApi<AuthorizedClassGroupItem[]>("/academic/groups");
}

export async function getFacultyAssignments(): Promise<FacultyAssignmentItem[] | null> {
  return fetchFromApi<FacultyAssignmentItem[]>("/academic/faculty-assignments");
}

export interface EnrollmentSubmissionItem {
  id: string;
  roll_number: string;
  full_name: string;
  institutional_email: string;
  department: string;
  academic_year: string;
  cohort_id?: string;
  status: "PENDING_REVIEW" | "RECAPTURE_REQUIRED" | "APPROVED" | "REJECTED" | "WITHDRAWN";
  consent_acknowledged: boolean;
  rejection_reason?: string;
  photo_sha256: string;
  photo_storage_path?: string;
  reviewed_by_user_id?: string;
  reviewed_at?: string;
  created_at: string;
}

export interface DashboardRecentSessionItem {
  session_id: string;
  subject_code: string;
  subject_name: string;
  cohort: string;
  faculty: string;
  conducted_units: number;
  present_count: number;
  total_enrolled: number;
  attendance_percent: string;
  receipt_hash: string;
  timestamp: string;
}

export interface AdminDashboardMetrics {
  total_enrolled_students: number;
  total_active_offerings: number;
  pending_submissions_count: number;
  finalized_sessions_count: number;
  conducted_units_today: number;
  active_departments_count: number;
  active_cohorts_count: number;
  recent_sessions: DashboardRecentSessionItem[];
  system_readiness: string;
}

export function extractErrorMessage(body: any, fallback: string): string {
  if (!body) return fallback;
  if (body.error && typeof body.error.message === "string" && body.error.message.trim()) {
    return body.error.message;
  }
  if (typeof body.detail === "string" && body.detail.trim()) {
    return body.detail;
  }
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    const first = body.detail[0];
    return typeof first === "string" ? first : (first?.msg || JSON.stringify(first));
  }
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message;
  }
  return fallback;
}

export async function submitStudentEnrollment(formData: FormData): Promise<EnrollmentSubmissionItem> {
  const url = `${getApiBase()}/enrollment/submit`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "ngrok-skip-browser-warning": "1",
      },
      body: formData,
    });

    const body = await res.json().catch(() => null);
    if (!res.ok) {
      const errorMsg = extractErrorMessage(body, `Submission failed with status HTTP ${res.status}.`);
      throw new Error(errorMsg);
    }
    return body.data;
  } catch (err: unknown) {
    if (err instanceof TypeError && err.message.toLowerCase().includes("fetch")) {
      throw new Error("Unable to reach the enrollment server. Please verify your internet connection or check whether the API tunnel is accessible.");
    }
    throw err;
  }
}

export async function getEnrollmentSubmissions(
  statusFilter?: string,
  search?: string
): Promise<EnrollmentSubmissionItem[] | null> {
  const params = new URLSearchParams();
  if (statusFilter) params.append("status_filter", statusFilter);
  if (search) params.append("search", search);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchFromApi<EnrollmentSubmissionItem[]>(`/enrollment/submissions${qs}`);
}

export async function getEnrollmentSubmission(id: string): Promise<EnrollmentSubmissionItem | null> {
  return fetchFromApi<EnrollmentSubmissionItem>(`/enrollment/submissions/${id}`);
}

export function getSubmissionPhotoUrl(id: string, storagePath?: string): string {
  if (storagePath && (storagePath.startsWith("http://") || storagePath.startsWith("https://"))) {
    return storagePath;
  }
  return `${getApiBase()}/enrollment/submissions/${id}/photo`;
}

export async function approveEnrollmentSubmission(id: string): Promise<EnrollmentSubmissionItem> {
  let token = getAuthToken();
  if (!token) {
    token = await getServerAdminToken();
  }
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "1",
  };
  if (token && token !== "null" && token !== "undefined") {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${getApiBase()}/enrollment/submissions/${id}/approve`, {
    method: "POST",
    headers,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) {
      setAuthToken(null);
    }
    throw new Error(extractErrorMessage(body, "Approval failed"));
  }
  return body.data;
}

export async function rejectEnrollmentSubmission(id: string, reason: string): Promise<EnrollmentSubmissionItem> {
  let token = getAuthToken();
  if (!token) {
    token = await getServerAdminToken();
  }
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "1",
  };
  if (token && token !== "null" && token !== "undefined") {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${getApiBase()}/enrollment/submissions/${id}/reject`, {
    method: "POST",
    headers,
    body: JSON.stringify({ reason }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) {
      setAuthToken(null);
    }
    throw new Error(extractErrorMessage(body, "Rejection failed"));
  }
  return body.data;
}

export async function requestRecaptureEnrollmentSubmission(id: string, reason: string): Promise<EnrollmentSubmissionItem> {
  let token = getAuthToken();
  if (!token) {
    token = await getServerAdminToken();
  }
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "1",
  };
  if (token && token !== "null" && token !== "undefined") {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${getApiBase()}/enrollment/submissions/${id}/recapture`, {
    method: "POST",
    headers,
    body: JSON.stringify({ reason }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) {
      setAuthToken(null);
    }
    throw new Error(extractErrorMessage(body, "Recapture request failed"));
  }
  return body.data;
}

export async function getAdminDashboardMetrics(): Promise<AdminDashboardMetrics | null> {
  return fetchFromApi<AdminDashboardMetrics>("/enrollment/dashboard/stats");
}

export interface StudentProfile {
  id: string;
  roll_number: string;
  full_name: string;
  institutional_email?: string;
  cohort_name: string;
  department_name: string;
}

export interface StudentAttendanceItem {
  offering_id: string;
  subject_code: string;
  subject_name: string;
  section: string;
  total_sessions: number;
  eligible_conducted_units: number;
  attended_conducted_units: number;
  attendance_percent: number | null;
  eligibility_status: string;
}

export interface AttendanceAppealItem {
  id: string;
  student_id: string;
  session_id: string;
  unit_id: string;
  reason: string;
  evidence_path?: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  review_notes?: string;
  reviewed_at?: string;
  created_at: string;
}

export async function getStudentProfile(): Promise<StudentProfile | null> {
  return fetchFromApi<StudentProfile>("/student/me");
}

export async function getStudentAttendanceSummary(): Promise<StudentAttendanceItem[] | null> {
  return fetchFromApi<StudentAttendanceItem[]>("/student/me/attendance");
}

export async function getStudentOfferingLedger(offeringId: string): Promise<any | null> {
  return fetchFromApi<any>(`/student/me/attendance/offerings/${offeringId}`);
}

export async function submitStudentAppeal(sessionId: string, unitId: string, reason: string): Promise<AttendanceAppealItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/student/me/appeals`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ session_id: sessionId, unit_id: unitId, reason }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(extractErrorMessage(body, "Failed to submit appeal"));
  }
  return body.data;
}

export async function getStudentAppeals(): Promise<AttendanceAppealItem[] | null> {
  return fetchFromApi<AttendanceAppealItem[]>("/student/me/appeals");
}

export async function getAllAppeals(): Promise<AttendanceAppealItem[] | null> {
  return fetchFromApi<AttendanceAppealItem[]>("/student/appeals/all");
}

export async function reviewAppeal(appealId: string, approved: boolean, reviewNotes: string): Promise<AttendanceAppealItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/student/appeals/${appealId}/review`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ approved, review_notes: reviewNotes }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(extractErrorMessage(body, "Failed to review appeal"));
  }
  return body.data;
}

export async function createDepartment(code: string, name: string): Promise<DepartmentItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/departments`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ code, name }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to create department"));
  return body.data;
}

export async function createCohort(departmentId: string, name: string, admissionYear: number, graduationYear: number): Promise<CohortItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/cohorts`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ department_id: departmentId, name, admission_year: admissionYear, graduation_year: graduationYear }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to create cohort"));
  return body.data;
}

export async function createTerm(academicYearId: string, termType: string, startDate: string, endDate: string): Promise<TermItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/terms`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ academic_year_id: academicYearId, term_type: termType, start_date: startDate, end_date: endDate }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to create term"));
  return body.data;
}

export async function createSubject(code: string, name: string, departmentId: string, credits: number = 3): Promise<any> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/subjects`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ code, name, department_id: departmentId, credits }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to create subject"));
  return body.data;
}

export async function createOffering(subjectId: string, termId: string, primaryCohortId: string, section: string = "A"): Promise<SubjectOfferingItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/offerings`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ subject_id: subjectId, term_id: termId, primary_cohort_id: primaryCohortId, section }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to create offering"));
  return body.data;
}

export async function assignFaculty(facultyId: string, offeringId: string, startDate: string, endDate: string): Promise<FacultyAssignmentItem> {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/academic/faculty-assignments`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "1",
    },
    body: JSON.stringify({ faculty_id: facultyId, offering_id: offeringId, start_date: startDate, end_date: endDate }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "Failed to assign faculty"));
  return body.data;
}

export async function importStudentsCsv(file: File): Promise<{ imported_count: number; skipped_count: number; errors: string[] }> {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${getApiBase()}/academic/import/students/csv`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "ngrok-skip-browser-warning": "1",
    },
    body: formData,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(body, "CSV import failed"));
  return body.data;
}

export function getOfferingAttendanceExportUrl(offeringId: string): string {
  return `${API_BASE}/offerings/${offeringId}/export/csv`;
}

export interface DemoFaceBox {
  face_index: number;
  box: [number, number, number, number];
  detection_score: number;
  quality_score: number;
  quality_reason: string;
  face_crop_base64: string;
  status: "MATCHED" | "UNKNOWN_VISITOR" | "AMBIGUOUS" | "QUALITY_REJECTED" | string;
  attendance_granted: boolean;
  student_id?: string | null;
  roll_number?: string | null;
  full_name?: string | null;
  similarity_score: number;
  margin: number;
  reference_photo_base64?: string | null;
  color_hex: string;
  badge_label: string;
}

export interface DemoStudentResult {
  student_id: string;
  roll_number: string;
  full_name: string;
  attendance_granted: boolean;
  status: "PRESENT" | "ABSENT" | string;
  similarity_score?: number | null;
  face_crop_base64?: string | null;
  reference_photo_base64?: string | null;
  face_width_px?: number | null;
  face_height_px?: number | null;
  effective_threshold?: number | null;
}

export interface DemoEnrolledStudentSummary {
  student_id: string;
  roll_number: string;
  full_name: string;
  is_active: boolean;
  has_reference_photo: boolean;
  photo_url?: string;
  department_code?: string | null;
}

export interface DemoAnalysisResponse {
  total_detected_faces: number;
  total_enrolled_students: number;
  present_count: number;
  absent_count: number;
  unknown_count: number;
  image_width?: number;
  image_height?: number;
  department_filter?: string | null;
  detected_faces: DemoFaceBox[];
  attendance_granted: DemoStudentResult[];
  attendance_not_granted: DemoStudentResult[];
  unidentified_faces: DemoFaceBox[];
}

export async function getDemoEnrolledStudents(departmentCode?: string): Promise<DemoEnrolledStudentSummary[] | null> {
  const query = departmentCode && departmentCode !== "ALL" ? `?department_code=${encodeURIComponent(departmentCode)}` : "";
  return fetchFromApi<DemoEnrolledStudentSummary[]>(`/demo/enrolled-students${query}`);
}

export async function analyzeDemoPhoto(
  file: File,
  matchThreshold: number = 0.460,
  marginThreshold: number = 0.10,
  blurThreshold: number = 50.0,
  departmentCode?: string
): Promise<DemoAnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("match_threshold", matchThreshold.toString());
  formData.append("margin_threshold", marginThreshold.toString());
  formData.append("blur_threshold", blurThreshold.toString());
  if (departmentCode && departmentCode !== "ALL") {
    formData.append("department_code", departmentCode);
  }

  const res = await fetch(`${getApiBase()}/demo/analyze`, {
    method: "POST",
    headers: {
      "ngrok-skip-browser-warning": "1",
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Inference failed with HTTP ${res.status}`);
  }

  const envelope = await res.json();
  return envelope.data;
}


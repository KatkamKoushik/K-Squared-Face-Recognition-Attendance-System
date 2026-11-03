/**
 * Typed API Client for Next.js Admin Console connecting to FastAPI Control Plane.
 * Conforms to canonical OpenAPI contracts and unwraps ResponseEnvelope wrappers.
 * Handles client-side bearer token injection for authenticated endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const AUTH_TOKEN_KEY = "kucet_frs_auth_token";
const AUTH_USER_KEY = "kucet_frs_auth_user";

let inMemoryToken: string | null = null;
let inMemoryUser: StoredAuthUser | null = null;

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
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
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
    const token = getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options?.headers as Record<string, string> || {}),
    };

    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      next: { revalidate: 10 }, // Next.js ISR cache
    });

    if (!res.ok) {
      console.warn(`API error ${res.status} on ${endpoint}`);
      return null;
    }

    const json = await res.json();
    if (json && typeof json === "object" && "data" in json) {
      return json.data as T;
    }
    return json as T;
  } catch (error) {
    console.warn(`Fetch failure on ${endpoint}:`, error);
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

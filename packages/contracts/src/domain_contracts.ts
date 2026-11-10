/**
 * FRS V7.1 K² — Canonical Shared Domain Contracts & Enums.
 * Generated from OpenAPI / FastAPI source-of-truth.
 */

export enum UserRole {
  ADMIN = "ADMIN",
  FACULTY = "FACULTY",
  STUDENT = "STUDENT",
  OPERATOR = "OPERATOR",
  WORKER = "WORKER",
}

export enum AppealStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

export enum EnrollmentStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  DROPPED = "DROPPED",
  SUSPENDED = "SUSPENDED",
}

export enum AcademicTerm {
  ODD = "ODD",
  EVEN = "EVEN",
  SUMMER = "SUMMER",
}

export enum SessionState {
  DRAFT = "DRAFT",
  ROSTER_FROZEN = "ROSTER_FROZEN",
  CAPTURING = "CAPTURING",
  PROCESSING = "PROCESSING",
  IN_REVIEW = "IN_REVIEW",
  FINALIZED = "FINALIZED",
  CANCELLED = "CANCELLED",
}

export enum UnitStatus {
  PENDING = "PENDING",
  CONDUCTED_CONFIRMED = "CONDUCTED_CONFIRMED",
  NOT_CONDUCTED = "NOT_CONDUCTED",
  COMMITTED = "COMMITTED",
}

export enum JobState {
  PENDING = "PENDING",
  LEASED = "LEASED",
  RUNNING = "RUNNING",
  SUCCEEDED = "SUCCEEDED",
  RETRYABLE_FAILURE = "RETRYABLE_FAILURE",
  TERMINAL_FAILURE = "TERMINAL_FAILURE",
}

export enum EvidenceState {
  CAPTURED = "CAPTURED",
  VALIDATING = "VALIDATING",
  QUEUED = "QUEUED",
  PROCESSING = "PROCESSING",
  CANDIDATE = "CANDIDATE",
  UNKNOWN = "UNKNOWN",
  INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE",
  RECAPTURE_REQUIRED = "RECAPTURE_REQUIRED",
  REVIEW = "REVIEW",
  SECURITY_FAIL = "SECURITY_FAIL",
  SECURITY_UNCERTAIN = "SECURITY_UNCERTAIN",
  PIPELINE_ERROR = "PIPELINE_ERROR",
}

export enum AttendanceStatus {
  PRESENT_CONFIRMED = "PRESENT_CONFIRMED",
  ABSENT_CONFIRMED = "ABSENT_CONFIRMED",
  EXCUSED = "EXCUSED",
}

export enum AuditAction {
  SESSION_CREATED = "SESSION_CREATED",
  ROSTER_FROZEN = "ROSTER_FROZEN",
  FRAME_UPLOADED = "FRAME_UPLOADED",
  PROPOSAL_REVIEWED = "PROPOSAL_REVIEWED",
  ATTENDANCE_COMMITTED = "ATTENDANCE_COMMITTED",
  POST_COMMIT_OVERRIDE = "POST_COMMIT_OVERRIDE",
  APPEAL_PROCESSED = "APPEAL_PROCESSED",
  DATA_PURGE_EXECUTED = "DATA_PURGE_EXECUTED",
}

export interface UnitResponse {
  id: string;
  unit_index: number;
  is_conducted: boolean;
  status: UnitStatus;
}

export interface SessionResponse {
  id: string;
  offering_id: string;
  class_group_id: string | null;
  faculty_id: string;
  session_date: string;
  state: SessionState;
  policy_version_id: string;
  planned_units: number;
  created_at: string;
  finalized_at: string | null;
  units: UnitResponse[];
}

export interface CandidateProposalItem {
  student_id: string;
  roll_number: string;
  full_name: string;
  proposal_status: AttendanceStatus | null;
  evidence_state: EvidenceState;
  highest_similarity_score?: number | null;
  sightings_count: number;
  requires_manual_attention: boolean;
  uncertainty_reason?: string | null;
  frame_id?: string | null;
  detection_id?: string | null;
  match_threshold?: number | null;
  model_version?: string | null;
  quality_score?: number | null;
  is_simulated?: boolean;
}

export interface UnknownFaceItem {
  evidence_id: string;
  frame_id: string;
  box_x1: number;
  box_y1: number;
  box_x2: number;
  box_y2: number;
  quality_score: number;
  reason: string;
}

export interface RecaptureHint {
  frame_id: string;
  issue: string;
  recommendation: string;
}

export interface SessionProposalReviewResponse {
  session_id: string;
  total_eligible_students: number;
  proposed_present_count: number;
  proposed_absent_count: number;
  uncertain_count: number;
  unknown_faces_count: number;
  candidates: CandidateProposalItem[];
  unknown_faces: UnknownFaceItem[];
  recapture_hints: RecaptureHint[];
}

export interface StudentUnitDecision {
  student_id: string;
  unit_index: number;
  status: AttendanceStatus;
  reason_code?: string;
  source_evidence_id?: string | null;
}

export interface AttendanceCommitRequest {
  idempotency_key: string;
  conducted_unit_indices: number[];
  decisions: StudentUnitDecision[];
}

export interface CommitReceiptResponse {
  id: string;
  session_id: string;
  idempotency_key: string;
  committed_by_user_id: string;
  total_conducted_units: number;
  total_present_records: number;
  total_absent_records: number;
  receipt_hash: string;
  committed_at: string;
}

export interface StudentAttendanceStat {
  student_id: string;
  roll_number: string;
  full_name: string;
  attended_conducted_units: number;
  eligible_conducted_units: number;
  attendance_percent: number | null; // null if denominator is 0 (renders N/A)
}

export interface OfferingAttendanceAnalyticsResponse {
  offering_id: string;
  total_sessions: number;
  total_conducted_units: number;
  student_stats: StudentAttendanceStat[];
}

export interface AttendanceRecordResponse {
  id: string;
  session_id: string;
  unit_id: string;
  student_id: string;
  status: AttendanceStatus;
  finalized_by_user_id: string;
  reason_code: string;
  committed_at: string;
}

export interface AttendanceCorrectionRequest {
  student_id: string;
  unit_index: number;
  new_status: AttendanceStatus;
  action_type: "OVERRIDE" | "APPEAL" | string;
  reason: string;
  reference_document?: string | null;
}

export interface AttendanceCorrectionResponse {
  record_id: string;
  session_id: string;
  student_id: string;
  unit_index: number;
  previous_status: AttendanceStatus;
  new_status: AttendanceStatus;
  action: string;
  audit_event_id: string;
  updated_at: string;
}

export interface ReceiptVerificationResponse {
  session_id: string;
  receipt_id: string;
  is_valid: boolean;
  signature_verified: boolean;
  ledger_records_matched: boolean;
  total_conducted_units: number;
  total_present_records: number;
  total_absent_records: number;
  receipt_hash: string;
  verified_at: string;
}

export interface PurgeRequest {
  retention_days: number;
  session_id?: string | null;
}

export interface PurgeResponse {
  purged_frames_count: number;
  freed_bytes: number;
  retention_days: number;
  audit_event_id: string;
  executed_at: string;
}

export interface StudentConsentStatus {
  student_id: string;
  roll_number: string;
  full_name: string;
  biometric_consent_active: boolean;
  profile_version?: number | null;
  embedding_namespace?: string | null;
  alternative_roll_call_required: boolean;
}

export interface ConsentToggleRequest {
  student_id: string;
  consent_active: boolean;
  reason: string;
}

export interface GovernanceSummaryResponse {
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

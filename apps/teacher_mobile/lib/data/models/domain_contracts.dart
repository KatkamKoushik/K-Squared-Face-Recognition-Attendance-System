library;

/// FRS V7.1 K² — Canonical Domain Enums and DTOs.
/// Generated from OpenAPI / FastAPI source-of-truth.

enum UserRole {
  admin,
  faculty,
  student,
  operator,
  worker,
}

enum AppealStatus {
  pending,
  approved,
  rejected,
}

enum EnrollmentStatus {
  active,
  inactive,
  dropped,
  suspended,
}

enum AcademicTerm {
  odd,
  even,
  summer,
}

enum SessionState {
  draft,
  rosterFrozen,
  capturing,
  processing,
  inReview,
  finalized,
  cancelled,
}

enum UnitStatus {
  pending,
  conductedConfirmed,
  notConducted,
  committed,
}

enum JobState {
  pending,
  leased,
  running,
  succeeded,
  retryableFailure,
  terminalFailure,
}

enum EvidenceState {
  captured,
  validating,
  queued,
  processing,
  candidate,
  unknown,
  insufficientEvidence,
  recaptureRequired,
  review,
  securityFail,
  securityUncertain,
  pipelineError,
}

enum AttendanceStatus {
  presentConfirmed,
  absentConfirmed,
  excused,
}

extension SessionStateWireExtension on SessionState {
  String toWire() {
    switch (this) {
      case SessionState.draft:
        return 'DRAFT';
      case SessionState.rosterFrozen:
        return 'ROSTER_FROZEN';
      case SessionState.capturing:
        return 'CAPTURING';
      case SessionState.processing:
        return 'PROCESSING';
      case SessionState.inReview:
        return 'IN_REVIEW';
      case SessionState.finalized:
        return 'FINALIZED';
      case SessionState.cancelled:
        return 'CANCELLED';
    }
  }

  static SessionState fromWire(String? value) {
    switch (value?.toUpperCase()) {
      case 'ROSTER_FROZEN':
        return SessionState.rosterFrozen;
      case 'CAPTURING':
        return SessionState.capturing;
      case 'PROCESSING':
        return SessionState.processing;
      case 'IN_REVIEW':
      case 'NEEDS_REVIEW':
        return SessionState.inReview;
      case 'FINALIZED':
      case 'COMMITTED':
        return SessionState.finalized;
      case 'CANCELLED':
        return SessionState.cancelled;
      case 'DRAFT':
      default:
        return SessionState.draft;
    }
  }
}

extension UnitStatusWireExtension on UnitStatus {
  String toWire() {
    switch (this) {
      case UnitStatus.pending:
        return 'PENDING';
      case UnitStatus.conductedConfirmed:
        return 'CONDUCTED_CONFIRMED';
      case UnitStatus.notConducted:
        return 'NOT_CONDUCTED';
      case UnitStatus.committed:
        return 'COMMITTED';
    }
  }

  static UnitStatus fromWire(String? value) {
    switch (value?.toUpperCase()) {
      case 'CONDUCTED_CONFIRMED':
        return UnitStatus.conductedConfirmed;
      case 'NOT_CONDUCTED':
        return UnitStatus.notConducted;
      case 'COMMITTED':
        return UnitStatus.committed;
      case 'PENDING':
      default:
        return UnitStatus.pending;
    }
  }
}

extension EvidenceStateWireExtension on EvidenceState {
  String toWire() {
    switch (this) {
      case EvidenceState.captured:
        return 'CAPTURED';
      case EvidenceState.validating:
        return 'VALIDATING';
      case EvidenceState.queued:
        return 'QUEUED';
      case EvidenceState.processing:
        return 'PROCESSING';
      case EvidenceState.candidate:
        return 'CANDIDATE';
      case EvidenceState.unknown:
        return 'UNKNOWN';
      case EvidenceState.insufficientEvidence:
        return 'INSUFFICIENT_EVIDENCE';
      case EvidenceState.recaptureRequired:
        return 'RECAPTURE_REQUIRED';
      case EvidenceState.review:
        return 'REVIEW';
      case EvidenceState.securityFail:
        return 'SECURITY_FAIL';
      case EvidenceState.securityUncertain:
        return 'SECURITY_UNCERTAIN';
      case EvidenceState.pipelineError:
        return 'PIPELINE_ERROR';
    }
  }

  static EvidenceState fromWire(String? value) {
    switch (value?.toUpperCase()) {
      case 'CAPTURED':
        return EvidenceState.captured;
      case 'VALIDATING':
        return EvidenceState.validating;
      case 'QUEUED':
        return EvidenceState.queued;
      case 'PROCESSING':
        return EvidenceState.processing;
      case 'CANDIDATE':
        return EvidenceState.candidate;
      case 'INSUFFICIENT_EVIDENCE':
        return EvidenceState.insufficientEvidence;
      case 'RECAPTURE_REQUIRED':
        return EvidenceState.recaptureRequired;
      case 'REVIEW':
        return EvidenceState.review;
      case 'SECURITY_FAIL':
        return EvidenceState.securityFail;
      case 'SECURITY_UNCERTAIN':
        return EvidenceState.securityUncertain;
      case 'PIPELINE_ERROR':
        return EvidenceState.pipelineError;
      case 'UNKNOWN':
      default:
        return EvidenceState.unknown;
    }
  }
}

extension AttendanceStatusWireExtension on AttendanceStatus {
  String toWire() {
    switch (this) {
      case AttendanceStatus.presentConfirmed:
        return 'PRESENT_CONFIRMED';
      case AttendanceStatus.absentConfirmed:
        return 'ABSENT_CONFIRMED';
      case AttendanceStatus.excused:
        return 'EXCUSED';
    }
  }

  static AttendanceStatus? fromWire(String? value) {
    switch (value?.toUpperCase()) {
      case 'PRESENT_CONFIRMED':
      case 'PRESENT':
        return AttendanceStatus.presentConfirmed;
      case 'EXCUSED':
        return AttendanceStatus.excused;
      case 'ABSENT_CONFIRMED':
      case 'ABSENT':
        return AttendanceStatus.absentConfirmed;
      default:
        // P0.5 Guardrail: Null, missing, or unknown values must NEVER default to absent.
        return null;
    }
  }
}

enum AuditAction {
  sessionCreated,
  rosterFrozen,
  frameUploaded,
  proposalReviewed,
  attendanceCommitted,
  postCommitOverride,
  appealProcessed,
  dataPurgeExecuted,
}

class UnitResponse {
  final String id;
  final int unitIndex;
  final bool isConducted;
  final UnitStatus status;

  const UnitResponse({
    required this.id,
    required this.unitIndex,
    required this.isConducted,
    required this.status,
  });

  factory UnitResponse.fromJson(Map<String, dynamic> json) {
    return UnitResponse(
      id: json['id'] as String? ?? '',
      unitIndex: json['unit_index'] as int? ?? 1,
      isConducted: json['is_conducted'] as bool? ?? false,
      status: UnitStatusWireExtension.fromWire(json['status'] as String?),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'unit_index': unitIndex,
    'is_conducted': isConducted,
    'status': status.toWire(),
  };
}

class CandidateProposalItem {
  final String studentId;
  final String rollNumber;
  final String fullName;
  final AttendanceStatus? proposalStatus;
  final EvidenceState evidenceState;
  final double? highestSimilarityScore;
  final int sightingsCount;
  final List<String> sightedFrameIds;
  final bool requiresManualAttention;
  final String? uncertaintyReason;
  final Map<int, AttendanceStatus> unitAttendance;
  final String? frameId;
  final String? detectionId;
  final double? matchThreshold;
  final String? modelVersion;
  final double? qualityScore;
  final bool isSimulated;

  const CandidateProposalItem({
    required this.studentId,
    required this.rollNumber,
    required this.fullName,
    this.proposalStatus,
    required this.evidenceState,
    this.highestSimilarityScore,
    this.sightingsCount = 0,
    this.sightedFrameIds = const [],
    this.requiresManualAttention = false,
    this.uncertaintyReason,
    this.unitAttendance = const {},
    this.frameId,
    this.detectionId,
    this.matchThreshold,
    this.modelVersion,
    this.qualityScore,
    this.isSimulated = false,
  });

  CandidateProposalItem copyWith({
    String? studentId,
    String? rollNumber,
    String? fullName,
    AttendanceStatus? proposalStatus,
    EvidenceState? evidenceState,
    double? highestSimilarityScore,
    int? sightingsCount,
    List<String>? sightedFrameIds,
    bool? requiresManualAttention,
    String? uncertaintyReason,
    Map<int, AttendanceStatus>? unitAttendance,
    String? frameId,
    String? detectionId,
    double? matchThreshold,
    String? modelVersion,
    double? qualityScore,
    bool? isSimulated,
  }) {
    return CandidateProposalItem(
      studentId: studentId ?? this.studentId,
      rollNumber: rollNumber ?? this.rollNumber,
      fullName: fullName ?? this.fullName,
      proposalStatus: proposalStatus ?? this.proposalStatus,
      evidenceState: evidenceState ?? this.evidenceState,
      highestSimilarityScore: highestSimilarityScore ?? this.highestSimilarityScore,
      sightingsCount: sightingsCount ?? this.sightingsCount,
      sightedFrameIds: sightedFrameIds ?? this.sightedFrameIds,
      requiresManualAttention: requiresManualAttention ?? this.requiresManualAttention,
      uncertaintyReason: uncertaintyReason ?? this.uncertaintyReason,
      unitAttendance: unitAttendance ?? this.unitAttendance,
      frameId: frameId ?? this.frameId,
      detectionId: detectionId ?? this.detectionId,
      matchThreshold: matchThreshold ?? this.matchThreshold,
      modelVersion: modelVersion ?? this.modelVersion,
      qualityScore: qualityScore ?? this.qualityScore,
      isSimulated: isSimulated ?? this.isSimulated,
    );
  }

  factory CandidateProposalItem.fromJson(Map<String, dynamic> json) {
    return CandidateProposalItem(
      studentId: json['student_id'] as String,
      rollNumber: json['roll_number'] as String,
      fullName: json['full_name'] as String,
      proposalStatus: AttendanceStatusWireExtension.fromWire(json['proposal_status'] as String?),
      evidenceState: EvidenceStateWireExtension.fromWire(json['evidence_state'] as String?),
      highestSimilarityScore: (json['highest_similarity_score'] as num?)?.toDouble(),
      sightingsCount: json['sightings_count'] as int? ?? 0,
      sightedFrameIds: (json['sighted_frame_ids'] as List<dynamic>?)?.map((e) => e as String).toList() ?? const [],
      requiresManualAttention: json['requires_manual_attention'] as bool? ?? false,
      uncertaintyReason: json['uncertainty_reason'] as String?,
      frameId: json['frame_id'] as String?,
      detectionId: json['detection_id'] as String?,
      matchThreshold: (json['match_threshold'] as num?)?.toDouble(),
      modelVersion: json['model_version'] as String?,
      qualityScore: (json['quality_score'] as num?)?.toDouble(),
      isSimulated: json['is_simulated'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'student_id': studentId,
    'roll_number': rollNumber,
    'full_name': fullName,
    'proposal_status': proposalStatus?.toWire(),
    'evidence_state': evidenceState.toWire(),
    'highest_similarity_score': highestSimilarityScore,
    'sightings_count': sightingsCount,
    'sighted_frame_ids': sightedFrameIds,
    'requires_manual_attention': requiresManualAttention,
    'uncertainty_reason': uncertaintyReason,
    'frame_id': frameId,
    'detection_id': detectionId,
    'match_threshold': matchThreshold,
    'model_version': modelVersion,
    'quality_score': qualityScore,
    'is_simulated': isSimulated,
  };
}

class UnassignedFaceObservation {
  final String observationId;
  final String frameId;
  final String issueReason;
  final String description;
  final double qualityScore;
  final List<double>? boundingBox;

  const UnassignedFaceObservation({
    required this.observationId,
    required this.frameId,
    required this.issueReason,
    required this.description,
    required this.qualityScore,
    this.boundingBox,
  });

  factory UnassignedFaceObservation.fromJson(Map<String, dynamic> json) {
    List<double>? box;
    if (json['bounding_box'] is List) {
      box = (json['bounding_box'] as List<dynamic>).map((e) => (e as num).toDouble()).toList();
    } else if (json['box_x1'] != null) {
      box = [
        (json['box_x1'] as num).toDouble(),
        (json['box_y1'] as num).toDouble(),
        (json['box_x2'] as num).toDouble(),
        (json['box_y2'] as num).toDouble(),
      ];
    }
    return UnassignedFaceObservation(
      observationId: (json['observation_id'] ?? json['evidence_id'] ?? 'OBS-UNKNOWN') as String,
      frameId: (json['frame_id'] ?? '') as String,
      issueReason: (json['issue_reason'] ?? json['reason'] ?? 'UNKNOWN_FACE') as String,
      description: (json['description'] ?? 'Unassigned face observation detected by YuNet in classroom photo') as String,
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0.0,
      boundingBox: box,
    );
  }

  Map<String, dynamic> toJson() => {
    'observation_id': observationId,
    'frame_id': frameId,
    'issue_reason': issueReason,
    'description': description,
    'quality_score': qualityScore,
    'bounding_box': boundingBox,
  };
}

class CommitReceiptResponse {
  final String id;
  final String sessionId;
  final String idempotencyKey;
  final String committedByUserId;
  final int totalConductedUnits;
  final int totalPresentRecords;
  final int totalAbsentRecords;
  final String receiptHash;
  final String? modelVersion;
  final double? calibrationThreshold;
  final DateTime committedAt;

  const CommitReceiptResponse({
    required this.id,
    required this.sessionId,
    required this.idempotencyKey,
    required this.committedByUserId,
    required this.totalConductedUnits,
    required this.totalPresentRecords,
    required this.totalAbsentRecords,
    required this.receiptHash,
    this.modelVersion,
    this.calibrationThreshold,
    required this.committedAt,
  });

  factory CommitReceiptResponse.fromJson(Map<String, dynamic> json) {
    return CommitReceiptResponse(
      id: json['id'] as String,
      sessionId: json['session_id'] as String,
      idempotencyKey: json['idempotency_key'] as String,
      committedByUserId: json['committed_by_user_id'] as String,
      totalConductedUnits: json['total_conducted_units'] as int,
      totalPresentRecords: json['total_present_records'] as int,
      totalAbsentRecords: json['total_absent_records'] as int,
      receiptHash: json['receipt_hash'] as String,
      modelVersion: json['model_version'] as String?,
      calibrationThreshold: (json['calibration_threshold'] as num?)?.toDouble(),
      committedAt: DateTime.parse(json['committed_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'session_id': sessionId,
    'idempotency_key': idempotencyKey,
    'committed_by_user_id': committedByUserId,
    'total_conducted_units': totalConductedUnits,
    'total_present_records': totalPresentRecords,
    'total_absent_records': totalAbsentRecords,
    'receipt_hash': receiptHash,
    if (modelVersion != null) 'model_version': modelVersion,
    if (calibrationThreshold != null) 'calibration_threshold': calibrationThreshold,
    'committed_at': committedAt.toIso8601String(),
  };
}

class AttendanceRecordResponse {
  final String id;
  final String sessionId;
  final String unitId;
  final String studentId;
  final AttendanceStatus status;
  final String finalizedByUserId;
  final String reasonCode;
  final DateTime committedAt;

  const AttendanceRecordResponse({
    required this.id,
    required this.sessionId,
    required this.unitId,
    required this.studentId,
    required this.status,
    required this.finalizedByUserId,
    required this.reasonCode,
    required this.committedAt,
  });

  factory AttendanceRecordResponse.fromJson(Map<String, dynamic> json) {
    return AttendanceRecordResponse(
      id: json['id'] as String,
      sessionId: json['session_id'] as String,
      unitId: json['unit_id'] as String,
      studentId: json['student_id'] as String,
      status: AttendanceStatusWireExtension.fromWire(json['status'] as String?) ?? AttendanceStatus.absentConfirmed,
      finalizedByUserId: json['finalized_by_user_id'] as String,
      reasonCode: json['reason_code'] as String,
      committedAt: DateTime.parse(json['committed_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'session_id': sessionId,
    'unit_id': unitId,
    'student_id': studentId,
    'status': status.toWire(),
    'finalized_by_user_id': finalizedByUserId,
    'reason_code': reasonCode,
    'committed_at': committedAt.toIso8601String(),
  };
}

class AttendanceCorrectionRequest {
  final String studentId;
  final int unitIndex;
  final AttendanceStatus newStatus;
  final String actionType;
  final String reason;
  final String? referenceDocument;

  const AttendanceCorrectionRequest({
    required this.studentId,
    required this.unitIndex,
    required this.newStatus,
    required this.actionType,
    required this.reason,
    this.referenceDocument,
  });

  factory AttendanceCorrectionRequest.fromJson(Map<String, dynamic> json) {
    return AttendanceCorrectionRequest(
      studentId: json['student_id'] as String,
      unitIndex: json['unit_index'] as int,
      newStatus: AttendanceStatusWireExtension.fromWire(json['new_status'] as String?) ?? AttendanceStatus.absentConfirmed,
      actionType: json['action_type'] as String,
      reason: json['reason'] as String,
      referenceDocument: json['reference_document'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'student_id': studentId,
    'unit_index': unitIndex,
    'new_status': newStatus.toWire(),
    'action_type': actionType,
    'reason': reason,
    if (referenceDocument != null) 'reference_document': referenceDocument,
  };
}

class AttendanceCorrectionResponse {
  final String recordId;
  final String sessionId;
  final String studentId;
  final int unitIndex;
  final AttendanceStatus previousStatus;
  final AttendanceStatus newStatus;
  final String action;
  final String auditEventId;
  final DateTime updatedAt;

  const AttendanceCorrectionResponse({
    required this.recordId,
    required this.sessionId,
    required this.studentId,
    required this.unitIndex,
    required this.previousStatus,
    required this.newStatus,
    required this.action,
    required this.auditEventId,
    required this.updatedAt,
  });

  factory AttendanceCorrectionResponse.fromJson(Map<String, dynamic> json) {
    return AttendanceCorrectionResponse(
      recordId: json['record_id'] as String,
      sessionId: json['session_id'] as String,
      studentId: json['student_id'] as String,
      unitIndex: json['unit_index'] as int,
      previousStatus: AttendanceStatusWireExtension.fromWire(json['previous_status'] as String?) ?? AttendanceStatus.absentConfirmed,
      newStatus: AttendanceStatusWireExtension.fromWire(json['new_status'] as String?) ?? AttendanceStatus.absentConfirmed,
      action: json['action'] as String,
      auditEventId: json['audit_event_id'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'record_id': recordId,
    'session_id': sessionId,
    'student_id': studentId,
    'unit_index': unitIndex,
    'previous_status': previousStatus.toWire(),
    'new_status': newStatus.toWire(),
    'action': action,
    'audit_event_id': auditEventId,
    'updated_at': updatedAt.toIso8601String(),
  };
}

class ReceiptVerificationResponse {
  final String sessionId;
  final String receiptId;
  final bool isValid;
  final bool signatureVerified;
  final bool ledgerRecordsMatched;
  final int totalConductedUnits;
  final int totalPresentRecords;
  final int totalAbsentRecords;
  final String receiptHash;
  final DateTime verifiedAt;

  const ReceiptVerificationResponse({
    required this.sessionId,
    required this.receiptId,
    required this.isValid,
    required this.signatureVerified,
    required this.ledgerRecordsMatched,
    required this.totalConductedUnits,
    required this.totalPresentRecords,
    required this.totalAbsentRecords,
    required this.receiptHash,
    required this.verifiedAt,
  });

  factory ReceiptVerificationResponse.fromJson(Map<String, dynamic> json) {
    return ReceiptVerificationResponse(
      sessionId: json['session_id'] as String,
      receiptId: json['receipt_id'] as String,
      isValid: json['is_valid'] as bool,
      signatureVerified: json['signature_verified'] as bool,
      ledgerRecordsMatched: json['ledger_records_matched'] as bool,
      totalConductedUnits: json['total_conducted_units'] as int,
      totalPresentRecords: json['total_present_records'] as int,
      totalAbsentRecords: json['total_absent_records'] as int,
      receiptHash: json['receipt_hash'] as String,
      verifiedAt: DateTime.parse(json['verified_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'session_id': sessionId,
    'receipt_id': receiptId,
    'is_valid': isValid,
    'signature_verified': signatureVerified,
    'ledger_records_matched': ledgerRecordsMatched,
    'total_conducted_units': totalConductedUnits,
    'total_present_records': totalPresentRecords,
    'total_absent_records': totalAbsentRecords,
    'receipt_hash': receiptHash,
    'verified_at': verifiedAt.toIso8601String(),
  };
}

class StudentConsentStatus {
  final String studentId;
  final String rollNumber;
  final String fullName;
  final bool biometricConsentActive;
  final int? profileVersion;
  final String? embeddingNamespace;
  final bool alternativeRollCallRequired;

  const StudentConsentStatus({
    required this.studentId,
    required this.rollNumber,
    required this.fullName,
    required this.biometricConsentActive,
    this.profileVersion,
    this.embeddingNamespace,
    required this.alternativeRollCallRequired,
  });

  factory StudentConsentStatus.fromJson(Map<String, dynamic> json) {
    return StudentConsentStatus(
      studentId: json['student_id'] as String,
      rollNumber: json['roll_number'] as String,
      fullName: json['full_name'] as String,
      biometricConsentActive: json['biometric_consent_active'] as bool,
      profileVersion: json['profile_version'] as int?,
      embeddingNamespace: json['embedding_namespace'] as String?,
      alternativeRollCallRequired: json['alternative_roll_call_required'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'student_id': studentId,
    'roll_number': rollNumber,
    'full_name': fullName,
    'biometric_consent_active': biometricConsentActive,
    if (profileVersion != null) 'profile_version': profileVersion,
    if (embeddingNamespace != null) 'embedding_namespace': embeddingNamespace,
    'alternative_roll_call_required': alternativeRollCallRequired,
  };
}

class ConsentToggleRequest {
  final String studentId;
  final bool consentActive;
  final String reason;

  const ConsentToggleRequest({
    required this.studentId,
    required this.consentActive,
    required this.reason,
  });

  factory ConsentToggleRequest.fromJson(Map<String, dynamic> json) {
    return ConsentToggleRequest(
      studentId: json['student_id'] as String,
      consentActive: json['consent_active'] as bool,
      reason: json['reason'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'student_id': studentId,
    'consent_active': consentActive,
    'reason': reason,
  };
}

class PurgeRequest {
  final int retentionDays;
  final String? sessionId;

  const PurgeRequest({
    this.retentionDays = 7,
    this.sessionId,
  });

  factory PurgeRequest.fromJson(Map<String, dynamic> json) {
    return PurgeRequest(
      retentionDays: json['retention_days'] as int? ?? 7,
      sessionId: json['session_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'retention_days': retentionDays,
    if (sessionId != null) 'session_id': sessionId,
  };
}

class PurgeResponse {
  final int purgedFramesCount;
  final int freedBytes;
  final int retentionDays;
  final String auditEventId;
  final DateTime executedAt;

  const PurgeResponse({
    required this.purgedFramesCount,
    required this.freedBytes,
    required this.retentionDays,
    required this.auditEventId,
    required this.executedAt,
  });

  factory PurgeResponse.fromJson(Map<String, dynamic> json) {
    return PurgeResponse(
      purgedFramesCount: json['purged_frames_count'] as int,
      freedBytes: json['freed_bytes'] as int,
      retentionDays: json['retention_days'] as int,
      auditEventId: json['audit_event_id'] as String,
      executedAt: DateTime.parse(json['executed_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'purged_frames_count': purgedFramesCount,
    'freed_bytes': freedBytes,
    'retention_days': retentionDays,
    'audit_event_id': auditEventId,
    'executed_at': executedAt.toIso8601String(),
  };
}

class GovernanceSummaryResponse {
  final int totalStudents;
  final int studentsWithBiometricConsent;
  final int studentsWithheldConsent;
  final double consentCompliancePercentage;
  final int totalCapturedFrames;
  final int activeUnpurgedFrames;
  final int purgedFrames;
  final int diskUsageBytes;
  final double diskUsageMb;
  final int retentionPolicyDays;

  const GovernanceSummaryResponse({
    required this.totalStudents,
    required this.studentsWithBiometricConsent,
    required this.studentsWithheldConsent,
    required this.consentCompliancePercentage,
    required this.totalCapturedFrames,
    required this.activeUnpurgedFrames,
    required this.purgedFrames,
    required this.diskUsageBytes,
    required this.diskUsageMb,
    required this.retentionPolicyDays,
  });

  factory GovernanceSummaryResponse.fromJson(Map<String, dynamic> json) {
    return GovernanceSummaryResponse(
      totalStudents: json['total_students'] as int,
      studentsWithBiometricConsent: json['students_with_biometric_consent'] as int,
      studentsWithheldConsent: json['students_withheld_consent'] as int,
      consentCompliancePercentage: (json['consent_compliance_percentage'] as num).toDouble(),
      totalCapturedFrames: json['total_captured_frames'] as int,
      activeUnpurgedFrames: json['active_unpurged_frames'] as int,
      purgedFrames: json['purged_frames'] as int,
      diskUsageBytes: json['disk_usage_bytes'] as int,
      diskUsageMb: (json['disk_usage_mb'] as num).toDouble(),
      retentionPolicyDays: json['retention_policy_days'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'total_students': totalStudents,
    'students_with_biometric_consent': studentsWithBiometricConsent,
    'students_withheld_consent': studentsWithheldConsent,
    'consent_compliance_percentage': consentCompliancePercentage,
    'total_captured_frames': totalCapturedFrames,
    'active_unpurged_frames': activeUnpurgedFrames,
    'purged_frames': purgedFrames,
    'disk_usage_bytes': diskUsageBytes,
    'disk_usage_mb': diskUsageMb,
    'retention_policy_days': retentionPolicyDays,
  };
}

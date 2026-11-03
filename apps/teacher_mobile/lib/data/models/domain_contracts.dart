library;

/// FRS V7.1 K² — Canonical Domain Enums and DTOs.
/// Generated from OpenAPI / FastAPI source-of-truth.

enum UserRole {
  admin,
  faculty,
  operator,
  worker,
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
    return UnassignedFaceObservation(
      observationId: json['observation_id'] as String,
      frameId: json['frame_id'] as String,
      issueReason: json['issue_reason'] as String,
      description: json['description'] as String,
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0.0,
      boundingBox: (json['bounding_box'] as List<dynamic>?)?.map((e) => (e as num).toDouble()).toList(),
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
    'committed_at': committedAt.toIso8601String(),
  };
}

import 'package:frs_teacher_app/data/models/domain_contracts.dart';

/// Test fixtures for unit and regression testing only.
/// Strictly isolated to test/ directory; never used in production application flows.
class MockTestCandidates {
  static List<CandidateProposalItem> getInitialCandidates() {
    return [
      const CandidateProposalItem(
        studentId: 'STU-TEST-001',
        rollNumber: '00622501',
        fullName: 'Test Student One',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.94,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        frameId: 'FRM-TEST-001',
        detectionId: 'DET-TEST-001',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1',
        qualityScore: 0.95,
        isSimulated: true,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-TEST-002',
        rollNumber: '00622502',
        fullName: 'Test Student Two',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.91,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        frameId: 'FRM-TEST-001',
        detectionId: 'DET-TEST-002',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1',
        qualityScore: 0.92,
        isSimulated: true,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-TEST-003',
        rollNumber: '00622503',
        fullName: 'Test Student Three',
        proposalStatus: null,
        evidenceState: EvidenceState.review,
        highestSimilarityScore: 0.67,
        sightingsCount: 1,
        requiresManualAttention: true,
        uncertaintyReason: 'Similarity score near threshold (0.67 < 0.70). Faculty verification required.',
        frameId: 'FRM-TEST-001',
        detectionId: 'DET-TEST-003',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1',
        qualityScore: 0.74,
        isSimulated: true,
        unitAttendance: {},
      ),
    ];
  }

  static List<UnassignedFaceObservation> getUnassignedObservations() {
    return const [
      UnassignedFaceObservation(
        observationId: 'OBS-001',
        frameId: 'FRM-TEST-001',
        issueReason: 'FACE_MOTION_BLUR',
        description: 'Motion blur detected in test fixture.',
        qualityScore: 0.32,
        boundingBox: [0.72, 0.15, 0.81, 0.28],
      ),
    ];
  }
}

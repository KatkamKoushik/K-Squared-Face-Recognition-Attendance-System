import '../models/domain_contracts.dart';

class MockTeacherData {
  static const facultyId = 'FAC-CS-101';
  static const facultyName = 'Dr. K. Srinivas';

  static final sampleOfferings = [
    {
      'offeringId': 'OFF-CS401-2026',
      'subjectCode': 'CS401',
      'subjectName': 'Advanced Distributed Systems',
      'cohort': 'B.Tech CSE - Final Year (Sec A)',
      'term': 'Fall 2026',
      'enrolledCount': 45,
      'isJointClass': false,
    },
    {
      'offeringId': 'OFF-CS302-JOINT',
      'subjectCode': 'CS302',
      'subjectName': 'Database Engineering (Joint Session)',
      'cohort': 'Approved Union: Sec A + Sec B',
      'term': 'Fall 2026',
      'enrolledCount': 88,
      'isJointClass': true,
    },
  ];

  static List<CandidateProposalItem> getInitialCandidates() {
    return [
      const CandidateProposalItem(
        studentId: 'STU-001',
        rollNumber: '22KU01A0501',
        fullName: 'Aarav Sharma',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.89,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-002',
        rollNumber: '22KU01A0502',
        fullName: 'Bhavya Patel',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.92,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-003',
        rollNumber: '22KU01A0503',
        fullName: 'Chaitanya Reddy',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.review,
        highestSimilarityScore: 0.68,
        sightingsCount: 1,
        requiresManualAttention: true,
        uncertaintyReason: 'Similarity score near threshold (0.68). Please verify.',
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-004',
        rollNumber: '22KU01A0504',
        fullName: 'Deepika Rao',
        proposalStatus: AttendanceStatus.absentConfirmed,
        evidenceState: EvidenceState.recaptureRequired,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: true,
        uncertaintyReason: 'Face motion blur in back row. Targeted recapture recommended.',
        unitAttendance: {1: AttendanceStatus.absentConfirmed, 2: AttendanceStatus.absentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-005',
        rollNumber: '22KU01A0505',
        fullName: 'Eshwar Verma',
        proposalStatus: AttendanceStatus.absentConfirmed,
        evidenceState: EvidenceState.unknown,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: false,
        uncertaintyReason: 'No matching face detected across 3 classroom photos.',
        unitAttendance: {1: AttendanceStatus.absentConfirmed, 2: AttendanceStatus.absentConfirmed},
      ),
    ];
  }
}

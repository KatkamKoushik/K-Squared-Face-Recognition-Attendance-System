import '../models/domain_contracts.dart';

/// Institutional baseline data for KU College of Engineering & Technology (KUCET).
/// Extracted from official institutional registers (http://kucet.ac.in/).
class MockTeacherData {
  static const facultyId = 'KUCET-FAC-CSE-001';
  static const facultyName = 'Mr. V. Ramana Babu';
  static const facultyDesignation = 'Assistant Professor & Coordinator';
  static const departmentName = 'Department of Computer Science & Engineering';
  static const collegeName = 'KU College of Engineering & Technology (KUCET)';
  static const campusLocation = 'Kakatiya University Campus, Warangal - 506009';

  static final sampleOfferings = [
    {
      'offeringId': 'OFF-KUCET-CSE-401',
      'subjectCode': 'CS401',
      'subjectName': 'Distributed Systems & Cloud Computing',
      'cohort': 'B.Tech CSE - Final Year (IV/IV Sec A)',
      'term': 'VII Semester (2026-2027)',
      'enrolledCount': 66,
      'isJointClass': false,
    },
    {
      'offeringId': 'OFF-KUCET-CS-IT-JOINT',
      'subjectCode': 'CS302',
      'subjectName': 'Database Management Systems (Joint Theory)',
      'cohort': 'Approved Union: B.Tech CSE (Sec A) + B.Tech IT',
      'term': 'V Semester (2026-2027)',
      'enrolledCount': 132,
      'isJointClass': true,
    },
    {
      'offeringId': 'OFF-KUCET-CSD-301',
      'subjectCode': 'DS301',
      'subjectName': 'Artificial Intelligence & Machine Learning',
      'cohort': 'B.Tech CSE (Data Science) - Third Year (III/IV)',
      'term': 'V Semester (2026-2027)',
      'enrolledCount': 66,
      'isJointClass': false,
    },
  ];

  static List<CandidateProposalItem> getInitialCandidates() {
    return [
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622501',
        rollNumber: '00622501',
        fullName: 'Katkam Koushik',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.94,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622502',
        rollNumber: '00622502',
        fullName: 'A. Sai Teja',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.91,
        sightingsCount: 3,
        requiresManualAttention: false,
        uncertaintyReason: null,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622503',
        rollNumber: '00622503',
        fullName: 'B. Manasa Reddy',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.review,
        highestSimilarityScore: 0.67,
        sightingsCount: 1,
        requiresManualAttention: true,
        uncertaintyReason: 'Similarity score near threshold (0.67). Faculty verification requested.',
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622504',
        rollNumber: '00622504',
        fullName: 'Ch. Rahul',
        proposalStatus: AttendanceStatus.absentConfirmed,
        evidenceState: EvidenceState.recaptureRequired,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: true,
        uncertaintyReason: 'Face motion blur in back row seating. Targeted recapture recommended.',
        unitAttendance: {1: AttendanceStatus.absentConfirmed, 2: AttendanceStatus.absentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622505',
        rollNumber: '00622505',
        fullName: 'D. Ananya',
        proposalStatus: AttendanceStatus.absentConfirmed,
        evidenceState: EvidenceState.unknown,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: true,
        uncertaintyReason: 'Zero sightings across classroom sweep frames. Verification required.',
        unitAttendance: {1: AttendanceStatus.absentConfirmed, 2: AttendanceStatus.absentConfirmed},
      ),
    ];
  }
}

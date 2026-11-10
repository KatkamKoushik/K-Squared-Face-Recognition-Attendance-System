import '../models/domain_contracts.dart';

/// Institutional baseline data for KU College of Engineering & Technology (KUCET).
/// Extracted from official institutional registers (http://kucet.ac.in/).
class KucetTeacherData {
  static const facultyId = 'KUCET-FAC-IT-001';
  static const facultyName = 'Dr. M. Soujanya';
  static const facultyDesignation = 'Assistant Professor (c) & Academic Coordinator';
  static const departmentName = 'Department of Information Technology';
  static const facultyEmail = 'soujanyavedh@gmail.com';
  static const facultyPhone = '9010610430';
  static const collegeName = 'KU College of Engineering & Technology (KUCET)';
  static const campusLocation = 'Kakatiya University Campus, Warangal - 506009';

  static final sampleOfferings = [
    {
      'offeringId': 'OFF-KUCET-IT-302-DBMS',
      'subjectCode': 'IT302 / CS302',
      'subjectName': 'Database Management Systems (Joint Theory)',
      'cohort': 'Approved Union: B.Tech IT + B.Tech CSE (Sec A)',
      'term': 'V Semester (2026-2027)',
      'enrolledCount': 132,
      'isJointClass': true,
    },
    {
      'offeringId': 'OFF-KUCET-IT-401',
      'subjectCode': 'IT401',
      'subjectName': 'Web Technologies & Information Security',
      'cohort': 'B.Tech IT - Final Year (IV/IV)',
      'term': 'VII Semester (2026-2027)',
      'enrolledCount': 66,
      'isJointClass': false,
    },
    {
      'offeringId': 'OFF-KUCET-IT-201',
      'subjectCode': 'IT201',
      'subjectName': 'Object Oriented Programming through Java',
      'cohort': 'B.Tech IT - Second Year (II/IV)',
      'term': 'III Semester (2026-2027)',
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
        frameId: 'FRM-1250B58D',
        detectionId: 'DET-KUCET-001',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1 (OpenCV Zoo ONNX)',
        qualityScore: 0.95,
        isSimulated: false,
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
        frameId: 'FRM-1250B58D',
        detectionId: 'DET-KUCET-002',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1 (OpenCV Zoo ONNX)',
        qualityScore: 0.92,
        isSimulated: false,
        unitAttendance: {1: AttendanceStatus.presentConfirmed, 2: AttendanceStatus.presentConfirmed},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622503',
        rollNumber: '00622503',
        fullName: 'B. Manasa Reddy',
        proposalStatus: null,
        evidenceState: EvidenceState.review,
        highestSimilarityScore: 0.67,
        sightingsCount: 1,
        requiresManualAttention: true,
        uncertaintyReason: 'Similarity score near threshold (0.67 < 0.70). Faculty verification required.',
        frameId: 'FRM-1250B58D',
        detectionId: 'DET-KUCET-003',
        matchThreshold: 0.70,
        modelVersion: 'sface_128d_v1 (OpenCV Zoo ONNX)',
        qualityScore: 0.74,
        isSimulated: false,
        unitAttendance: {},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622504',
        rollNumber: '00622504',
        fullName: 'Ch. Rahul',
        proposalStatus: null,
        evidenceState: EvidenceState.unknown,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: true,
        uncertaintyReason: 'NON_BIOMETRIC_ALTERNATIVE_REQUIRED: Student has withheld biometric consent under DPDP Act. Manual roll-call fallback required.',
        frameId: null,
        detectionId: null,
        matchThreshold: null,
        modelVersion: null,
        qualityScore: null,
        isSimulated: false,
        unitAttendance: {},
      ),
      const CandidateProposalItem(
        studentId: 'STU-KUCET-00622505',
        rollNumber: '00622505',
        fullName: 'D. Ananya',
        proposalStatus: null,
        evidenceState: EvidenceState.unknown,
        highestSimilarityScore: null,
        sightingsCount: 0,
        requiresManualAttention: true,
        uncertaintyReason: 'NO_CAMERA_SIGHTING',
        frameId: null,
        detectionId: null,
        matchThreshold: null,
        modelVersion: null,
        qualityScore: null,
        isSimulated: false,
        unitAttendance: {},
      ),
    ];
  }

  static List<UnassignedFaceObservation> getUnassignedObservations() {
    return const [
      UnassignedFaceObservation(
        observationId: 'OBS-001',
        frameId: 'FRM-1250B58D',
        issueReason: 'FACE_MOTION_BLUR',
        description: 'Motion blur detected in back row seating. Quality score 0.32 below 0.50 cutoff. Could not extract biometric embedding. Recommend targeted recapture.',
        qualityScore: 0.32,
        boundingBox: [0.72, 0.15, 0.81, 0.28],
      ),
      UnassignedFaceObservation(
        observationId: 'OBS-002',
        frameId: 'FRM-1250B58D',
        issueReason: 'UNKNOWN_SUBJECT',
        description: 'Clear face crop detected (Quality: 0.84), but cosine similarity < 0.40 against all enrolled cohort templates. Possible visitor or auditing student.',
        qualityScore: 0.84,
        boundingBox: [0.12, 0.40, 0.22, 0.54],
      ),
    ];
  }
}

/// Backward compatibility alias for tests
typedef MockTeacherData = KucetTeacherData;

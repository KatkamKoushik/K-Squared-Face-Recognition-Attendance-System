import 'package:flutter_test/flutter_test.dart';
import 'package:frs_teacher_app/data/models/domain_contracts.dart';

void main() {
  group('Domain Enums Wire Serialization', () {
    test('AttendanceStatus wire mapping is exact and bidirectional', () {
      expect(AttendanceStatus.presentConfirmed.toWire(), 'PRESENT_CONFIRMED');
      expect(AttendanceStatus.absentConfirmed.toWire(), 'ABSENT_CONFIRMED');
      expect(AttendanceStatus.excused.toWire(), 'EXCUSED');

      expect(AttendanceStatusWireExtension.fromWire('PRESENT_CONFIRMED'), AttendanceStatus.presentConfirmed);
      expect(AttendanceStatusWireExtension.fromWire('PRESENT'), AttendanceStatus.presentConfirmed);
      expect(AttendanceStatusWireExtension.fromWire('ABSENT_CONFIRMED'), AttendanceStatus.absentConfirmed);
      expect(AttendanceStatusWireExtension.fromWire('ABSENT'), AttendanceStatus.absentConfirmed);
      expect(AttendanceStatusWireExtension.fromWire('EXCUSED'), AttendanceStatus.excused);
      expect(AttendanceStatusWireExtension.fromWire('UNKNOWN_STRING'), AttendanceStatus.absentConfirmed);
    });

    test('SessionState wire mapping normalizes legacy terminology', () {
      expect(SessionState.inReview.toWire(), 'IN_REVIEW');
      expect(SessionState.finalized.toWire(), 'FINALIZED');

      expect(SessionStateWireExtension.fromWire('IN_REVIEW'), SessionState.inReview);
      expect(SessionStateWireExtension.fromWire('NEEDS_REVIEW'), SessionState.inReview);
      expect(SessionStateWireExtension.fromWire('FINALIZED'), SessionState.finalized);
      expect(SessionStateWireExtension.fromWire('COMMITTED'), SessionState.finalized);
    });

    test('CandidateProposalItem roundtrips faithfully to and from JSON', () {
      final item = CandidateProposalItem(
        studentId: 'STU-100',
        rollNumber: '22KU01A0501',
        fullName: 'Test Student',
        proposalStatus: AttendanceStatus.presentConfirmed,
        evidenceState: EvidenceState.candidate,
        highestSimilarityScore: 0.88,
        sightingsCount: 3,
        requiresManualAttention: false,
      );

      final json = item.toJson();
      expect(json['proposal_status'], 'PRESENT_CONFIRMED');
      expect(json['evidence_state'], 'CANDIDATE');

      final deserialized = CandidateProposalItem.fromJson(json);
      expect(deserialized.studentId, 'STU-100');
      expect(deserialized.proposalStatus, AttendanceStatus.presentConfirmed);
      expect(deserialized.evidenceState, EvidenceState.candidate);
      expect(deserialized.highestSimilarityScore, 0.88);
    });
  });
}


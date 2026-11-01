import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/core/network/api_service.dart';
import 'package:frs_teacher_app/logic/session_provider.dart';
import 'package:frs_teacher_app/data/models/domain_contracts.dart';

class MockServerSuccessApiService extends FrsApiService {
  @override
  Future<CommitReceiptResponse?> commitSession({
    required String sessionId,
    required String idempotencyKey,
    required int conductedUnitsCount,
    required List<CandidateProposalItem> candidates,
  }) async {
    return CommitReceiptResponse(
      id: 'RCP-AUTH-SERVER-001',
      sessionId: sessionId,
      idempotencyKey: idempotencyKey,
      committedByUserId: 'FAC-KUCET-001',
      totalConductedUnits: conductedUnitsCount,
      totalPresentRecords: 2,
      totalAbsentRecords: 0,
      receiptHash: '0xauthhash123456',
      committedAt: DateTime.now(),
    );
  }

  @override
  Future<CommitReceiptResponse?> getSessionReceipt(String sessionId) async {
    return CommitReceiptResponse(
      id: 'RCP-AUTH-SERVER-001',
      sessionId: sessionId,
      idempotencyKey: 'IDEMP-SAVED',
      committedByUserId: 'FAC-KUCET-001',
      totalConductedUnits: 2,
      totalPresentRecords: 2,
      totalAbsentRecords: 0,
      receiptHash: '0xauthhash123456',
      committedAt: DateTime.now(),
    );
  }
}

void main() {
  group('Session Workflow Riverpod State Machine', () {
    test('Initial state is draft with 2 conducted units default', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final state = container.read(sessionProvider);
      expect(state.state, SessionState.draft);
      expect(state.conductedUnitsCount, 2);
      expect(state.capturedFrames, isEmpty);
      expect(state.candidates, isEmpty);
    });

    test('Selecting offering transitions state to rosterFrozen and assigns session IDs', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      await container.read(sessionProvider.notifier).selectOffering({
        'id': 'OFF-CS401-2026',
        'code': 'CS401',
        'name': 'Cloud Computing',
      });

      final state = container.read(sessionProvider);
      expect(state.state, SessionState.rosterFrozen);
      expect(state.sessionId, startsWith('SES-'));
      expect(state.batchId, startsWith('BAT-'));
    });

    test('Conducted units enforces bounds 1 <= units <= 4', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      notifier.setConductedUnits(3);
      expect(container.read(sessionProvider).conductedUnitsCount, 3);

      notifier.setConductedUnits(0); // Out of bounds, ignored
      expect(container.read(sessionProvider).conductedUnitsCount, 3);

      notifier.setConductedUnits(5); // Out of bounds, ignored
      expect(container.read(sessionProvider).conductedUnitsCount, 3);
    });

    test('Adding and removing captured frames updates state and transitions to capturing', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      notifier.addCapturedFrame(frameId: 'FRM-01', hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');

      var state = container.read(sessionProvider);
      expect(state.state, SessionState.capturing);
      expect(state.capturedFrames.length, 1);

      notifier.removeFrame(0);
      state = container.read(sessionProvider);
      expect(state.capturedFrames, isEmpty);
    });

    test('Submitting batch updates state to inReview with populated candidates', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      await notifier.selectOffering({'id': 'OFF-CS401-2026'});
      await notifier.submitBatchForProcessing();

      final state = container.read(sessionProvider);
      expect(state.state, SessionState.inReview);
      expect(state.candidates, isNotEmpty);
    });

    test('P0.4: Committing offline forbids client-minted receipt and retains inReview state', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      await notifier.selectOffering({'id': 'OFF-CS401-2026'});
      await notifier.submitBatchForProcessing();

      // Attempt commit without backend server running
      final receipt = await notifier.commitFinalAttendance();
      final state = container.read(sessionProvider);

      // P0.4: Forbid client from entering SessionState.finalized without authoritative server receipt
      expect(receipt, isNull);
      expect(state.state, SessionState.inReview);
      expect(state.receipt, isNull);
      expect(state.errorMessage, contains('Client-minted offline receipts are prohibited'));
    });

    test('P0.4: Committing with authoritative server receipt transitions to finalized', () async {
      final container = ProviderContainer(
        overrides: [
          apiProvider.overrideWithValue(MockServerSuccessApiService()),
        ],
      );
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      await notifier.selectOffering({'id': 'OFF-CS401-2026'});
      await notifier.submitBatchForProcessing();

      final receipt = await notifier.commitFinalAttendance();
      final state = container.read(sessionProvider);

      expect(state.state, SessionState.finalized);
      expect(state.receipt, isNotNull);
      expect(receipt?.id, 'RCP-AUTH-SERVER-001');
      expect(receipt?.receiptHash, '0xauthhash123456');
      expect(receipt?.totalConductedUnits, 2);
    });

    test('P0.4: checkCommitReceiptStatus recovers durable receipt from server', () async {
      final container = ProviderContainer(
        overrides: [
          apiProvider.overrideWithValue(MockServerSuccessApiService()),
        ],
      );
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      await notifier.selectOffering({'id': 'OFF-CS401-2026'});

      final recovered = await notifier.checkCommitReceiptStatus();
      final state = container.read(sessionProvider);

      expect(recovered, isNotNull);
      expect(recovered?.id, 'RCP-AUTH-SERVER-001');
      expect(state.state, SessionState.finalized);
    });
  });
}

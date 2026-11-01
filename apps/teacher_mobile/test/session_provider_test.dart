import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/logic/session_provider.dart';
import 'package:frs_teacher_app/data/models/domain_contracts.dart';

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

    test('Committing session transitions to finalized and returns durable receipt', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(sessionProvider.notifier);
      await notifier.selectOffering({'id': 'OFF-CS401-2026'});
      await notifier.submitBatchForProcessing();

      final receipt = await notifier.commitFinalAttendance();
      final state = container.read(sessionProvider);

      expect(state.state, SessionState.finalized);
      expect(state.receipt, isNotNull);
      expect(receipt.id, startsWith('RCP-'));
      expect(receipt.receiptHash, startsWith('0x'));
      expect(receipt.totalConductedUnits, 2);
    });
  });
}

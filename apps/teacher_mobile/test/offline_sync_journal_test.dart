import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:frs_teacher_app/core/network/offline_sync_journal.dart';

void main() {
  group('OfflineSyncJournal & Mutation LifeCycle (Checklist Controls 20-N001..20-N016)', () {
    late OfflineSyncJournal journal;

    setUp(() {
      journal = OfflineSyncJournal();
    });

    test('Enqueue mutation binds to teacher account and sets pending status', () {
      final mutation = QueuedMutation(
        id: 'mut-001',
        mutationType: 'MANUAL_ATTENDANCE',
        accountId: 'FAC-001',
        sessionId: 'SES-999',
        idempotencyKey: 'idemp-001',
        payload: {'student_id': 'STU-1', 'status': 'PRESENT_CONFIRMED'},
        createdAt: DateTime.now(),
      );

      final enqueued = journal.enqueueMutation(mutation);
      expect(enqueued, isTrue);
      expect(journal.queueLength, 1);
      expect(journal.pendingCount, 1);
      expect(journal.syncedCount, 0);

      final pending = journal.getPendingMutationsForAccount('FAC-001');
      expect(pending.length, 1);
      expect(pending.first.id, 'mut-001');
    });

    test('Account context isolation prevents mutation replay under different teacher (20-N006)', () {
      final mutation = QueuedMutation(
        id: 'mut-002',
        mutationType: 'SESSION_COMMIT',
        accountId: 'FAC-001',
        sessionId: 'SES-999',
        idempotencyKey: 'idemp-002',
        payload: {'conducted_units': 2},
        createdAt: DateTime.now(),
      );

      journal.enqueueMutation(mutation);

      // Querying as another teacher returns empty list
      final otherTeacherPending = journal.getPendingMutationsForAccount('FAC-002');
      expect(otherTeacherPending, isEmpty);

      // Querying as original teacher returns the queued mutation
      final originalTeacherPending = journal.getPendingMutationsForAccount('FAC-001');
      expect(originalTeacherPending.length, 1);
    });

    test('Status transitions: pending -> synced updates lastSuccessfulSyncAt (20-N007, 20-N015)', () {
      final mutation = QueuedMutation(
        id: 'mut-003',
        mutationType: 'MANUAL_ATTENDANCE',
        accountId: 'FAC-001',
        sessionId: 'SES-999',
        idempotencyKey: 'idemp-003',
        payload: {},
        createdAt: DateTime.now(),
      );

      journal.enqueueMutation(mutation);
      expect(journal.lastSuccessfulSyncAt, isNull);

      journal.markSynced('mut-003');
      expect(journal.syncedCount, 1);
      expect(journal.pendingCount, 0);
      expect(journal.lastSuccessfulSyncAt, isNotNull);
    });

    test('Terminal and retryable failure handling with exponential backoff (20-N005, 20-N012)', () {
      final mutation = QueuedMutation(
        id: 'mut-004',
        mutationType: 'MANUAL_ATTENDANCE',
        accountId: 'FAC-001',
        sessionId: 'SES-999',
        idempotencyKey: 'idemp-004',
        payload: {},
        createdAt: DateTime.now(),
      );

      journal.enqueueMutation(mutation);

      // 1st failure: retryable
      journal.recordFailure('mut-004', 'Temporary HTTP 503');
      expect(mutation.status, MutationSyncStatus.failedRetryable);
      expect(mutation.attemptCount, 1);

      // Check backoff increases
      final backoff1 = journal.calculateBackoffMs(1, baseMs: 100);
      expect(backoff1, greaterThanOrEqualTo(200));

      // Terminal failure
      journal.recordFailure('mut-004', 'Permanent 400 Bad Request', isTerminal: true);
      expect(mutation.status, MutationSyncStatus.failedTerminal);
    });

    test('Purge on logout clears all sensitive pending queue items (20-N016)', () {
      journal.enqueueMutation(QueuedMutation(
        id: 'mut-005',
        mutationType: 'MANUAL_ATTENDANCE',
        accountId: 'FAC-001',
        sessionId: 'SES-999',
        idempotencyKey: 'idemp-005',
        payload: {},
        createdAt: DateTime.now(),
      ));

      expect(journal.queueLength, 1);
      journal.purgeOnLogout();
      expect(journal.queueLength, 0);
      expect(journal.lastSuccessfulSyncAt, isNull);
    });

    test('Serialization and deserialization preserves all mutation state', () {
      final now = DateTime.now();
      journal.enqueueMutation(QueuedMutation(
        id: 'mut-006',
        mutationType: 'MANUAL_ATTENDANCE',
        accountId: 'FAC-001',
        sessionId: 'SES-888',
        idempotencyKey: 'idemp-006',
        payload: {'test_key': 'test_val'},
        createdAt: now,
      ));

      final serialized = journal.serialize();
      final newJournal = OfflineSyncJournal();
      newJournal.deserialize(serialized);

      expect(newJournal.queueLength, 1);
      final restored = newJournal.getPendingMutationsForAccount('FAC-001').first;
      expect(restored.id, 'mut-006');
      expect(restored.sessionId, 'SES-888');
      expect(restored.payload['test_key'], 'test_val');
    });

    test('FileJournalStorage persists mutations across app crash/process restarts', () async {
      final tempDir = await Directory.systemTemp.createTemp('journal_test_');
      final journalFile = File('${tempDir.path}/offline_queue.wal');

      try {
        // 1. First app run: create journal, enqueue mutations
        final initialJournal = OfflineSyncJournal(file: journalFile);
        expect(initialJournal.queueLength, 0);

        final now = DateTime.now();
        initialJournal.enqueueMutation(QueuedMutation(
          id: 'mut-crash-001',
          mutationType: 'SESSION_COMMIT',
          accountId: 'FAC-KUCET-101',
          sessionId: 'SES-CRASH-TEST',
          idempotencyKey: 'idemp-crash-001',
          payload: {'conducted_units': 2, 'records_count': 35},
          createdAt: now,
        ));

        initialJournal.recordFailure('mut-crash-001', 'Network unreachable 503');
        expect(initialJournal.queueLength, 1);
        expect(initialJournal.pendingCount, 1);

        // Verify the file was written
        expect(journalFile.existsSync(), isTrue);

        // 2. Simulate app kill/process restart: instantiate completely new journal with same file
        final recoveredJournal = OfflineSyncJournal(file: journalFile);
        expect(recoveredJournal.queueLength, 1);
        expect(recoveredJournal.pendingCount, 1);

        final pending = recoveredJournal.getPendingMutationsForAccount('FAC-KUCET-101');
        expect(pending.length, 1);
        expect(pending.first.id, 'mut-crash-001');
        expect(pending.first.sessionId, 'SES-CRASH-TEST');
        expect(pending.first.status, MutationSyncStatus.failedRetryable);
        expect(pending.first.attemptCount, 1);
        expect(pending.first.lastErrorMessage, 'Network unreachable 503');

        // 3. Mark synced in recovered session and verify file update
        recoveredJournal.markSynced('mut-crash-001');
        expect(recoveredJournal.syncedCount, 1);

        final thirdRunJournal = OfflineSyncJournal(file: journalFile);
        expect(thirdRunJournal.syncedCount, 1);
        expect(thirdRunJournal.pendingCount, 0);

        // 4. Logout purges memory and disk
        thirdRunJournal.purgeOnLogout();
        expect(thirdRunJournal.queueLength, 0);
        expect(journalFile.existsSync(), isFalse);
      } finally {
        if (tempDir.existsSync()) {
          tempDir.deleteSync(recursive: true);
        }
      }
    });
  });
}

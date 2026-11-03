import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../core/network/api_service.dart';
import '../core/network/offline_sync_journal.dart';
import '../data/mock/mock_teacher_data.dart';
import '../data/models/domain_contracts.dart';

class SessionWorkflowState {
  final String sessionId;
  final String batchId;
  final Map<String, dynamic>? selectedOffering;
  final int conductedUnitsCount;
  final List<Map<String, String>> capturedFrames;
  final SessionState state;
  final List<CandidateProposalItem> candidates;
  final List<UnassignedFaceObservation> unassignedObservations;
  final CommitReceiptResponse? receipt;
  final String? errorMessage;

  const SessionWorkflowState({
    this.sessionId = '',
    this.batchId = '',
    this.selectedOffering,
    this.conductedUnitsCount = 2,
    this.capturedFrames = const [],
    this.state = SessionState.draft,
    this.candidates = const [],
    this.unassignedObservations = const [],
    this.receipt,
    this.errorMessage,
  });

  SessionWorkflowState copyWith({
    String? sessionId,
    String? batchId,
    Map<String, dynamic>? selectedOffering,
    int? conductedUnitsCount,
    List<Map<String, String>>? capturedFrames,
    SessionState? state,
    List<CandidateProposalItem>? candidates,
    List<UnassignedFaceObservation>? unassignedObservations,
    CommitReceiptResponse? receipt,
    String? errorMessage,
  }) {
    return SessionWorkflowState(
      sessionId: sessionId ?? this.sessionId,
      batchId: batchId ?? this.batchId,
      selectedOffering: selectedOffering ?? this.selectedOffering,
      conductedUnitsCount: conductedUnitsCount ?? this.conductedUnitsCount,
      capturedFrames: capturedFrames ?? this.capturedFrames,
      state: state ?? this.state,
      candidates: candidates ?? this.candidates,
      unassignedObservations: unassignedObservations ?? this.unassignedObservations,
      receipt: receipt ?? this.receipt,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

final apiProvider = Provider<FrsApiService>((ref) => FrsApiService());
final offlineSyncJournalProvider = Provider<OfflineSyncJournal>((ref) => OfflineSyncJournal());

class SessionNotifier extends Notifier<SessionWorkflowState> {
  FrsApiService get _api => ref.read(apiProvider);
  OfflineSyncJournal get _journal => ref.read(offlineSyncJournalProvider);

  @override
  SessionWorkflowState build() {
    return const SessionWorkflowState();
  }

  Future<void> selectOffering(Map<String, dynamic> offering) async {
    const uuid = Uuid();
    final newSessionId = 'SES-${uuid.v4().substring(0, 8).toUpperCase()}';
    final newBatchId = 'BAT-${uuid.v4().substring(0, 8).toUpperCase()}';

    state = state.copyWith(
      sessionId: newSessionId,
      batchId: newBatchId,
      selectedOffering: offering,
      state: SessionState.rosterFrozen,
    );

    // Asynchronously register session on control-plane in background
    final offeringId = offering['id'] as String? ?? 'OFF-CS401-2026';
    try {
      final serverId = await _api.createSession(
        offeringId: offeringId,
        plannedUnits: state.conductedUnitsCount,
      );
      if (serverId != null && serverId.isNotEmpty) {
        state = state.copyWith(sessionId: serverId);
      }
    } catch (_) {
      // Disposed or offline
    }
  }

  void setConductedUnits(int count) {
    if (count < 1 || count > 4) return;
    state = state.copyWith(conductedUnitsCount: count);
  }

  void addCapturedFrame({required String frameId, required String hash}) {
    final updated = List<Map<String, String>>.from(state.capturedFrames)
      ..add({'frameId': frameId, 'hash': hash, 'time': DateTime.now().toIso8601String()});
    state = state.copyWith(
      capturedFrames: updated,
      state: SessionState.capturing,
    );
  }

  void removeFrame(int index) {
    final updated = List<Map<String, String>>.from(state.capturedFrames)..removeAt(index);
    state = state.copyWith(capturedFrames: updated);
  }

  Future<void> submitBatchForProcessing() async {
    state = state.copyWith(state: SessionState.processing);

    // Call real asynchronous proposal polling with graceful fallback
    final candidates = await _api.pollProposal(
      sessionId: state.sessionId,
      maxAttempts: 2,
      interval: const Duration(milliseconds: 500),
    );

    state = state.copyWith(
      state: SessionState.inReview,
      candidates: candidates,
      unassignedObservations: MockTeacherData.getUnassignedObservations(),
    );
  }

  void updateStudentUnitAttendance(String studentId, int unitIdx, AttendanceStatus status) {
    final updatedCandidates = state.candidates.map((c) {
      if (c.studentId == studentId) {
        final updatedUnits = Map<int, AttendanceStatus>.from(c.unitAttendance);
        updatedUnits[unitIdx] = status;
        return c.copyWith(unitAttendance: updatedUnits);
      }
      return c;
    }).toList();

    state = state.copyWith(candidates: updatedCandidates);
  }

  void resolveCandidateState(String studentId, AttendanceStatus status) {
    final updatedCandidates = state.candidates.map((c) {
      if (c.studentId == studentId) {
        final updatedUnits = <int, AttendanceStatus>{};
        for (int i = 1; i <= state.conductedUnitsCount; i++) {
          updatedUnits[i] = status;
        }
        return c.copyWith(
          proposalStatus: status,
          evidenceState: status == AttendanceStatus.presentConfirmed
              ? EvidenceState.candidate
              : EvidenceState.unknown,
          uncertaintyReason: 'Resolved by faculty instructor',
          unitAttendance: updatedUnits,
          requiresManualAttention: false,
        );
      }
      return c;
    }).toList();

    state = state.copyWith(candidates: updatedCandidates);
  }

  Future<CommitReceiptResponse?> commitFinalAttendance() async {
    const uuid = Uuid();
    final idempotencyKey = 'IDEMP-${uuid.v4().replaceAll('-', '')}';

    // Attempt real HTTP commit against FastAPI control plane
    final serverReceipt = await _api.commitSession(
      sessionId: state.sessionId,
      idempotencyKey: idempotencyKey,
      conductedUnitsCount: state.conductedUnitsCount,
      candidates: state.candidates,
    );

    if (serverReceipt != null) {
      state = state.copyWith(
        state: SessionState.finalized,
        receipt: serverReceipt,
        errorMessage: null,
      );
      return serverReceipt;
    }

    // P0.4: Eliminate client-minted offline receipts.
    // Client is forbidden from entering SessionState.finalized without an authoritative server-issued receipt.
    // Record pending mutation in offline sync journal for durable reconciliation upon reconnect.
    _journal.enqueueMutation(
      QueuedMutation(
        id: 'MUT-${uuid.v4().substring(0, 8).toUpperCase()}',
        mutationType: 'SESSION_COMMIT',
        accountId: 'FACULTY-KUCET',
        sessionId: state.sessionId,
        idempotencyKey: idempotencyKey,
        payload: {
          'session_id': state.sessionId,
          'conducted_units_count': state.conductedUnitsCount,
        },
        createdAt: DateTime.now(),
      ),
    );

    // Retain inReview state and set descriptive error message.
    state = state.copyWith(
      errorMessage:
          'Commit failed or server unreachable. Client-minted offline receipts are prohibited by institutional governance policy. Mutation queued in offline journal.',
    );
    return null;
  }

  /// Synchronizes pending mutations queued in the offline journal with the server.
  Future<int> syncOfflineJournal() async {
    final pending = _journal.getPendingMutationsForAccount('FACULTY-KUCET');
    int syncedCount = 0;
    for (final mutation in pending) {
      if (mutation.mutationType == 'SESSION_COMMIT') {
        final serverReceipt = await _api.commitSession(
          sessionId: mutation.sessionId,
          idempotencyKey: mutation.idempotencyKey,
          conductedUnitsCount: mutation.payload['conducted_units_count'] as int? ?? state.conductedUnitsCount,
          candidates: state.candidates,
        );
        if (serverReceipt != null) {
          _journal.markSynced(mutation.id);
          syncedCount++;
          if (mutation.sessionId == state.sessionId) {
            state = state.copyWith(
              state: SessionState.finalized,
              receipt: serverReceipt,
              errorMessage: null,
            );
          }
        } else {
          _journal.recordFailure(mutation.id, 'Connection unreachable during background sync');
        }
      }
    }
    return syncedCount;
  }

  /// P0.4: Explicit server query to verify/recover durable commit receipt without fabricating local state.
  Future<CommitReceiptResponse?> checkCommitReceiptStatus() async {
    if (state.sessionId.isEmpty) return null;
    final serverReceipt = await _api.getSessionReceipt(state.sessionId);
    if (serverReceipt != null) {
      state = state.copyWith(
        state: SessionState.finalized,
        receipt: serverReceipt,
        errorMessage: null,
      );
      return serverReceipt;
    }
    return null;
  }

  void resetSession() {
    state = const SessionWorkflowState();
  }
}

final sessionProvider = NotifierProvider<SessionNotifier, SessionWorkflowState>(SessionNotifier.new);

final assignedOfferingsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = FrsApiService();
  return api.getAssignedOfferings();
});


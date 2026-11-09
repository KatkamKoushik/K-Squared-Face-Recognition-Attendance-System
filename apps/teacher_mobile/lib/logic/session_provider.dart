import 'dart:io' as io;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../core/network/api_service.dart';
import '../core/network/offline_sync_journal.dart';
import '../data/models/domain_contracts.dart';

class SessionWorkflowState {
  final String sessionId;
  final String batchId;
  final Map<String, dynamic>? selectedOffering;
  final int conductedUnitsCount;
  final List<Map<String, dynamic>> capturedFrames;
  final SessionState state;
  final List<CandidateProposalItem> candidates;
  final List<UnassignedFaceObservation> unassignedObservations;
  final CommitReceiptResponse? receipt;
  final String? errorMessage;
  final String? uploadProgress;

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
    this.uploadProgress,
  });

  SessionWorkflowState copyWith({
    String? sessionId,
    String? batchId,
    Map<String, dynamic>? selectedOffering,
    int? conductedUnitsCount,
    List<Map<String, dynamic>>? capturedFrames,
    SessionState? state,
    List<CandidateProposalItem>? candidates,
    List<UnassignedFaceObservation>? unassignedObservations,
    CommitReceiptResponse? receipt,
    String? errorMessage,
    String? uploadProgress,
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
      errorMessage: errorMessage,
      uploadProgress: uploadProgress,
    );
  }
}

final apiProvider = Provider<FrsApiService>((ref) => FrsApiService());
final offlineSyncJournalProvider = ChangeNotifierProvider<OfflineSyncJournal>((ref) => OfflineSyncJournal());

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
      errorMessage: null,
    );

    // Register session on control-plane
    final offeringId = (offering['id'] ?? offering['offeringId']) as String? ?? 'OFF-CS401-2026';
    try {
      final serverId = await _api.createSession(
        offeringId: offeringId,
        plannedUnits: state.conductedUnitsCount,
      );
      if (serverId != null && serverId.isNotEmpty) {
        state = state.copyWith(sessionId: serverId);
      }
    } catch (e) {
      state = state.copyWith(
        errorMessage: 'Server session registration warning: ${e.toString().replaceFirst('Exception: ', '')}',
      );
    }
  }

  void setConductedUnits(int count) {
    if (count < 1 || count > 4) return;
    state = state.copyWith(conductedUnitsCount: count);
  }

  void addCapturedFrame({
    required String frameId,
    required String hash,
    String? path,
    List<int>? bytes,
  }) {
    final updated = List<Map<String, dynamic>>.from(state.capturedFrames)
      ..add({
        'frameId': frameId,
        'hash': hash,
        'path': path,
        'bytes': bytes,
        'time': DateTime.now().toIso8601String(),
      });
    state = state.copyWith(
      capturedFrames: updated,
      state: SessionState.capturing,
      errorMessage: null,
    );
  }

  void removeFrame(int index) {
    final updated = List<Map<String, dynamic>>.from(state.capturedFrames)..removeAt(index);
    state = state.copyWith(capturedFrames: updated);
  }

  /// P0-A: Sequential multipart upload of actual image bytes followed by live proposal polling.
  Future<void> submitBatchForProcessing() async {
    if (state.capturedFrames.isEmpty && _api.liveDemoMode) {
      state = state.copyWith(errorMessage: 'Please capture at least one classroom photograph.');
      return;
    }

    state = state.copyWith(
      state: SessionState.processing,
      uploadProgress: state.capturedFrames.isNotEmpty
          ? 'Preparing ${state.capturedFrames.length} photos for upload...'
          : 'Processing classroom proposal...',
      errorMessage: null,
    );

    try {
      // 1. Upload every frame's real image bytes
      for (int i = 0; i < state.capturedFrames.length; i++) {
        final frame = state.capturedFrames[i];
        state = state.copyWith(
          uploadProgress: 'Uploading classroom photo ${i + 1} of ${state.capturedFrames.length}...',
        );

        List<int>? bytes = frame['bytes'] as List<int>?;
        if (bytes == null && frame['path'] != null) {
          final file = io.File(frame['path'] as String);
          if (await file.exists()) {
            bytes = await file.readAsBytes();
          }
        }

        if (bytes == null || bytes.isEmpty) {
          throw Exception('Could not read image bytes for frame ${frame['frameId']}.');
        }

        final success = await _api.uploadFrame(
          sessionId: state.sessionId,
          batchId: state.batchId,
          frameIndex: i,
          imageBytes: bytes,
          filename: 'frame_$i.jpg',
        );

        if (!success) {
          throw Exception('Upload failed for photo ${i + 1} (${frame['frameId']}). Server rejected or unreachable.');
        }
      }

      // 2. Poll proposal for live worker reconciliation
      state = state.copyWith(
        uploadProgress: 'Vision worker analyzing classroom faces (YuNet + SFace)...',
      );

      final proposalData = await _api.pollProposalData(
        sessionId: state.sessionId,
        maxAttempts: 6,
        interval: const Duration(seconds: 1),
      );

      final List<dynamic> rawCandidates = proposalData['candidates'] ?? [];
      final candidates = rawCandidates.map((item) {
        final c = CandidateProposalItem.fromJson(item as Map<String, dynamic>);
        if (c.unitAttendance.isEmpty && c.proposalStatus != null) {
          final defaultUnits = <int, AttendanceStatus>{};
          for (int u = 1; u <= state.conductedUnitsCount; u++) {
            defaultUnits[u] = c.proposalStatus!;
          }
          return c.copyWith(unitAttendance: defaultUnits);
        }
        return c;
      }).toList();

      final List<dynamic> rawUnknowns = proposalData['unknown_faces'] ?? [];
      final unknowns = rawUnknowns
          .map((item) => UnassignedFaceObservation.fromJson(item as Map<String, dynamic>))
          .toList();

      state = state.copyWith(
        state: SessionState.inReview,
        candidates: candidates,
        unassignedObservations: unknowns,
        uploadProgress: null,
        errorMessage: null,
      );
    } catch (e) {
      state = state.copyWith(
        state: _api.liveDemoMode ? SessionState.capturing : SessionState.inReview,
        uploadProgress: null,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
      if (_api.liveDemoMode) rethrow;
    }
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

    // Ensure all decisions are populated from proposalStatus if untouched
    final resolvedCandidates = state.candidates.map((c) {
      final units = Map<int, AttendanceStatus>.from(c.unitAttendance);
      for (int i = 1; i <= state.conductedUnitsCount; i++) {
        units[i] ??= c.proposalStatus ?? AttendanceStatus.absentConfirmed;
      }
      return c.copyWith(unitAttendance: units);
    }).toList();
    state = state.copyWith(candidates: resolvedCandidates);

    final serverReceipt = await _api.commitSession(
      sessionId: state.sessionId,
      idempotencyKey: idempotencyKey,
      conductedUnitsCount: state.conductedUnitsCount,
      candidates: resolvedCandidates,
    );

    if (serverReceipt != null) {
      state = state.copyWith(
        state: SessionState.finalized,
        receipt: serverReceipt,
        errorMessage: null,
      );
      return serverReceipt;
    }

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

    state = state.copyWith(
      errorMessage:
          'Commit failed or server unreachable. Client-minted offline receipts are prohibited by institutional governance policy. Mutation queued in offline journal.',
    );
    return null;
  }

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
  final api = ref.watch(apiProvider);
  return api.getAssignedOfferings();
});

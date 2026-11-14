import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:flutter/foundation.dart';

/// Lifecycle state of a queued offline mutation.
enum MutationSyncStatus {
  pending,
  syncing,
  synced,
  failedRetryable,
  failedTerminal,
}

/// Strongly-typed offline mutation record adhering to Checklist Controls 20-N001 & 20-N002.
class QueuedMutation {
  final String id;
  final String mutationType; // e.g. "MANUAL_ATTENDANCE", "SESSION_COMMIT"
  final String accountId; // Bound teacher user ID (Checklist 20-N006)
  final String sessionId;
  final String idempotencyKey;
  final Map<String, dynamic> payload;
  final DateTime createdAt;
  DateTime? lastAttemptedAt;
  int attemptCount;
  MutationSyncStatus status;
  String? lastErrorMessage;

  QueuedMutation({
    required this.id,
    required this.mutationType,
    required this.accountId,
    required this.sessionId,
    required this.idempotencyKey,
    required this.payload,
    required this.createdAt,
    this.lastAttemptedAt,
    this.attemptCount = 0,
    this.status = MutationSyncStatus.pending,
    this.lastErrorMessage,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'mutation_type': mutationType,
        'account_id': accountId,
        'session_id': sessionId,
        'idempotency_key': idempotencyKey,
        'payload': payload,
        'created_at': createdAt.toIso8601String(),
        'last_attempted_at': lastAttemptedAt?.toIso8601String(),
        'attempt_count': attemptCount,
        'status': status.name,
        'last_error_message': lastErrorMessage,
      };

  factory QueuedMutation.fromJson(Map<String, dynamic> json) => QueuedMutation(
        id: json['id'] as String,
        mutationType: json['mutation_type'] as String,
        accountId: json['account_id'] as String,
        sessionId: json['session_id'] as String,
        idempotencyKey: json['idempotency_key'] as String,
        payload: json['payload'] as Map<String, dynamic>,
        createdAt: DateTime.parse(json['created_at'] as String),
        lastAttemptedAt: json['last_attempted_at'] != null
            ? DateTime.parse(json['last_attempted_at'] as String)
            : null,
        attemptCount: json['attempt_count'] as int? ?? 0,
        status: MutationSyncStatus.values.firstWhere(
          (s) => s.name == json['status'],
          orElse: () => MutationSyncStatus.pending,
        ),
        lastErrorMessage: json['last_error_message'] as String?,
      );
}

/// Storage interface for durable mutation persistence across app lifecycles.
abstract class JournalStorage {
  String? readJournalSync();
  void writeJournalSync(String data);
  void clearJournalSync();
}

/// Durable, atomic file storage using atomic rename to prevent corruption on sudden kills.
class FileJournalStorage implements JournalStorage {
  final File file;

  FileJournalStorage(this.file);

  @override
  String? readJournalSync() {
    try {
      if (file.existsSync()) {
        return file.readAsStringSync();
      }
    } catch (e) {
      debugPrint('FileJournalStorage read error: $e');
    }
    return null;
  }

  @override
  void writeJournalSync(String data) {
    try {
      final parentDir = file.parent;
      if (!parentDir.existsSync()) {
        parentDir.createSync(recursive: true);
      }
      final tmpFile = File('${file.path}.tmp');
      tmpFile.writeAsStringSync(data, flush: true);
      if (tmpFile.existsSync()) {
        tmpFile.renameSync(file.path);
      }
    } catch (e) {
      debugPrint('FileJournalStorage atomic write error: $e');
    }
  }

  @override
  void clearJournalSync() {
    try {
      if (file.existsSync()) {
        file.deleteSync();
      }
      final tmpFile = File('${file.path}.tmp');
      if (tmpFile.existsSync()) {
        tmpFile.deleteSync();
      }
    } catch (e) {
      debugPrint('FileJournalStorage clear error: $e');
    }
  }
}

/// Durable, bounded Offline Sync Operation Journal (Checklist Controls 20-N001 to 20-N016).
class OfflineSyncJournal extends ChangeNotifier {
  static const int maxQueueCapacity = 500; // Bounded storage (20-N005)
  static const int maxRetryAttempts = 5;

  final Map<String, QueuedMutation> _queue = {};
  final JournalStorage? storage;
  DateTime? _lastSuccessfulSyncAt;

  DateTime? get lastSuccessfulSyncAt => _lastSuccessfulSyncAt;
  int get queueLength => _queue.length;

  int get pendingCount => _queue.values
      .where((m) =>
          m.status == MutationSyncStatus.pending ||
          m.status == MutationSyncStatus.failedRetryable)
      .length;

  int get syncedCount =>
      _queue.values.where((m) => m.status == MutationSyncStatus.synced).length;

  OfflineSyncJournal({JournalStorage? storage, File? file})
      : storage = storage ?? (file != null ? FileJournalStorage(file) : null) {
    if (this.storage != null) {
      final raw = this.storage!.readJournalSync();
      if (raw != null && raw.trim().isNotEmpty) {
        try {
          deserialize(raw);
        } catch (e) {
          debugPrint('Failed to deserialize offline journal: $e');
        }
      }
    }
  }

  void _persist() {
    if (storage != null) {
      try {
        final data = serialize();
        storage!.writeJournalSync(data);
      } catch (e) {
        debugPrint('Failed to persist offline journal: $e');
      }
    }
  }

  /// Enqueue an offline mutation bound to the active teacher account (20-N002, 20-N006).
  bool enqueueMutation(QueuedMutation mutation) {
    if (_queue.length >= maxQueueCapacity) {
      // Reject when queue capacity is reached to prevent unbounded memory growth
      return false;
    }
    _queue[mutation.id] = mutation;
    _persist();
    notifyListeners();
    return true;
  }

  /// Retrieve mutations eligible for synchronization for the given account.
  List<QueuedMutation> getPendingMutationsForAccount(String currentAccountId) {
    return _queue.values
        .where((m) =>
            m.accountId == currentAccountId &&
            (m.status == MutationSyncStatus.pending ||
                m.status == MutationSyncStatus.failedRetryable))
        .toList();
  }

  /// Computes exponential backoff with jitter in milliseconds (20-N012).
  int calculateBackoffMs(int attemptCount, {int baseMs = 500, int maxMs = 30000}) {
    if (attemptCount <= 0) return 0;
    final exp = min(attemptCount, 6);
    final ceiling = min(baseMs * pow(2, exp).toInt(), maxMs);
    // Add 20% random jitter
    final randomJitter = Random().nextInt(max(1, (ceiling * 0.2).toInt()));
    return ceiling + randomJitter;
  }

  /// Mark mutation as successfully synced and update sync timestamp (20-N007, 20-N015).
  void markSynced(String mutationId) {
    final mutation = _queue[mutationId];
    if (mutation != null) {
      mutation.status = MutationSyncStatus.synced;
      _lastSuccessfulSyncAt = DateTime.now();
      _persist();
      notifyListeners();
    }
  }

  /// Mark mutation as failed with error details (20-N005, 20-N012).
  void recordFailure(String mutationId, String errorMessage, {bool isTerminal = false}) {
    final mutation = _queue[mutationId];
    if (mutation != null) {
      mutation.attemptCount += 1;
      mutation.lastAttemptedAt = DateTime.now();
      mutation.lastErrorMessage = errorMessage;
      if (isTerminal || mutation.attemptCount >= maxRetryAttempts) {
        mutation.status = MutationSyncStatus.failedTerminal;
      } else {
        mutation.status = MutationSyncStatus.failedRetryable;
      }
      _persist();
      notifyListeners();
    }
  }

  /// Purges all local data and mutations on teacher logout (20-N016).
  void purgeOnLogout() {
    _queue.clear();
    _lastSuccessfulSyncAt = null;
    if (storage != null) {
      storage!.clearJournalSync();
    }
    notifyListeners();
  }

  /// Export queue state to JSON string for persistent disk storage.
  String serialize() {
    final list = _queue.values.map((m) => m.toJson()).toList();
    return jsonEncode(list);
  }

  /// Restore queue state from persisted JSON string.
  void deserialize(String jsonStr) {
    _queue.clear();
    final list = jsonDecode(jsonStr) as List<dynamic>;
    for (final item in list) {
      final mutation = QueuedMutation.fromJson(item as Map<String, dynamic>);
      _queue[mutation.id] = mutation;
    }
    notifyListeners();
  }
}

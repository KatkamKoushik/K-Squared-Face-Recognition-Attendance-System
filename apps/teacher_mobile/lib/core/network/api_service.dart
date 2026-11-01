import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../data/models/domain_contracts.dart';
import '../../data/mock/mock_teacher_data.dart';

/// FRS API Service connecting Flutter Teacher Client to FastAPI Control Plane.
/// Conforms to canonical OpenAPI contracts and unwraps ResponseEnvelope wrappers.
/// Gracefully falls back to deterministic mock when backend is unreachable or offline.
class FrsApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  final http.Client _client;

  FrsApiService({http.Client? client}) : _client = client ?? http.Client();

  dynamic _unwrap(http.Response res) {
    final decoded = jsonDecode(res.body);
    if (decoded is Map<String, dynamic> && decoded.containsKey('data')) {
      return decoded['data'];
    }
    return decoded;
  }

  /// GET /academic/offerings
  Future<List<Map<String, dynamic>>> getAssignedOfferings() async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/academic/offerings'),
        headers: {'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is List) {
          return payload.cast<Map<String, dynamic>>();
        }
      }
    } catch (_) {
      // Fallback to local mock offerings
    }
    return MockTeacherData.sampleOfferings;
  }

  /// POST /sessions
  Future<String?> createSession({
    required String offeringId,
    required int plannedUnits,
  }) async {
    try {
      final res = await _client.post(
        Uri.parse('$baseUrl/sessions'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'offering_id': offeringId,
          'planned_units': plannedUnits,
        }),
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200 || res.statusCode == 201) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return payload['id'] as String?;
        }
      }
    } catch (_) {
      // Gracefully handle offline
    }
    return 'SES-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';
  }

  /// POST /sessions/{session_id}/batches/{batch_id}/frames
  Future<bool> uploadFrame({
    required String sessionId,
    required String batchId,
    required int frameIndex,
    required List<int> imageBytes,
    required String filename,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/sessions/$sessionId/batches/$batchId/frames');
      final request = http.MultipartRequest('POST', uri);
      request.fields['frame_index'] = frameIndex.toString();
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageBytes,
          filename: filename,
        ),
      );

      final streamedResponse = await _client.send(request).timeout(const Duration(seconds: 10));
      return streamedResponse.statusCode == 200 || streamedResponse.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  /// GET /sessions/{id}/proposal
  Future<List<CandidateProposalItem>> getSessionProposal(String sessionId) async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
        headers: {'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          final List<dynamic> list = payload['candidates'] ?? [];
          return list.map((item) => CandidateProposalItem.fromJson(item as Map<String, dynamic>)).toList();
        }
      }
    } catch (_) {
      // Fallback
    }
    return MockTeacherData.getInitialCandidates();
  }

  /// Asynchronous polling for vision worker processing completion
  Future<List<CandidateProposalItem>> pollProposal({
    required String sessionId,
    int maxAttempts = 3,
    Duration interval = const Duration(seconds: 1),
  }) async {
    for (int i = 0; i < maxAttempts; i++) {
      try {
        final res = await _client.get(
          Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
          headers: {'Accept': 'application/json'},
        ).timeout(const Duration(seconds: 3));

        if (res.statusCode == 200) {
          final payload = _unwrap(res);
          if (payload is Map<String, dynamic> && payload['candidates'] != null) {
            final List<dynamic> list = payload['candidates'];
            return list.map((item) => CandidateProposalItem.fromJson(item as Map<String, dynamic>)).toList();
          }
        }
      } catch (_) {
        // Retry
      }
      if (i < maxAttempts - 1) {
        await Future.delayed(interval);
      }
    }
    return MockTeacherData.getInitialCandidates();
  }

  /// POST /sessions/{id}/commit
  Future<CommitReceiptResponse?> commitSession({
    required String sessionId,
    required String idempotencyKey,
    required int conductedUnitsCount,
    required List<CandidateProposalItem> candidates,
  }) async {
    try {
      final decisions = <Map<String, dynamic>>[];
      for (final c in candidates) {
        for (int i = 1; i <= conductedUnitsCount; i++) {
          final status = c.unitAttendance[i] ?? AttendanceStatus.absentConfirmed;
          decisions.add({
            'student_id': c.studentId,
            'unit_index': i,
            'status': status.toWire(),
            'reason_code': 'FACULTY_COMMIT',
          });
        }
      }

      final res = await _client.post(
        Uri.parse('$baseUrl/sessions/$sessionId/commit'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'idempotency_key': idempotencyKey,
          'conducted_unit_indices': List.generate(conductedUnitsCount, (i) => i + 1),
          'decisions': decisions,
        }),
      ).timeout(const Duration(seconds: 5));

      if (res.statusCode == 200 || res.statusCode == 201) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return CommitReceiptResponse.fromJson(payload);
        }
      }
    } catch (_) {
      // Gracefully handle offline
    }
    return null;
  }
}

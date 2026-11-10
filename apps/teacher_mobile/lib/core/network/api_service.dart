import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../data/models/domain_contracts.dart';
import '../../data/mock/mock_teacher_data.dart';

/// FRS API Service connecting Flutter Teacher Client to FastAPI Control Plane.
/// Conforms to canonical OpenAPI contracts and unwraps ResponseEnvelope wrappers.
/// In live-demo mode, fails closed rather than returning mock proposals or fake receipts.
class FrsApiService {
  static const String defaultBaseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  String baseUrl;
  final http.Client _client;
  String? authToken;
  bool liveDemoMode;

  FrsApiService({
    String? baseUrl,
    http.Client? client,
    this.authToken,
    this.liveDemoMode = false,
  })  : baseUrl = baseUrl ?? defaultBaseUrl,
        _client = client ?? http.Client();

  Map<String, String> _headers({Map<String, String>? extra}) {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (authToken != null && authToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $authToken';
    }
    if (extra != null) {
      headers.addAll(extra);
    }
    return headers;
  }

  dynamic _unwrap(http.Response res) {
    final decoded = jsonDecode(res.body);
    if (decoded is Map<String, dynamic> && decoded.containsKey('data')) {
      return decoded['data'];
    }
    return decoded;
  }

  /// Verifies connectivity to the FastAPI control plane endpoint.
  Future<bool> checkConnection() async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/health/liveness'),
        headers: {'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (_) {
      try {
        final resAlt = await _client.get(
          Uri.parse('$baseUrl/health/readiness'),
          headers: {'Accept': 'application/json'},
        ).timeout(const Duration(seconds: 3));
        return resAlt.statusCode == 200;
      } catch (_) {
        return false;
      }
    }
  }

  /// POST /auth/login
  /// Authenticates faculty credentials against FastAPI control plane.
  Future<Map<String, dynamic>?> login({
    required String email,
    required String password,
  }) async {
    try {
      final res = await _client.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          authToken = payload['access_token'] as String?;
          return payload;
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    return null;
  }

  /// Clears active JWT session token.
  void logout() {
    authToken = null;
  }

  /// GET /academic/offerings
  Future<List<Map<String, dynamic>>> getAssignedOfferings() async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/academic/offerings'),
        headers: _headers(),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is List) {
          return payload.cast<Map<String, dynamic>>();
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    if (liveDemoMode) {
      throw Exception('Failed to load assigned subject offerings from backend ($baseUrl).');
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
        headers: _headers(),
        body: jsonEncode({
          'offering_id': offeringId,
          'planned_units': plannedUnits,
        }),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200 || res.statusCode == 201) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return payload['id'] as String?;
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    if (liveDemoMode) {
      throw Exception('Server session registration failed on $baseUrl.');
    }
    return 'SES-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';
  }

  /// POST /sessions/{session_id}/batches/{batch_id}/frames
  /// P0-A: Real multipart/form-data upload of camera image bytes.
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
      if (authToken != null && authToken!.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $authToken';
      }
      request.headers['Accept'] = 'application/json';
      request.fields['frame_index'] = frameIndex.toString();
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageBytes,
          filename: filename,
        ),
      );

      final streamedResponse = await _client.send(request).timeout(const Duration(seconds: 15));
      final res = await http.Response.fromStream(streamedResponse);
      return res.statusCode == 200 || res.statusCode == 201;
    } catch (e) {
      if (liveDemoMode) rethrow;
      return false;
    }
  }

  /// GET /sessions/{id}/proposal
  /// Retrieves live vision worker candidate proposals and unknown observations.
  Future<Map<String, dynamic>> getSessionProposalData(String sessionId) async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
        headers: _headers(),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return payload;
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    if (liveDemoMode) {
      throw Exception('Proposal retrieval failed on $baseUrl/sessions/$sessionId/proposal.');
    }
    return {
      'candidates': MockTeacherData.getInitialCandidates().map((c) => c.toJson()).toList(),
      'unknown_faces': <dynamic>[],
    };
  }

  /// Polling for vision worker processing completion.
  Future<Map<String, dynamic>> pollProposalData({
    required String sessionId,
    int maxAttempts = 6,
    Duration interval = const Duration(seconds: 1),
  }) async {
    final attempts = liveDemoMode ? maxAttempts : 2;
    final pollInterval = liveDemoMode ? interval : const Duration(milliseconds: 100);
    final timeoutDuration = liveDemoMode ? const Duration(seconds: 4) : const Duration(milliseconds: 500);

    for (int i = 0; i < attempts; i++) {
      try {
        final res = await _client.get(
          Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
          headers: _headers(),
        ).timeout(timeoutDuration);

        if (res.statusCode == 200) {
          final payload = _unwrap(res);
          if (payload is Map<String, dynamic> && payload['candidates'] != null) {
            final List<dynamic> list = payload['candidates'];
            // If candidates exist or vision frames are processed, return real data
            if (list.isNotEmpty || i == attempts - 1) {
              return payload;
            }
          }
        }
      } catch (e) {
        if (i == attempts - 1 && liveDemoMode) rethrow;
      }
      if (i < attempts - 1) {
        await Future.delayed(pollInterval);
      }
    }
    if (liveDemoMode) {
      throw Exception('Vision worker processing timed out for session $sessionId.');
    }
    return {
      'candidates': MockTeacherData.getInitialCandidates().map((c) => c.toJson()).toList(),
      'unknown_faces': <dynamic>[],
    };
  }

  /// POST /sessions/{id}/commit
  /// P0-G: Strict faculty adjudication. Zero silent defaults to absentConfirmed.
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
          final status = c.unitAttendance[i];
          if (status == null) {
            throw Exception('Cannot commit: Student ${c.rollNumber} has no explicit attendance decision for conducted unit $i.');
          }
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
        headers: _headers(),
        body: jsonEncode({
          'idempotency_key': idempotencyKey,
          'conducted_unit_indices': List.generate(conductedUnitsCount, (i) => i + 1),
          'decisions': decisions,
        }),
      ).timeout(liveDemoMode ? const Duration(seconds: 8) : const Duration(milliseconds: 500));

      if (res.statusCode == 200 || res.statusCode == 201) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return CommitReceiptResponse.fromJson(payload);
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    return null;
  }

  /// GET /sessions/{id}/receipt
  /// Queries the authoritative commit receipt from the server.
  Future<CommitReceiptResponse?> getSessionReceipt(String sessionId) async {
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/sessions/$sessionId/receipt'),
        headers: _headers(),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final payload = _unwrap(res);
        if (payload is Map<String, dynamic>) {
          return CommitReceiptResponse.fromJson(payload);
        }
      }
    } catch (e) {
      if (liveDemoMode) rethrow;
    }
    return null;
  }
}

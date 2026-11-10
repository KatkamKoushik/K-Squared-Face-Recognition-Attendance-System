import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../data/models/domain_contracts.dart';

/// FRS API Service connecting Flutter Teacher Client to FastAPI Control Plane.
/// Conforms to canonical OpenAPI contracts and unwraps ResponseEnvelope wrappers.
/// In live-demo mode, fails closed rather than returning mock proposals or fake receipts.
class SessionExpiredException implements Exception {
  final String message;
  const SessionExpiredException([this.message = 'Session expired. Please log in again.']);
  @override
  String toString() => message;
}

class FrsApiService {
  static const String defaultBaseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'https://straddle-deflate-footwear.ngrok-free.dev/api/v1',
  );

  String baseUrl;
  final http.Client _client;
  String? authToken;
  bool liveDemoMode;
  String? lastConnectionError;
  void Function()? onSessionExpired;

  FrsApiService({
    String? baseUrl,
    http.Client? client,
    this.authToken,
    this.liveDemoMode = true,
    this.onSessionExpired,
  })  : baseUrl = baseUrl ?? defaultBaseUrl,
        _client = client ?? http.Client();

  Map<String, String> _headers({Map<String, String>? extra}) {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    };
    if (authToken != null && authToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $authToken';
    }
    if (extra != null) {
      headers.addAll(extra);
    }
    return headers;
  }

  void _checkAuthError(http.Response res) {
    if (res.statusCode == 401) {
      authToken = null;
      onSessionExpired?.call();
      throw const SessionExpiredException();
    }
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
    lastConnectionError = null;
    try {
      final res = await _client.get(
        Uri.parse('$baseUrl/health/liveness'),
        headers: {'Accept': 'application/json', 'ngrok-skip-browser-warning': 'true'},
      ).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) return true;
      lastConnectionError = 'Liveness probe returned HTTP ${res.statusCode}: ${res.body}';
    } catch (e) {
      lastConnectionError = 'Liveness probe failed: ${e.toString().replaceFirst("Exception: ", "")}';
    }

    try {
      final resAlt = await _client.get(
        Uri.parse('$baseUrl/health/readiness'),
        headers: {'Accept': 'application/json', 'ngrok-skip-browser-warning': 'true'},
      ).timeout(const Duration(seconds: 4));
      if (resAlt.statusCode == 200) return true;
      lastConnectionError = 'Readiness probe returned HTTP ${resAlt.statusCode}: ${resAlt.body}';
      return false;
    } catch (eAlt) {
      lastConnectionError = eAlt.toString().replaceFirst("Exception: ", "");
      return false;
    }
  }

  /// POST /auth/login
  /// Authenticates faculty credentials against FastAPI control plane.
  Future<Map<String, dynamic>?> login({
    required String email,
    required String password,
  }) async {
    final res = await _client.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _headers(),
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    ).timeout(const Duration(seconds: 8));

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        authToken = payload['access_token'] as String?;
        return payload;
      }
    }

    String detail = 'HTTP ${res.statusCode}';
    try {
      final err = jsonDecode(res.body);
      if (err is Map && err.containsKey('detail')) {
        detail = err['detail'].toString();
      }
    } catch (_) {}
    throw Exception('Login rejected ($detail)');
  }

  /// Clears active JWT session token.
  void logout() {
    authToken = null;
  }

  /// GET /academic/offerings
  Future<List<Map<String, dynamic>>> getAssignedOfferings() async {
    final res = await _client.get(
      Uri.parse('$baseUrl/academic/offerings'),
      headers: _headers(),
    ).timeout(const Duration(seconds: 8));
    _checkAuthError(res);

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is List) {
        return payload.cast<Map<String, dynamic>>();
      }
    }
    throw Exception('Failed to load assigned subject offerings from $baseUrl (HTTP ${res.statusCode}): ${res.body}');
  }

  /// POST /sessions
  Future<String?> createSession({
    required String offeringId,
    required int plannedUnits,
  }) async {
    final res = await _client.post(
      Uri.parse('$baseUrl/sessions'),
      headers: _headers(),
      body: jsonEncode({
        'offering_id': offeringId,
        'planned_units': plannedUnits,
      }),
    ).timeout(const Duration(seconds: 8));
    _checkAuthError(res);

    if (res.statusCode == 200 || res.statusCode == 201) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        return payload['id'] as String?;
      }
    }
    throw Exception('Server session registration failed on $baseUrl (HTTP ${res.statusCode}): ${res.body}');
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
    final uri = Uri.parse('$baseUrl/sessions/$sessionId/batches/$batchId/frames');
    final request = http.MultipartRequest('POST', uri);
    if (authToken != null && authToken!.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $authToken';
    }
    request.headers['Accept'] = 'application/json';
    request.headers['ngrok-skip-browser-warning'] = 'true';
    request.fields['frame_index'] = frameIndex.toString();
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: filename,
      ),
    );

    final streamedResponse = await _client.send(request).timeout(const Duration(seconds: 20));
    final res = await http.Response.fromStream(streamedResponse);
    _checkAuthError(res);
    if (res.statusCode == 200 || res.statusCode == 201) {
      return true;
    }
    throw Exception('Photo upload rejected by server on $uri (HTTP ${res.statusCode}): ${res.body}');
  }

  /// GET /sessions/{id}/proposal
  /// Retrieves live vision worker candidate proposals and unknown observations.
  Future<Map<String, dynamic>> getSessionProposalData(String sessionId) async {
    final res = await _client.get(
      Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
      headers: _headers(),
    ).timeout(const Duration(seconds: 8));
    _checkAuthError(res);

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        return payload;
      }
    }
    throw Exception('Proposal retrieval failed on $baseUrl/sessions/$sessionId/proposal (HTTP ${res.statusCode}): ${res.body}');
  }

  /// Polling for vision worker processing completion.
  Future<Map<String, dynamic>> pollProposalData({
    required String sessionId,
    int maxAttempts = 6,
    Duration interval = const Duration(seconds: 1),
  }) async {
    Object? lastError;
    for (int i = 0; i < maxAttempts; i++) {
      try {
        final res = await _client.get(
          Uri.parse('$baseUrl/sessions/$sessionId/proposal'),
          headers: _headers(),
        ).timeout(const Duration(seconds: 4));
        _checkAuthError(res);

        if (res.statusCode == 200) {
          final payload = _unwrap(res);
          if (payload is Map<String, dynamic> && payload['candidates'] != null) {
            final List<dynamic> list = payload['candidates'];
            if (list.isNotEmpty || i == maxAttempts - 1) {
              return payload;
            }
          }
        } else {
          lastError = 'HTTP ${res.statusCode}: ${res.body}';
        }
      } catch (e) {
        lastError = e;
        if (i == maxAttempts - 1) rethrow;
      }
      if (i < maxAttempts - 1) {
        await Future.delayed(interval);
      }
    }
    final detail = lastError != null ? ' ($lastError)' : '';
    throw Exception('Vision worker processing timed out for session $sessionId on $baseUrl$detail.');
  }

  /// POST /sessions/{id}/commit
  /// P0-G: Strict faculty adjudication. Zero silent defaults to absentConfirmed.
  Future<CommitReceiptResponse?> commitSession({
    required String sessionId,
    required String idempotencyKey,
    required int conductedUnitsCount,
    required List<CandidateProposalItem> candidates,
  }) async {
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
    ).timeout(const Duration(seconds: 10));
    _checkAuthError(res);

    if (res.statusCode == 200 || res.statusCode == 201) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        return CommitReceiptResponse.fromJson(payload);
      }
    }
    throw Exception('Session commit failed on $baseUrl (HTTP ${res.statusCode}): ${res.body}');
  }

  /// GET /sessions/{id}/receipt
  /// Queries the authoritative commit receipt from the server.
  Future<CommitReceiptResponse?> getSessionReceipt(String sessionId) async {
    final res = await _client.get(
      Uri.parse('$baseUrl/sessions/$sessionId/receipt'),
      headers: _headers(),
    ).timeout(const Duration(seconds: 6));
    _checkAuthError(res);

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        return CommitReceiptResponse.fromJson(payload);
      }
    }
    throw Exception('Receipt query failed on $baseUrl (HTTP ${res.statusCode}): ${res.body}');
  }

  /// POST /demo/analyze
  /// Universal branch-agnostic demo photo analysis with visual bounding boxes and reconciliation.
  Future<DemoAnalysisResponse> analyzeDemoImage({
    required List<int> imageBytes,
    required String filename,
    double matchThreshold = 0.363,
    double marginThreshold = 0.10,
    double blurThreshold = 50.0,
  }) async {
    final uri = Uri.parse('$baseUrl/demo/analyze');
    final request = http.MultipartRequest('POST', uri);
    request.headers['Accept'] = 'application/json';
    request.headers['ngrok-skip-browser-warning'] = 'true';
    if (authToken != null && authToken!.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $authToken';
    }
    request.fields['match_threshold'] = matchThreshold.toString();
    request.fields['margin_threshold'] = marginThreshold.toString();
    request.fields['blur_threshold'] = blurThreshold.toString();
    request.files.add(
      http.MultipartFile.fromBytes('file', imageBytes, filename: filename),
    );

    final streamed = await _client.send(request).timeout(const Duration(seconds: 30));
    final res = await http.Response.fromStream(streamed);
    _checkAuthError(res);

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is Map<String, dynamic>) {
        return DemoAnalysisResponse.fromJson(payload);
      }
    }
    throw Exception('Demo photo analysis failed on $baseUrl (HTTP ${res.statusCode}): ${res.body}');
  }

  /// GET /demo/enrolled-students
  Future<List<Map<String, dynamic>>> getDemoEnrolledStudents() async {
    final res = await _client.get(
      Uri.parse('$baseUrl/demo/enrolled-students'),
      headers: _headers(),
    ).timeout(const Duration(seconds: 6));
    _checkAuthError(res);

    if (res.statusCode == 200) {
      final payload = _unwrap(res);
      if (payload is List) {
        return payload.cast<Map<String, dynamic>>();
      }
    }
    throw Exception('Failed to load demo enrolled students (HTTP ${res.statusCode}): ${res.body}');
  }
}

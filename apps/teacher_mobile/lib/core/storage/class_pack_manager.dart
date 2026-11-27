import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../config/supabase_config.dart';
import '../database/local_database_service.dart';
import 'class_pack.dart';

/// Manages authorized downloadable class database packs.
/// Caches authorized student rosters and vector templates for offline recognition.
class ClassPackManager extends ChangeNotifier {
  static final ClassPackManager _instance = ClassPackManager._internal();
  factory ClassPackManager() => _instance;
  ClassPackManager._internal() {
    _packs = ClassDataPack.sampleAuthorizedPacks;
    _syncWithLocalDatabase();
  }

  late List<ClassDataPack> _packs;
  final LocalDatabaseService _localDb = LocalDatabaseService();

  List<ClassDataPack> get packs => List.unmodifiable(_packs);
  int get downloadedCount => _packs.where((p) => p.isDownloaded).length;

  Future<void> _syncWithLocalDatabase() async {
    try {
      await _localDb.init();
      final rows = await _localDb.db.query('class_packs');
      for (final r in rows) {
        final pid = r['id'] as String;
        final isDown = (r['is_downloaded'] as int? ?? 0) == 1;
        final match = _packs.where((p) => p.id == pid);
        if (match.isNotEmpty) {
          match.first.isDownloaded = isDown;
          if (r['downloaded_at'] != null) {
            match.first.downloadedAt = DateTime.tryParse(r['downloaded_at'] as String);
          }
        }
      }
      notifyListeners();
    } catch (e) {
      debugPrint('[ClassPackManager] Local sync note: $e');
    }
  }

  /// Downloads authorized class roster and cryptographic embeddings into encrypted local storage.
  /// Free Fire-style expansion pack downloader with animated real-time progress.
  Future<void> downloadClassPack(String packId, {void Function(double progress)? onProgress}) async {
    final pack = _packs.firstWhere((p) => p.id == packId);

    try {
      // 1. Simulating initial handshake & stream setup
      onProgress?.call(0.15);
      await Future.delayed(const Duration(milliseconds: 150));

      Map<String, dynamic>? packData;

      // 2. Load from bundled asset or fetch live from Supabase cloud
      if (pack.assetPath != null) {
        onProgress?.call(0.40);
        final jsonStr = await rootBundle.loadString(pack.assetPath!);
        packData = json.decode(jsonStr) as Map<String, dynamic>;
        onProgress?.call(0.70);
      } else {
        // Fetch from Supabase Cloud directly over cellular / Wi-Fi
        onProgress?.call(0.35);
        packData = await _fetchFromSupabase(pack);
        onProgress?.call(0.75);
      }

      // 3. Write into Local Mobile SQLite Database
      await _localDb.installPackFromJson(packData);

      onProgress?.call(0.95);
      await Future.delayed(const Duration(milliseconds: 100));

      pack.isDownloaded = true;
      pack.downloadedAt = DateTime.now();
      onProgress?.call(1.0);
      notifyListeners();
    } catch (e) {
      debugPrint('[ClassPackManager] Failed to download pack $packId: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> _fetchFromSupabase(ClassDataPack pack) async {
    const supabaseUrl = SupabaseConfig.url;
    const supabaseKey = SupabaseConfig.publishableKey;
    final headers = {
      'apikey': supabaseKey,
      'Authorization': 'Bearer $supabaseKey',
    };

    final sResp = await http.get(
      Uri.parse('$supabaseUrl/rest/v1/students?select=id,roll_number,full_name&limit=50'),
      headers: headers,
    );
    final students = json.decode(sResp.body) as List<dynamic>;

    final pResp = await http.get(
      Uri.parse('$supabaseUrl/rest/v1/enrollment_profiles?select=student_id,embedding_namespace,embedding_dimension,vector_data'),
      headers: headers,
    );
    final profiles = json.decode(pResp.body) as List<dynamic>;

    final profilesByStudent = <String, Map<String, dynamic>>{};
    for (final p in profiles) {
      final sid = p['student_id'] as String;
      profilesByStudent.putIfAbsent(sid, () => {})[p['embedding_namespace'] as String] = {
        'dimension': p['embedding_dimension'],
        'vector': p['vector_data'],
      };
    }

    final packStudents = students.map((s) {
      final sid = s['id'] as String;
      return {
        'student_id': sid,
        'roll_number': s['roll_number'],
        'full_name': s['full_name'],
        'department': pack.department,
        'academic_year': pack.academicYear,
        'section': pack.section,
        'portrait_base64': '',
        'embeddings': profilesByStudent[sid] ?? {},
      };
    }).toList();

    return {
      'pack_id': pack.id,
      'title': pack.title,
      'department': pack.department,
      'academic_year': pack.academicYear,
      'section': pack.section,
      'subject_code': pack.subjectCode,
      'subject_name': pack.subjectName,
      'student_count': packStudents.length,
      'students': packStudents,
    };
  }

  /// Removes an offline class pack to free local device space.
  Future<void> removeClassPack(String packId) async {
    final pack = _packs.firstWhere((p) => p.id == packId);
    await _localDb.removePack(packId);
    pack.isDownloaded = false;
    pack.downloadedAt = null;
    notifyListeners();
  }
}

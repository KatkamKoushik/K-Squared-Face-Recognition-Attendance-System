import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite_sqlcipher/sqflite.dart';

/// Local SQLite Database & Vector Matcher Service for K² FRS Mobile.
/// Enables 100% offline biometric attendance verification running on mobile ARM processors.
class LocalDatabaseService {
  static final LocalDatabaseService _instance = LocalDatabaseService._internal();
  factory LocalDatabaseService() => _instance;
  LocalDatabaseService._internal();

  Database? _db;
  bool _isInitialized = false;

  Database get db {
    if (_db == null) {
      throw StateError('LocalDatabaseService is not initialized. Call init() first.');
    }
    return _db!;
  }

  bool get isInitialized => _isInitialized;

  /// Initializes the local SQLite database and pre-seeds bundled packs if needed.
  Future<void> init() async {
    if (_isInitialized) return;

    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, 'kucet_frs_offline.db');

    _db = await openDatabase(
      path,
      version: 3,
      onCreate: (db, version) async {
        await _createTables(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 3) {
          await db.execute('DROP TABLE IF EXISTS student_embeddings');
          await db.execute('DROP TABLE IF EXISTS enrolled_students');
          await db.execute('DROP TABLE IF EXISTS class_packs');
          await _createTables(db);
        }
      },
    );

    _isInitialized = true;
    debugPrint('[LocalDatabaseService] SQLite database opened at: $path');

    // Auto-seed authentic bundled institutional packs matching Supabase
    await _autoSeedBundledPack();
  }

  Future<void> _createTables(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS class_packs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        section TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        enrolled_student_count INTEGER NOT NULL,
        embeddings_count INTEGER NOT NULL,
        size_bytes INTEGER NOT NULL,
        is_downloaded INTEGER NOT NULL DEFAULT 0,
        downloaded_at TEXT
      )
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS enrolled_students (
        student_id TEXT PRIMARY KEY,
        pack_id TEXT NOT NULL,
        roll_number TEXT NOT NULL,
        full_name TEXT NOT NULL,
        department TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        section TEXT NOT NULL,
        portrait_base64 TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
      )
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS student_embeddings (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        namespace TEXT NOT NULL,
        dimension INTEGER NOT NULL,
        vector_json TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES enrolled_students (student_id) ON DELETE CASCADE
      )
    ''');

    await db.execute('CREATE INDEX IF NOT EXISTS idx_emb_ns ON student_embeddings (namespace)');
    await db.execute('CREATE INDEX IF NOT EXISTS idx_emb_student ON student_embeddings (student_id)');
  }

  Future<void> _autoSeedBundledPack() async {
    const bundledPacks = [
      ('pack_civil_first_year', 'assets/packs/pack_civil_first_year.json'),
      ('pack_cse_final_year', 'assets/packs/pack_cse_final_year.json'),
      ('pack_csd_third_year', 'assets/packs/pack_csd_third_year.json'),
      ('pack_civil_final_year', 'assets/packs/pack_civil_final_year.json'),
      ('pack_mech_final_year', 'assets/packs/pack_mech_final_year.json'),
    ];

    try {
      for (final (packId, assetPath) in bundledPacks) {
        final count = Sqflite.firstIntValue(
          await _db!.rawQuery('SELECT COUNT(*) FROM class_packs WHERE id = ? AND is_downloaded = 1', [packId]),
        );
        if (count == null || count == 0) {
          debugPrint('[LocalDatabaseService] Seeding authentic pack $packId...');
          final jsonStr = await rootBundle.loadString(assetPath);
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          await installPackFromJson(data);
        }
      }
    } catch (e) {
      debugPrint('[LocalDatabaseService] Auto-seed note: $e');
    }
  }

  /// Installs or updates a class database pack into local SQLite storage.
  Future<void> installPackFromJson(Map<String, dynamic> packData) async {
    final database = db;
    final packId = packData['pack_id'] as String? ?? 'pack_cse_first_year';
    final students = packData['students'] as List<dynamic>? ?? [];

    await database.transaction((txn) async {
      // 1. Upsert pack metadata
      await txn.insert(
        'class_packs',
        {
          'id': packId,
          'title': packData['title'] ?? 'B.Tech CSE — First Year',
          'department': packData['department'] ?? 'CSE',
          'academic_year': packData['academic_year'] ?? 'First Year',
          'section': packData['section'] ?? 'Section A',
          'subject_code': packData['subject_code'] ?? 'CS101',
          'subject_name': packData['subject_name'] ?? 'Programming & Problem Solving',
          'enrolled_student_count': students.length,
          'embeddings_count': students.length * 2,
          'size_bytes': packData['size_bytes'] ?? 485990,
          'is_downloaded': 1,
          'downloaded_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );

      // 2. Insert students & embeddings
      for (final s in students) {
        final studentMap = s as Map<String, dynamic>;
        final sid = studentMap['student_id'] as String;
        final roll = studentMap['roll_number'] as String;
        final name = studentMap['full_name'] as String;
        final dept = studentMap['department'] as String? ?? 'CSE';
        final yr = studentMap['academic_year'] as String? ?? 'First Year';
        final sec = studentMap['section'] as String? ?? 'Section A';
        final portrait = studentMap['portrait_base64'] as String? ?? '';

        await txn.insert(
          'enrolled_students',
          {
            'student_id': sid,
            'pack_id': packId,
            'roll_number': roll,
            'full_name': name,
            'department': dept,
            'academic_year': yr,
            'section': sec,
            'portrait_base64': portrait,
            'is_active': 1,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );

        final embeddings = studentMap['embeddings'] as Map<String, dynamic>? ?? {};
        for (final entry in embeddings.entries) {
          final ns = entry.key;
          final embObj = entry.value;
          List<dynamic> vector = [];
          int dim = 128;

          if (embObj is Map<String, dynamic>) {
            vector = embObj['vector'] as List<dynamic>? ?? [];
            dim = embObj['dimension'] as int? ?? vector.length;
          } else if (embObj is List) {
            vector = embObj;
            dim = vector.length;
          }

          if (vector.isNotEmpty) {
            await txn.insert(
              'student_embeddings',
              {
                'id': '${sid}_$ns',
                'student_id': sid,
                'namespace': ns,
                'dimension': dim,
                'vector_json': json.encode(vector),
              },
              conflictAlgorithm: ConflictAlgorithm.replace,
            );
          }
        }
      }
    });

    debugPrint('[LocalDatabaseService] Installed pack $packId with ${students.length} students.');
  }

  /// Removes a downloaded class pack from the local database.
  Future<void> removePack(String packId) async {
    final database = db;
    await database.transaction((txn) async {
      await txn.delete('student_embeddings', where: 'student_id IN (SELECT student_id FROM enrolled_students WHERE pack_id = ?)', whereArgs: [packId]);
      await txn.delete('enrolled_students', where: 'pack_id = ?', whereArgs: [packId]);
      await txn.update(
        'class_packs',
        {
          'is_downloaded': 0,
          'downloaded_at': null,
        },
        where: 'id = ?',
        whereArgs: [packId],
      );
    });
  }

  /// Retrieves enrolled students from local storage filtered strictly by academic year / cohort.
  Future<List<Map<String, dynamic>>> getLocalEnrolledStudents({
    String? departmentCode,
    String? academicYear,
    String? packId,
    String? modelNamespace,
  }) async {
    final database = db;
    String query = '''
      SELECT s.student_id, s.roll_number, s.full_name, s.department, s.academic_year, s.portrait_base64
      FROM enrolled_students s
      WHERE s.is_active = 1
    ''';
    List<dynamic> args = [];

    if (packId != null && packId.isNotEmpty) {
      query += ' AND s.pack_id = ?';
      args.add(packId);
    } else if (academicYear != null && academicYear.isNotEmpty) {
      if (academicYear != 'ALL') {
        query += ' AND s.academic_year = ?';
        args.add(academicYear);
      }
      // If academicYear == 'ALL', do not filter by academic_year
    } else {
      // Return all active cohorts when no filter specified
    }

    if (departmentCode != null && departmentCode.isNotEmpty && departmentCode != 'ALL') {
      query += ' AND s.department = ?';
      args.add(departmentCode);
    }

    query += ' ORDER BY s.roll_number ASC';
    final rows = await database.rawQuery(query, args);

    return rows.map((r) => {
      'student_id': r['student_id'],
      'roll_number': r['roll_number'],
      'full_name': r['full_name'],
      'department': r['department'],
      'academic_year': r['academic_year'],
      'portrait_base64': r['portrait_base64'],
      'portrait_url': null,
    }).toList();
  }

  /// Performs vector search across all local templates in mobile RAM using Cosine Similarity.
  Future<Map<String, dynamic>?> matchVector({
    required List<double> queryVector,
    required String namespace,
    String academicYear = 'First Year',
    double matchThreshold = 0.380,
    double marginThreshold = 0.080,
  }) async {
    final database = db;

    final rows = await database.rawQuery('''
      SELECT e.student_id, e.vector_json, s.roll_number, s.full_name, s.portrait_base64
      FROM student_embeddings e
      JOIN enrolled_students s ON e.student_id = s.student_id
      WHERE e.namespace = ? AND s.academic_year = ? AND s.is_active = 1
    ''', [namespace, academicYear]);

    if (rows.isEmpty) return null;

    double bestSim = -1.0;
    Map<String, dynamic>? bestMatch;
    double runnerUpSim = -1.0;

    for (final row in rows) {
      final vecList = (json.decode(row['vector_json'] as String) as List)
          .map((v) => (v as num).toDouble())
          .toList();

      final sim = computeCosineSimilarity(queryVector, vecList);

      if (sim > bestSim) {
        runnerUpSim = bestSim;
        bestSim = sim;
        bestMatch = row;
      } else if (sim > runnerUpSim) {
        runnerUpSim = sim;
      }
    }

    if (bestMatch == null) return null;

    final margin = (runnerUpSim > -1.0) ? (bestSim - runnerUpSim) : 1.0;
    final isMatch = bestSim >= matchThreshold && margin >= marginThreshold;
    final isAmbiguous = bestSim >= matchThreshold && margin < marginThreshold;

    String status = 'STRANGER';
    String badge = 'STRANGER';

    if (isMatch) {
      status = 'PRESENT';
      badge = 'MATCHED';
    } else if (isAmbiguous) {
      status = 'AMBIGUOUS_LOOKALIKE_CONFLICT';
      badge = 'AMBIGUOUS';
    }

    return {
      'attendance_granted': isMatch,
      'status': status,
      'badge_label': badge,
      'student_id': bestMatch['student_id'],
      'roll_number': bestMatch['roll_number'],
      'full_name': bestMatch['full_name'],
      'portrait_base64': bestMatch['portrait_base64'],
      'similarity_score': bestSim,
      'margin': margin,
      'runner_up_similarity': runnerUpSim,
    };
  }

  /// Calculates Angular Cosine Similarity between two L2-normalized vectors.
  static double computeCosineSimilarity(List<double> a, List<double> b) {
    if (a.length != b.length) return 0.0;
    double dot = 0.0;
    double normA = 0.0;
    double normB = 0.0;

    for (int i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    if (normA == 0.0 || normB == 0.0) return 0.0;
    return dot / (sqrt(normA) * sqrt(normB));
  }
}

/// Offline Class Database Pack Specification for K² FRS.
/// Represents a scoped, authorized class database containing
/// student identity metadata, portrait thumbnails, and approved biometric embeddings.
class ClassDataPack {
  final String id;
  final String department;
  final String academicYear;
  final String section;
  final String subjectCode;
  final String subjectName;
  final int enrolledStudentCount;
  final int embeddingsCount;
  final int sizeBytes;
  final DateTime? expiresAt;
  final bool isBundled;
  final String? assetPath;
  bool isDownloaded;
  DateTime? downloadedAt;

  ClassDataPack({
    required this.id,
    required this.department,
    required this.academicYear,
    required this.section,
    required this.subjectCode,
    required this.subjectName,
    required this.enrolledStudentCount,
    required this.embeddingsCount,
    required this.sizeBytes,
    this.expiresAt,
    this.isBundled = false,
    this.assetPath,
    this.isDownloaded = false,
    this.downloadedAt,
  });

  String get title => '$department — $academicYear · $section';
  String get subtitle => '$subjectCode: $subjectName';

  String get formattedSize {
    if (sizeBytes < 1024 * 1024) {
      return '${(sizeBytes / 1024).toStringAsFixed(1)} KB';
    }
    return '${(sizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  static List<ClassDataPack> get sampleAuthorizedPacks => [
    ClassDataPack(
      id: 'pack_civil_first_year',
      department: 'CIVIL',
      academicYear: 'First Year',
      section: 'Class of 2030',
      subjectCode: 'CE101',
      subjectName: 'Engineering Mechanics & Surveying',
      enrolledStudentCount: 39,
      embeddingsCount: 156,
      sizeBytes: 486190,
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_civil_first_year.json',
    ),
    ClassDataPack(
      id: 'pack_cse_final_year',
      department: 'CSE',
      academicYear: 'Final Year',
      section: 'Class of 2026',
      subjectCode: 'CS401',
      subjectName: 'Distributed Cloud Architectures & AI',
      enrolledStudentCount: 4,
      embeddingsCount: 16,
      sizeBytes: 52077,
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_cse_final_year.json',
    ),
    ClassDataPack(
      id: 'pack_csd_third_year',
      department: 'CSD',
      academicYear: 'Third Year',
      section: 'Class of 2027',
      subjectCode: 'CD301',
      subjectName: 'Statistical Learning & Data Engineering',
      enrolledStudentCount: 2,
      embeddingsCount: 8,
      sizeBytes: 26192,
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_csd_third_year.json',
    ),
    ClassDataPack(
      id: 'pack_civil_final_year',
      department: 'CIVIL',
      academicYear: 'Final Year',
      section: 'Class of 2026',
      subjectCode: 'CE401',
      subjectName: 'Structural Analysis & Geotechnics',
      enrolledStudentCount: 2,
      embeddingsCount: 8,
      sizeBytes: 24195,
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_civil_final_year.json',
    ),
    ClassDataPack(
      id: 'pack_mech_final_year',
      department: 'MECH',
      academicYear: 'Final Year',
      section: 'Class of 2026',
      subjectCode: 'ME401',
      subjectName: 'Thermal Systems & CAD/CAM',
      enrolledStudentCount: 2,
      embeddingsCount: 8,
      sizeBytes: 24996,
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_mech_final_year.json',
    ),
  ];
}

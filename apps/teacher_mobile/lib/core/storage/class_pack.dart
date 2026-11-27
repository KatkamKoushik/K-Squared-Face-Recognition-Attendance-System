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
      id: 'pack_cse_first_year',
      department: 'CSE',
      academicYear: 'First Year',
      section: 'Class of 2030',
      subjectCode: 'CS101',
      subjectName: 'Programming & Problem Solving',
      enrolledStudentCount: 39,
      embeddingsCount: 156,
      sizeBytes: 485990, // ~475 KB
      isDownloaded: true,
      downloadedAt: DateTime.now(),
      isBundled: true,
      assetPath: 'assets/packs/pack_cse_first_year.json',
    ),
    ClassDataPack(
      id: 'pack_cse_third_year',
      department: 'CSE',
      academicYear: 'Third Year',
      section: 'Class of 2027',
      subjectCode: 'CS301',
      subjectName: 'Artificial Intelligence & Neural Networks',
      enrolledStudentCount: 10,
      embeddingsCount: 40,
      sizeBytes: 126464, // ~124 KB
      isDownloaded: false,
      isBundled: true,
      assetPath: 'assets/packs/pack_cse_third_year.json',
    ),
    ClassDataPack(
      id: 'pack_ece_4a',
      department: 'ECE',
      academicYear: '4th Year',
      section: 'Section A',
      subjectCode: 'EC401',
      subjectName: 'Embedded Systems & IoT Architectures',
      enrolledStudentCount: 42,
      embeddingsCount: 84,
      sizeBytes: 524288, // ~512 KB
      isDownloaded: false,
    ),
    ClassDataPack(
      id: 'pack_it_3a',
      department: 'IT',
      academicYear: '3rd Year',
      section: 'Section A',
      subjectCode: 'IT302',
      subjectName: 'Cloud Computing & Distributed Systems',
      enrolledStudentCount: 48,
      embeddingsCount: 96,
      sizeBytes: 589824, // ~576 KB
      isDownloaded: false,
    ),
  ];
}

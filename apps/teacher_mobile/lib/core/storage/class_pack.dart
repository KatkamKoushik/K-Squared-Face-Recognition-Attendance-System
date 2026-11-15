/// Offline Class Database Pack Specification for K² FRS.
/// Represents a scoped, authorized class database containing
/// student identity metadata and approved biometric embeddings.
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
      id: 'pack_cse_3a',
      department: 'CSE',
      academicYear: '3rd Year',
      section: 'Section A',
      subjectCode: 'CS301',
      subjectName: 'Artificial Intelligence & Neural Networks',
      enrolledStudentCount: 56,
      embeddingsCount: 56,
      sizeBytes: 819200, // ~800 KB
      isDownloaded: true,
      downloadedAt: DateTime.now().subtract(const Duration(days: 1)),
      expiresAt: DateTime.now().add(const Duration(days: 13)),
    ),
    ClassDataPack(
      id: 'pack_it_3a',
      department: 'IT',
      academicYear: '3rd Year',
      section: 'Section A',
      subjectCode: 'IT302',
      subjectName: 'Cloud Computing & Distributed Systems',
      enrolledStudentCount: 48,
      embeddingsCount: 48,
      sizeBytes: 716800, // ~700 KB
      isDownloaded: false,
    ),
    ClassDataPack(
      id: 'pack_cse_2b',
      department: 'CSE',
      academicYear: '2nd Year',
      section: 'Section B',
      subjectCode: 'CS204',
      subjectName: 'Database Management Systems',
      enrolledStudentCount: 62,
      embeddingsCount: 62,
      sizeBytes: 921600, // ~900 KB
      isDownloaded: false,
    ),
    ClassDataPack(
      id: 'pack_ece_4a',
      department: 'ECE',
      academicYear: '4th Year',
      section: 'Section A',
      subjectCode: 'EC401',
      subjectName: 'Embedded Systems & IoT Architectures',
      enrolledStudentCount: 42,
      embeddingsCount: 42,
      sizeBytes: 614400, // ~600 KB
      isDownloaded: false,
    ),
  ];
}

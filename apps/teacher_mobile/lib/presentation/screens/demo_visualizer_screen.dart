import 'dart:convert';
import 'dart:io' as io;
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/network/api_service.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/domain_contracts.dart';
import '../../logic/session_provider.dart';

class DemoVisualizerScreen extends ConsumerStatefulWidget {
  const DemoVisualizerScreen({super.key});

  @override
  ConsumerState<DemoVisualizerScreen> createState() => _DemoVisualizerScreenState();
}

class _DemoVisualizerScreenState extends ConsumerState<DemoVisualizerScreen> with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  Uint8List? _selectedImageBytes;
  String? _selectedImageName;
  bool _isAnalyzing = false;
  String? _errorMessage;
  DemoAnalysisResponse? _analysisResult;
  int? _selectedFaceIndex;
  late TabController _tabController;

  double _matchThreshold = 0.363;
  double _marginThreshold = 0.10;
  double _blurThreshold = 50.0;
  int _totalEnrolledStudents = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadEnrolledGalleryCount();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadEnrolledGalleryCount() async {
    try {
      final students = await ref.read(apiProvider).getDemoEnrolledStudents();
      if (mounted) {
        setState(() {
          _totalEnrolledStudents = students.length;
        });
      }
    } catch (_) {}
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 92,
      );
      if (file == null) return;

      final bytes = await file.readAsBytes();
      setState(() {
        _selectedImageBytes = bytes;
        _selectedImageName = file.name;
        _analysisResult = null;
        _selectedFaceIndex = null;
        _errorMessage = null;
      });

      await _runInference(bytes, file.name);
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Failed to load image: ${e.toString().replaceFirst("Exception: ", "")}';
        });
      }
    }
  }

  Future<void> _runInference(Uint8List bytes, String filename) async {
    setState(() {
      _isAnalyzing = true;
      _errorMessage = null;
    });

    try {
      final result = await ref.read(apiProvider).analyzeDemoImage(
        imageBytes: bytes,
        filename: filename,
        matchThreshold: _matchThreshold,
        marginThreshold: _marginThreshold,
        blurThreshold: _blurThreshold,
      );

      if (mounted) {
        setState(() {
          _analysisResult = result;
          _isAnalyzing = false;
          _totalEnrolledStudents = result.totalEnrolledStudents;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceFirst("Exception: ", "");
          _isAnalyzing = false;
        });
      }
    }
  }

  Color _parseHexColor(String hex) {
    try {
      final clean = hex.replaceAll('#', '');
      return Color(int.parse('FF$clean', radix: 16));
    } catch (_) {
      return Colors.blue;
    }
  }

  Widget _buildBase64Thumbnail(String? dataUri, {double size = 52, double radius = 8}) {
    if (dataUri == null || !dataUri.contains(',')) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(radius),
        ),
        child: Icon(Icons.person, size: size * 0.5, color: Colors.grey.shade400),
      );
    }
    try {
      final base64Str = dataUri.split(',').last;
      final bytes = base64Decode(base64Str);
      return ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: Image.memory(
          bytes,
          width: size,
          height: size,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Container(
            width: size,
            height: size,
            color: Colors.grey.shade200,
            child: Icon(Icons.broken_image, size: size * 0.4, color: Colors.grey),
          ),
        ),
      );
    } catch (_) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(radius),
        ),
        child: Icon(Icons.person, size: size * 0.5, color: Colors.grey.shade400),
      );
    }
  }

  void _showSettingsModal() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Calibration & Inference Parameters',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.primaryNavy),
                  ),
                  const SizedBox(height: 16),
                  Text('Cosine Match Threshold (\u03c4): ${_matchThreshold.toStringAsFixed(3)}'),
                  Slider(
                    value: _matchThreshold,
                    min: 0.25,
                    max: 0.60,
                    divisions: 35,
                    label: _matchThreshold.toStringAsFixed(3),
                    onChanged: (v) {
                      setModalState(() => _matchThreshold = v);
                      setState(() => _matchThreshold = v);
                    },
                  ),
                  Text('Separation Margin (\u0394s): ${_marginThreshold.toStringAsFixed(2)}'),
                  Slider(
                    value: _marginThreshold,
                    min: 0.05,
                    max: 0.25,
                    divisions: 20,
                    label: _marginThreshold.toStringAsFixed(2),
                    onChanged: (v) {
                      setModalState(() => _marginThreshold = v);
                      setState(() => _marginThreshold = v);
                    },
                  ),
                  Text('Laplacian Blur Rejection Threshold: ${_blurThreshold.toStringAsFixed(0)}'),
                  Slider(
                    value: _blurThreshold,
                    min: 10.0,
                    max: 100.0,
                    divisions: 18,
                    label: _blurThreshold.toStringAsFixed(0),
                    onChanged: (v) {
                      setModalState(() => _blurThreshold = v);
                      setState(() => _blurThreshold = v);
                    },
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        if (_selectedImageBytes != null && _selectedImageName != null) {
                          _runInference(_selectedImageBytes!, _selectedImageName!);
                        }
                      },
                      child: const Text('Apply & Re-analyze'),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ground-Truth Visualizer', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text(
              'Universal Test Sandbox (${_totalEnrolledStudents > 0 ? "$_totalEnrolledStudents Enrolled" : "All Branches"})',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.normal),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: 'Calibration Settings',
            onPressed: _showSettingsModal,
          ),
          IconButton(
            icon: const Icon(Icons.photo_library_outlined),
            tooltip: 'Pick from Gallery',
            onPressed: _isAnalyzing ? null : () => _pickImage(ImageSource.gallery),
          ),
          IconButton(
            icon: const Icon(Icons.camera_alt),
            tooltip: 'Take Photo',
            onPressed: _isAnalyzing ? null : () => _pickImage(ImageSource.camera),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_selectedImageBytes == null) {
      return _buildEmptyState();
    }

    return Column(
      children: [
        // Image Canvas with Bounding Boxes
        Expanded(
          flex: 5,
          child: Container(
            color: Colors.black,
            child: Stack(
              fit: StackFit.expand,
              children: [
                Center(
                  child: Image.memory(
                    _selectedImageBytes!,
                    fit: BoxFit.contain,
                  ),
                ),
                if (_analysisResult != null)
                  LayoutBuilder(
                    builder: (context, constraints) {
                      return CustomPaint(
                        size: Size(constraints.maxWidth, constraints.maxHeight),
                        painter: _FaceBoxesPainter(
                          detectedFaces: _analysisResult!.detectedFaces,
                          selectedFaceIndex: _selectedFaceIndex,
                          onFaceTap: (idx) {
                            setState(() {
                              _selectedFaceIndex = idx;
                            });
                          },
                        ),
                      );
                    },
                  ),
                if (_isAnalyzing)
                  Container(
                    color: Colors.black54,
                    child: Center(
                      child: Card(
                        color: Colors.white,
                        margin: const EdgeInsets.all(24),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: const [
                              CircularProgressIndicator(),
                              SizedBox(height: 16),
                              Text(
                                'YuNet & SFace Inference in Progress...',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Extracting 128-D embeddings and matching against PostgreSQL',
                                style: TextStyle(fontSize: 11, color: Colors.grey),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),

        // Metrics Banner
        if (_analysisResult != null) _buildMetricsSummaryBar(),

        // Reconciled Breakdown Tabs
        if (_analysisResult != null) ...[
          Container(
            color: Colors.white,
            child: TabBar(
              controller: _tabController,
              labelColor: AppTheme.primaryNavy,
              unselectedLabelColor: Colors.grey,
              indicatorColor: AppTheme.primaryNavy,
              tabs: [
                Tab(text: 'Granted (${_analysisResult!.presentCount})'),
                Tab(text: 'Absent (${_analysisResult!.absentCount})'),
                Tab(text: 'Strangers (${_analysisResult!.unknownCount})'),
              ],
            ),
          ),
          Expanded(
            flex: 4,
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildAttendanceGrantedList(),
                _buildAttendanceNotGrantedList(),
                _buildUnidentifiedFacesList(),
              ],
            ),
          ),
        ],

        if (_errorMessage != null)
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.red.shade50,
            child: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.red),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.camera_enhance_rounded, size: 64, color: AppTheme.primaryNavy),
            ),
            const SizedBox(height: 24),
            const Text(
              'Ground-Truth Face Visualizer',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppTheme.primaryNavy),
            ),
            const SizedBox(height: 8),
            Text(
              'Capture a group photo containing registered students and unregistered visitors. The system will circle each face with color-coded tags and prove who gets attendance and who is rejected.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.4),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFECFDF5),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.3)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.verified_user_outlined, size: 18, color: Color(0xFF10B981)),
                  const SizedBox(width: 8),
                  Text(
                    'Active Gallery: $_totalEnrolledStudents Enrolled Identities',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Take Camera Photo'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Pick from Gallery'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsSummaryBar() {
    final r = _analysisResult!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: Colors.white,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            _MetricPill(label: 'Faces Found', count: r.totalDetectedFaces, color: Colors.blueGrey),
            const SizedBox(width: 8),
            _MetricPill(label: 'Granted', count: r.presentCount, color: const Color(0xFF10B981)),
            const SizedBox(width: 8),
            _MetricPill(label: 'Absent', count: r.absentCount, color: Colors.orange.shade800),
            const SizedBox(width: 8),
            _MetricPill(label: 'Unknown Strangers', count: r.unknownCount, color: const Color(0xFFEF4444)),
          ],
        ),
      ),
    );
  }

  Widget _buildAttendanceGrantedList() {
    final granted = _analysisResult!.attendanceGranted;
    if (granted.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('No enrolled students were recognized in this photograph.'),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: granted.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final item = granted[index];
        return Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(color: const Color(0xFF10B981).withValues(alpha: 0.3)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                // Side-by-side evidence: Crop from photo vs Database reference
                Column(
                  children: [
                    _buildBase64Thumbnail(item.faceCropBase64, size: 48),
                    const SizedBox(height: 2),
                    const Text('Classroom Crop', style: TextStyle(fontSize: 8, color: Colors.grey)),
                  ],
                ),
                const SizedBox(width: 8),
                const Icon(Icons.compare_arrows, size: 16, color: Color(0xFF10B981)),
                const SizedBox(width: 8),
                Column(
                  children: [
                    _buildBase64Thumbnail(item.referencePhotoBase64, size: 48),
                    const SizedBox(height: 2),
                    const Text('DB Portrait', style: TextStyle(fontSize: 8, color: Colors.grey)),
                  ],
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item.fullName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      Text(item.rollNumber, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFFECFDF5),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'Sim: ${item.similarityScore?.toStringAsFixed(3) ?? "N/A"}',
                              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            'PRESENT',
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF10B981)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAttendanceNotGrantedList() {
    final absent = _analysisResult!.attendanceNotGranted;
    if (absent.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('All enrolled database students were detected present!'),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: absent.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final item = absent[index];
        return Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _buildBase64Thumbnail(item.referencePhotoBase64, size: 44),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item.fullName, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      Text(item.rollNumber, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    'ABSENT (Not in Photo)',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildUnidentifiedFacesList() {
    final unknown = _analysisResult!.unidentifiedFaces;
    if (unknown.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('Zero unknown persons or rejected faces detected in this photograph.'),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: unknown.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final item = unknown[index];
        final color = _parseHexColor(item.colorHex);
        return Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(color: color.withValues(alpha: 0.3)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _buildBase64Thumbnail(item.faceCropBase64, size: 48),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Face #${item.faceIndex} — ${item.status}',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: color),
                      ),
                      Text(
                        item.badgeLabel,
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Attendance NOT Granted',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.red.shade800),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _MetricPill extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _MetricPill({required this.label, required this.count, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('$count', style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 12)),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}

class _FaceBoxesPainter extends CustomPainter {
  final List<DemoFaceBox> detectedFaces;
  final int? selectedFaceIndex;
  final void Function(int) onFaceTap;

  _FaceBoxesPainter({
    required this.detectedFaces,
    required this.selectedFaceIndex,
    required this.onFaceTap,
  });

  Color _parseHex(String hex) {
    try {
      final clean = hex.replaceAll('#', '');
      return Color(int.parse('FF$clean', radix: 16));
    } catch (_) {
      return Colors.blue;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (final face in detectedFaces) {
      final box = face.box;
      final x1 = box[0] * size.width;
      final y1 = box[1] * size.height;
      final x2 = box[2] * size.width;
      final y2 = box[3] * size.height;

      final color = _parseHex(face.colorHex);
      final isSelected = selectedFaceIndex == face.faceIndex;

      // Draw bounding box / circle
      final paint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = isSelected ? 3.5 : 2.0;

      final rect = Rect.fromLTRB(x1, y1, x2, y2);
      canvas.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(6)), paint);

      // Draw badge tag above head
      final textSpan = TextSpan(
        text: face.badgeLabel,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      );
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();

      final badgeBgRect = Rect.fromLTWH(
        x1,
        (y1 - 18).clamp(0, size.height),
        textPainter.width + 8,
        16,
      );
      final bgPaint = Paint()..color = color.withValues(alpha: 0.9);
      canvas.drawRRect(RRect.fromRectAndRadius(badgeBgRect, const Radius.circular(4)), bgPaint);
      textPainter.paint(canvas, Offset(x1 + 4, (y1 - 17).clamp(0, size.height)));
    }
  }

  @override
  bool shouldRepaint(covariant _FaceBoxesPainter oldDelegate) {
    return oldDelegate.detectedFaces != detectedFaces || oldDelegate.selectedFaceIndex != selectedFaceIndex;
  }
}

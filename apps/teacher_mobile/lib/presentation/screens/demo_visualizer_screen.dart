import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/domain_contracts.dart';
import '../../logic/session_provider.dart';

enum OverlayDisplayMode {
  clean,     // Clean focus: compact student name pill on matched, minimal ? dot on unknown
  boxesOnly, // Colored bounding boxes only, zero text (100% face visibility)
  rawPhoto,  // Clean raw photograph without overlays
}

class SweepFrame {
  final Uint8List bytes;
  final String name;
  final Size? pixelSize;
  DemoAnalysisResponse? analysis;
  bool isAnalyzing;
  String? error;

  SweepFrame({
    required this.bytes,
    required this.name,
    this.pixelSize,
    this.analysis,
    this.isAnalyzing = false,
    this.error,
  });
}

class DemoVisualizerScreen extends ConsumerStatefulWidget {
  const DemoVisualizerScreen({super.key});

  @override
  ConsumerState<DemoVisualizerScreen> createState() => _DemoVisualizerScreenState();
}

class _DemoVisualizerScreenState extends ConsumerState<DemoVisualizerScreen> with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  final List<SweepFrame> _sweepFrames = [];
  int _activeFrameIndex = 0;
  OverlayDisplayMode _overlayMode = OverlayDisplayMode.clean;
  final TransformationController _transformController = TransformationController();

  int? _selectedFaceIndex;
  late TabController _tabController;

  double _matchThreshold = 0.460;
  double _marginThreshold = 0.10;
  double _blurThreshold = 50.0;
  int _totalEnrolledStudents = 0;
  String _selectedDepartment = 'ALL';
  final List<String> _departmentOptions = const ['ALL', 'CSD', 'CSE', 'ECE', 'MECH', 'EEE', 'CIVIL', 'IT'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadEnrolledGalleryCount();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _transformController.dispose();
    super.dispose();
  }

  SweepFrame? get _currentFrame =>
      _sweepFrames.isNotEmpty && _activeFrameIndex < _sweepFrames.length ? _sweepFrames[_activeFrameIndex] : null;

  Future<void> _loadEnrolledGalleryCount() async {
    try {
      final students = await ref.read(apiProvider).getDemoEnrolledStudents(
        departmentCode: _selectedDepartment,
      );
      if (mounted) {
        setState(() {
          _totalEnrolledStudents = students.length;
        });
      }
    } catch (_) {}
  }

  Future<void> _pickImage(ImageSource source) async {
    if (source == ImageSource.camera) {
      await _captureCameraPhoto();
    } else {
      await _pickGalleryImages();
    }
  }

  Future<void> _captureCameraPhoto() async {
    try {
      final XFile? file = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 92,
      );
      if (file == null) return;

      final bytes = await file.readAsBytes();
      final decoded = await decodeImageFromList(bytes);
      final size = Size(decoded.width.toDouble(), decoded.height.toDouble());
      final frame = SweepFrame(
        bytes: bytes,
        name: 'Sweep #${_sweepFrames.length + 1} (${file.name})',
        pixelSize: size,
        isAnalyzing: true,
      );

      setState(() {
        _sweepFrames.add(frame);
        _activeFrameIndex = _sweepFrames.length - 1;
        _selectedFaceIndex = null;
      });

      await _analyzeFrame(frame);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to capture photo: $e'), backgroundColor: AppTheme.errorRed),
        );
      }
    }
  }

  Future<void> _pickGalleryImages() async {
    try {
      final List<XFile> pickedFiles = await _picker.pickMultiImage(
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 88,
      );
      if (pickedFiles.isEmpty) return;

      final newFrames = <SweepFrame>[];
      for (final file in pickedFiles) {
        final bytes = await file.readAsBytes();
        final decoded = await decodeImageFromList(bytes);
        final size = Size(decoded.width.toDouble(), decoded.height.toDouble());
        final frame = SweepFrame(
          bytes: bytes,
          name: 'Sweep #${_sweepFrames.length + newFrames.length + 1} (${file.name})',
          pixelSize: size,
          isAnalyzing: true,
        );
        newFrames.add(frame);
      }

      setState(() {
        _sweepFrames.addAll(newFrames);
        _activeFrameIndex = _sweepFrames.length - 1;
        _selectedFaceIndex = null;
      });

      // Process frames sequentially to avoid saturating HTTP sockets and backend thread pool
      for (final frame in newFrames) {
        await _analyzeFrame(frame);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load gallery images: $e'), backgroundColor: AppTheme.errorRed),
        );
      }
    }
  }

  Future<void> _analyzeFrame(SweepFrame frame) async {
    try {
      final result = await ref.read(apiProvider).analyzeDemoImage(
        imageBytes: frame.bytes,
        filename: frame.name,
        matchThreshold: _matchThreshold,
        marginThreshold: _marginThreshold,
        blurThreshold: _blurThreshold,
        departmentCode: _selectedDepartment,
      );

      if (mounted) {
        setState(() {
          frame.analysis = result;
          frame.isAnalyzing = false;
          _totalEnrolledStudents = result.totalEnrolledStudents;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          frame.error = e.toString().replaceFirst("Exception: ", "");
          frame.isAnalyzing = false;
        });
      }
    }
  }

  Future<void> _reanalyzeAllFrames() async {
    for (final frame in _sweepFrames) {
      if (mounted) {
        setState(() {
          frame.isAnalyzing = true;
          frame.error = null;
        });
      }
      await _analyzeFrame(frame);
    }
  }

  // Multi-frame Consolidated Attendance Calculations
  List<DemoStudentResult> get _consolidatedGranted {
    final Map<String, DemoStudentResult> best = {};
    for (final frame in _sweepFrames) {
      if (frame.analysis == null) continue;
      for (final g in frame.analysis!.attendanceGranted) {
        if (!best.containsKey(g.studentId) || (g.similarityScore ?? 0) > (best[g.studentId]!.similarityScore ?? 0)) {
          best[g.studentId] = g;
        }
      }
    }
    final list = best.values.toList();
    list.sort((a, b) => a.rollNumber.compareTo(b.rollNumber));
    return list;
  }

  List<DemoStudentResult> get _consolidatedAbsent {
    if (_sweepFrames.isEmpty) return [];
    final grantedIds = _consolidatedGranted.map((g) => g.studentId).toSet();
    final Map<String, DemoStudentResult> absents = {};
    for (final frame in _sweepFrames) {
      if (frame.analysis == null) continue;
      for (final a in frame.analysis!.attendanceNotGranted) {
        if (!grantedIds.contains(a.studentId)) {
          absents[a.studentId] = a;
        }
      }
    }
    final list = absents.values.toList();
    list.sort((a, b) => a.rollNumber.compareTo(b.rollNumber));
    return list;
  }

  List<DemoFaceBox> get _activeFrameUnidentified {
    return _currentFrame?.analysis?.unidentifiedFaces ?? [];
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
                  const SizedBox(height: 14),
                  const Text('Roster Department Scope:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 6),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _departmentOptions.map((dept) {
                        final isSelected = _selectedDepartment == dept;
                        return Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: ChoiceChip(
                            label: Text(dept == 'ALL' ? 'All (Universal)' : dept),
                            selected: isSelected,
                            selectedColor: AppTheme.primaryNavy.withValues(alpha: 0.15),
                            labelStyle: TextStyle(
                              fontSize: 11,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              color: isSelected ? AppTheme.primaryNavy : Colors.black87,
                            ),
                            onSelected: (selected) {
                              if (selected) {
                                setModalState(() => _selectedDepartment = dept);
                                setState(() => _selectedDepartment = dept);
                                _loadEnrolledGalleryCount();
                              }
                            },
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text('Cosine Match Threshold (\u03c4): ${_matchThreshold.toStringAsFixed(3)} (Resolution-Adaptive)'),
                  Slider(
                    value: _matchThreshold,
                    min: 0.25,
                    max: 0.65,
                    divisions: 40,
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
                        _reanalyzeAllFrames();
                      },
                      child: const Text('Apply & Re-analyze All Frames'),
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
        title: const Text('Face Visualizer', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        actions: [
          if (_sweepFrames.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.add_photo_alternate_outlined),
              tooltip: 'Add Sweep Shot',
              onPressed: () => _pickGalleryImages(),
            ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Gallery & Re-Analyze',
            onPressed: () {
              _loadEnrolledGalleryCount();
              _reanalyzeAllFrames();
            },
          ),
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: 'Calibration Settings',
            onPressed: _showSettingsModal,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_sweepFrames.isEmpty) {
      return _buildEmptyState();
    }

    final currentFrame = _currentFrame;
    if (currentFrame == null) return const SizedBox.shrink();

    final result = currentFrame.analysis;

    return Column(
      children: [
        // Multi-Frame Sweep Strip (Filmstrip)
        if (_sweepFrames.length > 1) _buildSweepFilmstrip(),

        // Photo Canvas with Uncluttered Bounding Boxes
        Expanded(
          flex: 5,
          child: Container(
            color: Colors.black,
            child: Stack(
              children: [
                LayoutBuilder(
                  builder: (context, constraints) {
                    final Rect imageRect;
                    if (currentFrame.pixelSize != null &&
                        currentFrame.pixelSize!.width > 0 &&
                        currentFrame.pixelSize!.height > 0) {
                      final fitted = applyBoxFit(
                        BoxFit.contain,
                        currentFrame.pixelSize!,
                        Size(constraints.maxWidth, constraints.maxHeight),
                      );
                      final dx = (constraints.maxWidth - fitted.destination.width) / 2.0;
                      final dy = (constraints.maxHeight - fitted.destination.height) / 2.0;
                      imageRect = Rect.fromLTWH(dx, dy, fitted.destination.width, fitted.destination.height);
                    } else {
                      imageRect = Rect.fromLTWH(0, 0, constraints.maxWidth, constraints.maxHeight);
                    }

                    return InteractiveViewer(
                      transformationController: _transformController,
                      minScale: 1.0,
                      maxScale: 4.5,
                      clipBehavior: Clip.none,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Center(
                            child: Image.memory(
                              currentFrame.bytes,
                              fit: BoxFit.contain,
                            ),
                          ),
                          if (result != null)
                            GestureDetector(
                              behavior: HitTestBehavior.translucent,
                              onTapUp: (details) {
                                final pos = details.localPosition;
                                int? tappedIdx;
                                for (final face in result.detectedFaces) {
                                  final box = face.box;
                                  final x1 = imageRect.left + box[0] * imageRect.width;
                                  final y1 = imageRect.top + box[1] * imageRect.height;
                                  final x2 = imageRect.left + box[2] * imageRect.width;
                                  final y2 = imageRect.top + box[3] * imageRect.height;
                                  final hitRect = Rect.fromLTRB(x1 - 8, y1 - 8, x2 + 8, y2 + 8);
                                  if (hitRect.contains(pos)) {
                                    tappedIdx = face.faceIndex;
                                    break;
                                  }
                                }
                                setState(() {
                                  _selectedFaceIndex = tappedIdx == _selectedFaceIndex ? null : tappedIdx;
                                });
                              },
                              child: CustomPaint(
                                size: Size(constraints.maxWidth, constraints.maxHeight),
                                painter: _FaceBoxesPainter(
                                  detectedFaces: result.detectedFaces,
                                  selectedFaceIndex: _selectedFaceIndex,
                                  imageRect: imageRect,
                                  displayMode: _overlayMode,
                                  onFaceTap: (idx) {
                                    setState(() {
                                      _selectedFaceIndex = idx;
                                    });
                                  },
                                ),
                              ),
                            ),
                        ],
                      ),
                    );
                  },
                ),

                // Floating Overlay Mode Switcher Pill (Clean, Boxes Only, Raw Photo)
                Positioned(
                  top: 10,
                  right: 10,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.75),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.white24),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _buildModeButton(OverlayDisplayMode.clean, 'Pills', Icons.filter_center_focus),
                        _buildModeButton(OverlayDisplayMode.boxesOnly, 'Boxes', Icons.crop_free),
                        _buildModeButton(OverlayDisplayMode.rawPhoto, 'Photo', Icons.visibility_off_outlined),
                      ],
                    ),
                  ),
                ),

                // Selected Face Floating Inspector Card (Tap-to-Inspect)
                if (_selectedFaceIndex != null && result != null)
                  Positioned(
                    bottom: 10,
                    left: 12,
                    right: 12,
                    child: _buildSelectedFaceInspectionCard(result),
                  ),

                // Loading Spinner Overlay
                if (currentFrame.isAnalyzing)
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

        // Metrics Summary Bar (Single Frame or Multi-Frame Consolidated)
        _buildMetricsSummaryBar(),

        // Reconciled Breakdown Tabs
        Container(
          color: Colors.white,
          child: TabBar(
            controller: _tabController,
            labelColor: AppTheme.primaryNavy,
            unselectedLabelColor: Colors.grey,
            indicatorColor: AppTheme.primaryNavy,
            tabs: [
              Tab(text: 'Granted (${_consolidatedGranted.length})'),
              Tab(text: 'Absent (${_consolidatedAbsent.length})'),
              Tab(text: 'Strangers (${_activeFrameUnidentified.length})'),
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

        if (currentFrame.error != null)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: Colors.red.shade50,
            child: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.red, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(currentFrame.error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                ),
                TextButton.icon(
                  onPressed: () {
                    setState(() {
                      currentFrame.isAnalyzing = true;
                      currentFrame.error = null;
                    });
                    _analyzeFrame(currentFrame);
                  },
                  icon: const Icon(Icons.refresh, size: 16, color: Colors.red),
                  label: const Text('Retry', style: TextStyle(color: Colors.red, fontSize: 12, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildModeButton(OverlayDisplayMode mode, String label, IconData icon) {
    final isSelected = _overlayMode == mode;
    return GestureDetector(
      onTap: () {
        setState(() {
          _overlayMode = mode;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryNavy : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 12, color: isSelected ? Colors.white : Colors.white70),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? Colors.white : Colors.white70,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSweepFilmstrip() {
    return Container(
      color: Colors.grey.shade900,
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _sweepFrames.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, idx) {
                final frame = _sweepFrames[idx];
                final isSelected = idx == _activeFrameIndex;
                final faceCount = frame.analysis?.totalDetectedFaces ?? 0;

                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _activeFrameIndex = idx;
                      _selectedFaceIndex = null;
                      _transformController.value = Matrix4.identity();
                    });
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primaryNavy : Colors.grey.shade800,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isSelected ? const Color(0xFF10B981) : Colors.transparent,
                        width: 1.5,
                      ),
                    ),
                    child: Row(
                      children: [
                        if (frame.isAnalyzing)
                          const SizedBox(
                            width: 12,
                            height: 12,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        else
                          Icon(
                            Icons.photo_camera,
                            size: 13,
                            color: isSelected ? const Color(0xFF10B981) : Colors.white70,
                          ),
                        const SizedBox(width: 6),
                        Text(
                          'Shot #${idx + 1}',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            color: Colors.white,
                          ),
                        ),
                        if (frame.analysis != null) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                            decoration: BoxDecoration(
                              color: const Color(0xFF10B981).withValues(alpha: 0.3),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              '$faceCount faces',
                              style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Color(0xFF6EE7B7)),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.add_a_photo_outlined, size: 18, color: Colors.white70),
            tooltip: 'Add camera sweep frame',
            onPressed: () => _captureCameraPhoto(),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 18, color: Colors.redAccent),
            tooltip: 'Clear All Sweep Frames',
            onPressed: () {
              setState(() {
                _sweepFrames.clear();
                _activeFrameIndex = 0;
                _selectedFaceIndex = null;
              });
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSelectedFaceInspectionCard(DemoAnalysisResponse result) {
    final face = result.detectedFaces.firstWhere(
      (f) => f.faceIndex == _selectedFaceIndex,
      orElse: () => result.detectedFaces.first,
    );

    final isMatched = face.status == 'MATCHED';
    final color = _parseHexColor(face.colorHex);

    return Card(
      elevation: 6,
      color: Colors.white.withValues(alpha: 0.95),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: color, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildBase64Thumbnail(face.faceCropBase64, size: 44),
                const SizedBox(height: 2),
                const Text('Face Crop', style: TextStyle(fontSize: 8, color: Colors.grey)),
              ],
            ),
            if (isMatched && face.referencePhotoBase64 != null) ...[
              const SizedBox(width: 8),
              const Icon(Icons.sync_alt, size: 16, color: Color(0xFF10B981)),
              const SizedBox(width: 8),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildBase64Thumbnail(face.referencePhotoBase64, size: 44),
                  const SizedBox(height: 2),
                  const Text('DB Portrait', style: TextStyle(fontSize: 8, color: Colors.grey)),
                ],
              ),
            ],
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'Face #${face.faceIndex}',
                          style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: color),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        isMatched ? 'MATCHED' : face.status,
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    isMatched ? '${face.fullName} (${face.rollNumber})' : face.badgeLabel,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black87),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Similarity: ${face.similarityScore.toStringAsFixed(3)}  \u2022  Threshold: ${(face.effectiveThreshold ?? _matchThreshold).toStringAsFixed(3)}',
                    style: const TextStyle(fontSize: 9.5, color: Colors.black54),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.close, size: 18),
              onPressed: () {
                setState(() {
                  _selectedFaceIndex = null;
                });
              },
            ),
          ],
        ),
      ),
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
              'Capture a group photo or multi-photo sweep burst. The system detects faces with YuNet ONNX, extracts 128-D SFace embeddings, and matches against live PostgreSQL registered student identities.',
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
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 12,
              runSpacing: 12,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Take Photo'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Pick Gallery'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
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
    final granted = _consolidatedGranted;
    final absent = _consolidatedAbsent;
    final unknown = _activeFrameUnidentified;
    final totalSightings = _currentFrame?.analysis?.totalDetectedFaces ?? 0;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: Colors.white,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            if (_sweepFrames.length > 1) ...[
              _MetricPill(label: 'Sweep Frames', count: _sweepFrames.length, color: AppTheme.primaryNavy),
              const SizedBox(width: 8),
            ],
            _MetricPill(label: 'Faces in Frame', count: totalSightings, color: Colors.blueGrey),
            const SizedBox(width: 8),
            _MetricPill(label: 'Granted', count: granted.length, color: const Color(0xFF10B981)),
            const SizedBox(width: 8),
            _MetricPill(label: 'Absent', count: absent.length, color: Colors.orange.shade800),
            const SizedBox(width: 8),
            _MetricPill(label: 'Strangers', count: unknown.length, color: const Color(0xFFEF4444)),
          ],
        ),
      ),
    );
  }

  Widget _buildAttendanceGrantedList() {
    final granted = _consolidatedGranted;
    if (granted.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('No enrolled students were recognized in this sweep.'),
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
    final absent = _consolidatedAbsent;
    if (absent.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('All enrolled students in this cohort were observed and present!'),
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
            side: BorderSide(color: Colors.grey.shade300),
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _buildBase64Thumbnail(item.referencePhotoBase64, size: 48),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item.fullName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      Text(item.rollNumber, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                      if (item.departmentCode != null)
                        Text(item.departmentCode!, style: const TextStyle(fontSize: 10, color: Colors.blueGrey)),
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
                    'ABSENT',
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
    final unknown = _activeFrameUnidentified;
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
        final isSelected = _selectedFaceIndex == item.faceIndex;

        return GestureDetector(
          onTap: () {
            setState(() {
              _selectedFaceIndex = item.faceIndex;
            });
          },
          child: Card(
            elevation: 0,
            color: isSelected ? Colors.red.shade50 : Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: BorderSide(color: color.withValues(alpha: isSelected ? 0.8 : 0.3), width: isSelected ? 2 : 1),
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
  final Rect imageRect;
  final OverlayDisplayMode displayMode;
  final void Function(int) onFaceTap;

  _FaceBoxesPainter({
    required this.detectedFaces,
    required this.selectedFaceIndex,
    required this.imageRect,
    required this.displayMode,
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
    if (displayMode == OverlayDisplayMode.rawPhoto) {
      return; // 100% clean raw photo, zero overlays
    }

    for (final face in detectedFaces) {
      final box = face.box;
      final x1 = imageRect.left + box[0] * imageRect.width;
      final y1 = imageRect.top + box[1] * imageRect.height;
      final x2 = imageRect.left + box[2] * imageRect.width;
      final y2 = imageRect.top + box[3] * imageRect.height;

      final color = _parseHex(face.colorHex);
      final isSelected = selectedFaceIndex == face.faceIndex;
      final isMatched = face.status == 'MATCHED';

      // 1. Draw rounded bounding box
      final paint = Paint()
        ..color = isSelected ? Colors.white : color
        ..style = PaintingStyle.stroke
        ..strokeWidth = isSelected ? 3.5 : (isMatched ? 2.2 : 1.5);

      final rect = Rect.fromLTRB(x1, y1, x2, y2);
      canvas.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(6)), paint);

      // Selected face highlight ring
      if (isSelected) {
        final outerPaint = Paint()
          ..color = color.withValues(alpha: 0.5)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 5.0;
        canvas.drawRRect(RRect.fromRectAndRadius(rect.inflate(3), const Radius.circular(8)), outerPaint);
      }

      // If mode is boxesOnly, do NOT draw any text or badges
      if (displayMode == OverlayDisplayMode.boxesOnly) {
        continue;
      }

      // 2. Clean Overlay Mode (Minimal, uncluttered badges)
      if (isMatched) {
        // Draw compact student name pill (e.g. "Maneesh" or "Uma")
        final firstName = (face.fullName ?? 'Student').trim().split(' ').first;
        final labelText = firstName.length > 9 ? '${firstName.substring(0, 8)}..' : firstName;

        final textSpan = TextSpan(
          text: labelText,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 9.5,
            fontWeight: FontWeight.bold,
          ),
        );
        final textPainter = TextPainter(text: textSpan, textDirection: TextDirection.ltr);
        textPainter.layout();

        final pillW = textPainter.width + 10;
        const pillH = 15.0;
        final pillY = (y1 - 16).clamp(imageRect.top, imageRect.bottom - pillH);
        final pillX = x1.clamp(imageRect.left, imageRect.right - pillW);
        final pillRect = Rect.fromLTWH(pillX, pillY, pillW, pillH);

        final bgPaint = Paint()..color = const Color(0xFF10B981).withValues(alpha: 0.95);
        canvas.drawRRect(RRect.fromRectAndRadius(pillRect, const Radius.circular(4)), bgPaint);
        textPainter.paint(canvas, Offset(pillX + 5, pillY + 1));
      } else {
        // Stranger / Unknown: Draw only a tiny circular tag in the corner
        // NEVER draw a 250px wide sentence that blocks the faces!
        const dotSize = 14.0;
        final dotX = (x2 - dotSize + 2).clamp(imageRect.left, imageRect.right - dotSize);
        final dotY = (y1 - 6).clamp(imageRect.top, imageRect.bottom - dotSize);
        final dotRect = Rect.fromLTWH(dotX, dotY, dotSize, dotSize);

        final dotPaint = Paint()..color = color.withValues(alpha: 0.85);
        canvas.drawCircle(dotRect.center, dotSize / 2, dotPaint);

        final textSpan = const TextSpan(
          text: '?',
          style: TextStyle(
            color: Colors.white,
            fontSize: 8.5,
            fontWeight: FontWeight.bold,
          ),
        );
        final textPainter = TextPainter(text: textSpan, textDirection: TextDirection.ltr);
        textPainter.layout();
        textPainter.paint(
          canvas,
          Offset(dotRect.center.dx - textPainter.width / 2, dotRect.center.dy - textPainter.height / 2),
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant _FaceBoxesPainter oldDelegate) {
    return oldDelegate.detectedFaces != detectedFaces ||
        oldDelegate.selectedFaceIndex != selectedFaceIndex ||
        oldDelegate.imageRect != imageRect ||
        oldDelegate.displayMode != displayMode;
  }
}

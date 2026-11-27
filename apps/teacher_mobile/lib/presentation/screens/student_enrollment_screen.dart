import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme/app_theme.dart';
import '../../logic/session_provider.dart';

class StudentEnrollmentScreen extends ConsumerStatefulWidget {
  const StudentEnrollmentScreen({super.key});

  @override
  ConsumerState<StudentEnrollmentScreen> createState() => _StudentEnrollmentScreenState();
}

class _StudentEnrollmentScreenState extends ConsumerState<StudentEnrollmentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _rollController = TextEditingController();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();

  String _selectedDepartment = 'CSE';
  String _selectedAcademicYear = '2023-2027';

  final List<String> _departments = const [
    'CSE',
    'ECE',
    'EEE',
    'MECH',
    'CIVIL',
    'IT',
    'CSD',
  ];

  final List<String> _academicYears = const [
    '2023-2027',
    '2024-2028',
    '2022-2026',
    '2021-2025',
  ];

  final ImagePicker _picker = ImagePicker();
  Uint8List? _selectedPhotoBytes;
  String? _photoFileName;
  bool _isSubmitting = false;
  String? _statusMessage;
  String? _errorMessage;
  Map<String, dynamic>? _enrollmentResult;

  @override
  void dispose() {
    _rollController.dispose();
    _nameController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto(ImageSource source) async {
    setState(() {
      _errorMessage = null;
    });
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 98,
        preferredCameraDevice: CameraDevice.front,
      );
      if (file == null) return;

      final bytes = await file.readAsBytes();
      setState(() {
        _selectedPhotoBytes = bytes;
        _photoFileName = file.name;
        _enrollmentResult = null;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to capture or select image: ${e.toString().replaceFirst("Exception: ", "")}';
      });
    }
  }

  Future<void> _submitEnrollment() async {
    if (!_formKey.currentState!.validate()) return;

    if (_selectedPhotoBytes == null) {
      setState(() {
        _errorMessage = 'Face portrait photo is required. Please capture or select a photo.';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
      _statusMessage = 'Uploading to Cloudinary & computing multi-model embeddings...';
    });

    try {
      final api = ref.read(apiProvider);
      final result = await api.directEnrollStudent(
        rollNumber: _rollController.text.trim().toUpperCase(),
        fullName: _nameController.text.trim(),
        department: _selectedDepartment,
        academicYear: _selectedAcademicYear,
        institutionalEmail: _emailController.text.trim().isNotEmpty ? _emailController.text.trim() : null,
        photoBytes: _selectedPhotoBytes!,
        filename: _photoFileName ?? 'portrait_${_rollController.text.trim().toUpperCase()}.jpg',
      );

      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _statusMessage = null;
          _enrollmentResult = result;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _statusMessage = null;
          _errorMessage = e.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  void _resetForm() {
    setState(() {
      _rollController.clear();
      _nameController.clear();
      _emailController.clear();
      _selectedPhotoBytes = null;
      _photoFileName = null;
      _isSubmitting = false;
      _statusMessage = null;
      _errorMessage = null;
      _enrollmentResult = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Direct Student Enrollment',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              'RMX5003 Mobile Biometric Provisioning',
              style: TextStyle(fontSize: 10.5, color: Colors.white70),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Reset Form',
            onPressed: _resetForm,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // System Mode Header Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.primaryNavy.withValues(alpha: 0.05),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primaryNavy.withValues(alpha: 0.2)),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 22,
                      backgroundColor: AppTheme.primaryNavy,
                      child: const Icon(Icons.person_add_alt_1_rounded, color: Colors.white, size: 24),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'One-Click Direct Enrollment',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.primaryNavy),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Enrolls instantly to Cloudinary storage and registers separate embeddings for Option 1 (512-D), Option 3 (128-D) & Fine-Tuned (128-D).',
                            style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight, height: 1.3),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Success Banner & Details Card
              if (_enrollmentResult != null) ...[
                _buildSuccessCard(theme),
                const SizedBox(height: 24),
              ],

              // Error Banner
              if (_errorMessage != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppTheme.errorRed.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.errorRed.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline_rounded, color: AppTheme.errorRed, size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Enrollment Issue',
                              style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.errorRed, fontSize: 13),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              _errorMessage!,
                              style: const TextStyle(fontSize: 12, color: AppTheme.textMainLight),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // Enrollment Form
              Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Student Information',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),

                    // Roll Number Field
                    TextFormField(
                      controller: _rollController,
                      textCapitalization: TextCapitalization.characters,
                      decoration: const InputDecoration(
                        labelText: 'Roll Number / Student ID *',
                        hintText: 'e.g. 26567T0099',
                        prefixIcon: Icon(Icons.badge_outlined),
                        border: OutlineInputBorder(),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Please enter student roll number.';
                        }
                        if (val.trim().length < 3) {
                          return 'Roll number must be at least 3 characters.';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 16),

                    // Full Name Field
                    TextFormField(
                      controller: _nameController,
                      textCapitalization: TextCapitalization.words,
                      decoration: const InputDecoration(
                        labelText: 'Full Name *',
                        hintText: 'e.g. Katkam Koushik',
                        prefixIcon: Icon(Icons.person_outline),
                        border: OutlineInputBorder(),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Please enter student full name.';
                        }
                        if (val.trim().length < 2) {
                          return 'Name must be at least 2 characters.';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 16),

                    // Department & Academic Year Row
                    Row(
                      children: [
                        // Department Dropdown
                        Expanded(
                          flex: 5,
                          child: DropdownButtonFormField<String>(
                            value: _selectedDepartment,
                            isDense: true,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Dept *',
                              prefixIcon: Icon(Icons.apartment_outlined, size: 20),
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                            ),
                            items: _departments.map((dept) {
                              return DropdownMenuItem<String>(
                                value: dept,
                                child: Text(dept, style: const TextStyle(fontSize: 13.5)),
                              );
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) {
                                setState(() => _selectedDepartment = val);
                              }
                            },
                          ),
                        ),
                        const SizedBox(width: 10),

                        // Academic Year Dropdown
                        Expanded(
                          flex: 6,
                          child: DropdownButtonFormField<String>(
                            value: _selectedAcademicYear,
                            isDense: true,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Batch / Year',
                              prefixIcon: Icon(Icons.calendar_today_outlined, size: 20),
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                            ),
                            items: _academicYears.map((yr) {
                              return DropdownMenuItem<String>(
                                value: yr,
                                child: Text(yr, style: const TextStyle(fontSize: 13.5)),
                              );
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) {
                                setState(() => _selectedAcademicYear = val);
                              }
                            },
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // Institutional Email Field (Optional)
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Institutional Email (Optional)',
                        hintText: 'Auto-generated if left blank',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // Biometric Face Capture Section
                    Text(
                      'Biometric Portrait Photo',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Ensure student face is looking directly at camera in clear indoor lighting.',
                      style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight),
                    ),
                    const SizedBox(height: 12),

                    _buildPhotoSelectorCard(theme),

                    const SizedBox(height: 28),

                    // Action Button
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryNavy,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        icon: _isSubmitting
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.verified_user_rounded, size: 22),
                        label: Text(
                          _isSubmitting
                              ? (_statusMessage ?? 'Enrolling Student...')
                              : 'Enroll Student Directly',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        onPressed: _isSubmitting ? null : _submitEnrollment,
                      ),
                    ),

                    const SizedBox(height: 16),

                    Center(
                      child: Text(
                        'Direct enrollment active: Submits directly without secondary approval.',
                        style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight, fontSize: 11),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPhotoSelectorCard(ThemeData theme) {
    if (_selectedPhotoBytes != null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.surfaceLight,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.statusMatched, width: 1.5),
        ),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.memory(
                _selectedPhotoBytes!,
                width: 80,
                height: 96,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.check_circle_rounded, color: AppTheme.statusMatched, size: 18),
                      SizedBox(width: 6),
                      Text(
                        'Portrait Ready',
                        style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.statusMatched, fontSize: 14),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _photoFileName ?? 'Captured Photo',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      OutlinedButton.icon(
                        icon: const Icon(Icons.camera_alt_outlined, size: 14),
                        label: const Text('Retake', style: TextStyle(fontSize: 12)),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          minimumSize: const Size(0, 32),
                        ),
                        onPressed: () => _pickPhoto(ImageSource.camera),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.photo_library_outlined, size: 14),
                        label: const Text('Gallery', style: TextStyle(fontSize: 12)),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          minimumSize: const Size(0, 32),
                        ),
                        onPressed: () => _pickPhoto(ImageSource.gallery),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.borderLight, style: BorderStyle.solid),
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: AppTheme.primaryNavy.withValues(alpha: 0.08),
            child: const Icon(Icons.camera_enhance_outlined, size: 32, color: AppTheme.primaryNavy),
          ),
          const SizedBox(height: 12),
          const Text(
            'Select Student Portrait',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 4),
          const Text(
            'Capture live portrait with camera or select from gallery.',
            style: TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 18),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.camera_alt_outlined, size: 18),
                label: const Text('Camera'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryNavy,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                ),
                onPressed: () => _pickPhoto(ImageSource.camera),
              ),
              const SizedBox(width: 14),
              OutlinedButton.icon(
                icon: const Icon(Icons.photo_library_outlined, size: 18),
                label: const Text('Gallery'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                ),
                onPressed: () => _pickPhoto(ImageSource.gallery),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessCard(ThemeData theme) {
    final res = _enrollmentResult!;
    final roll = res['roll_number'] ?? '';
    final name = res['full_name'] ?? '';
    final dept = res['department'] ?? '';
    final photoUrl = res['cloudinary_photo_url'] as String? ?? '';
    final models = (res['models_enrolled'] as List?)?.cast<String>() ?? [];
    final namespaces = (res['namespaces'] as List?)?.cast<String>() ?? [];

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.statusMatched.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.statusMatched, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.verified_rounded, color: AppTheme.statusMatched, size: 24),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Student Enrolled Successfully',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppTheme.statusMatched,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '$name ($roll)',
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          Text(
            'Department: $dept | Batch: $_selectedAcademicYear',
            style: const TextStyle(fontSize: 13, color: AppTheme.textMutedLight),
          ),
          const SizedBox(height: 12),
          const Divider(),
          const SizedBox(height: 8),

          // Cloudinary Storage Status
          Row(
            children: [
              const Icon(Icons.cloud_done_rounded, color: AppTheme.secondaryBlue, size: 18),
              const SizedBox(width: 8),
              const Text(
                'Cloudinary Portrait URL:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 4),
          SelectableText(
            photoUrl,
            style: const TextStyle(fontSize: 11, color: AppTheme.secondaryBlue, fontFamily: 'monospace'),
          ),

          const SizedBox(height: 12),

          // Multi-Model Embeddings Status
          const Text(
            'Multi-Model Embeddings Registered:',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: List.generate(models.length, (idx) {
              final model = models[idx];
              final ns = idx < namespaces.length ? namespaces[idx] : '';
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primaryNavy.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppTheme.primaryNavy.withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.memory_rounded, size: 12, color: AppTheme.primaryNavy),
                    const SizedBox(width: 4),
                    Text(
                      ns.isNotEmpty ? '$model [$ns]' : model,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryNavy),
                    ),
                  ],
                ),
              );
            }),
          ),

          const SizedBox(height: 16),

          // Action buttons
          Row(
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.add_rounded, size: 16),
                label: const Text('Enroll Another Student'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.statusMatched,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                ),
                onPressed: _resetForm,
              ),
              const Spacer(),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Back to Home'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

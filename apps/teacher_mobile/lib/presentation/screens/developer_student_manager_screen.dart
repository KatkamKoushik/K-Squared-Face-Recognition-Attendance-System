import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme/app_theme.dart';
import '../../logic/session_provider.dart';

class DeveloperStudentManagerScreen extends ConsumerStatefulWidget {
  const DeveloperStudentManagerScreen({super.key});

  @override
  ConsumerState<DeveloperStudentManagerScreen> createState() => _DeveloperStudentManagerScreenState();
}

class _DeveloperStudentManagerScreenState extends ConsumerState<DeveloperStudentManagerScreen> {
  List<Map<String, dynamic>> _students = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _searchQuery = '';
  String _selectedDepartment = 'ALL';

  final List<String> _departments = const [
    'ALL',
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

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final api = ref.read(apiProvider);
      final list = await api.getDemoEnrolledStudents();
      setState(() {
        _students = list;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceFirst('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _filteredStudents {
    return _students.where((s) {
      final roll = (s['roll_number'] as String? ?? '').toUpperCase();
      final name = (s['full_name'] as String? ?? '').toUpperCase();
      final dept = (s['department_code'] as String? ?? 'CSE').toUpperCase();

      final matchesQuery = _searchQuery.isEmpty ||
          roll.contains(_searchQuery.toUpperCase()) ||
          name.contains(_searchQuery.toUpperCase());

      final matchesDept = _selectedDepartment == 'ALL' || dept == _selectedDepartment;

      return matchesQuery && matchesDept;
    }).toList();
  }

  void _openEditModal(Map<String, dynamic> student) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _StudentEditSheet(
        student: student,
        departments: _departments.where((d) => d != 'ALL').toList(),
        academicYears: _academicYears,
        onUpdated: () {
          Navigator.pop(ctx);
          _loadStudents();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _filteredStudents;

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Developer Database Control', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            Text(
              'koushikkatkam@gmail.com • Absolute Authority',
              style: TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Student Directory',
            onPressed: _loadStudents,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Developer Authority Banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              decoration: BoxDecoration(
                color: AppTheme.accentGold.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.accentGold.withValues(alpha: 0.35)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.admin_panel_settings_rounded, color: AppTheme.accentGold, size: 28),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          'Developer Database Control Active',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.primaryNavy),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Full permission: Rewrite names, alter branch/year, update photos from camera, and purge records.',
                          style: TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Search Bar & Department Filter
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: TextField(
                decoration: InputDecoration(
                  hintText: 'Search by student roll number or name...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  suffixIcon: _searchQuery.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () => setState(() => _searchQuery = ''),
                        )
                      : null,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  isDense: true,
                ),
                onChanged: (val) => setState(() => _searchQuery = val),
              ),
            ),

            // Department Filter Chips
            SizedBox(
              height: 42,
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                scrollDirection: Axis.horizontal,
                itemCount: _departments.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final dept = _departments[index];
                  final isSelected = _selectedDepartment == dept;
                  return ChoiceChip(
                    label: Text(dept, style: TextStyle(fontSize: 12, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal)),
                    selected: isSelected,
                    selectedColor: AppTheme.primaryNavy,
                    labelStyle: TextStyle(color: isSelected ? Colors.white : AppTheme.textMainLight),
                    onSelected: (selected) {
                      if (selected) setState(() => _selectedDepartment = dept);
                    },
                  );
                },
              ),
            ),

            const SizedBox(height: 4),

            // Students Count Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 4),
              child: Row(
                children: [
                  Text(
                    '${filtered.length} Student Record(s)',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMutedLight),
                  ),
                  const Spacer(),
                  const Text(
                    'Tap any student to edit or change photo',
                    style: TextStyle(fontSize: 11, color: AppTheme.secondaryBlue),
                  ),
                ],
              ),
            ),

            const Divider(height: 1),

            // Main Student List View
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _errorMessage != null
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.error_outline_rounded, color: AppTheme.errorRed, size: 36),
                                const SizedBox(height: 10),
                                Text(_errorMessage!, textAlign: TextAlign.center),
                                const SizedBox(height: 12),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.refresh, size: 16),
                                  label: const Text('Retry'),
                                  onPressed: _loadStudents,
                                ),
                              ],
                            ),
                          ),
                        )
                      : filtered.isEmpty
                          ? const Center(
                              child: Text(
                                'No students match current search filter.',
                                style: TextStyle(color: AppTheme.textMutedLight),
                              ),
                            )
                          : ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 8, 16, 20),
                              itemCount: filtered.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 10),
                              itemBuilder: (context, index) {
                                final s = filtered[index];
                                final roll = s['roll_number'] as String? ?? 'ROLL';
                                final name = s['full_name'] as String? ?? 'Student';
                                final dept = s['department_code'] as String? ?? 'CSE';
                                final photoB64 = s['reference_photo_base64'] as String?;
                                final hasPhoto = s['has_reference_photo'] as bool? ?? false;

                                return Card(
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    side: const BorderSide(color: AppTheme.borderLight),
                                  ),
                                  child: InkWell(
                                    borderRadius: BorderRadius.circular(12),
                                    onTap: () => _openEditModal(s),
                                    child: Padding(
                                      padding: const EdgeInsets.all(12),
                                      child: Row(
                                        children: [
                                          // Thumbnail
                                          ClipRRect(
                                            borderRadius: BorderRadius.circular(8),
                                            child: Container(
                                              width: 52,
                                              height: 58,
                                              color: Colors.grey.shade200,
                                              child: hasPhoto && photoB64 != null
                                                  ? Image.memory(
                                                      base64Decode(photoB64.split(',').last),
                                                      fit: BoxFit.cover,
                                                      errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 24),
                                                    )
                                                  : Center(
                                                      child: Text(
                                                        name.isNotEmpty ? name.substring(0, 1) : roll.substring(0, 2),
                                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: AppTheme.primaryNavy),
                                                      ),
                                                    ),
                                            ),
                                          ),
                                          const SizedBox(width: 14),

                                          // Details
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Row(
                                                  children: [
                                                    Text(
                                                      roll,
                                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, fontFamily: 'monospace'),
                                                    ),
                                                    const SizedBox(width: 8),
                                                    Container(
                                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                      decoration: BoxDecoration(
                                                        color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                                                        borderRadius: BorderRadius.circular(4),
                                                      ),
                                                      child: Text(
                                                        dept,
                                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10.5, color: AppTheme.primaryNavy),
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                                const SizedBox(height: 3),
                                                Text(
                                                  name,
                                                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                                                ),
                                                const SizedBox(height: 3),
                                                Row(
                                                  children: [
                                                    Icon(
                                                      hasPhoto ? Icons.check_circle_rounded : Icons.info_outline,
                                                      size: 13,
                                                      color: hasPhoto ? AppTheme.statusMatched : Colors.amber.shade800,
                                                    ),
                                                    const SizedBox(width: 4),
                                                    Text(
                                                      hasPhoto ? 'Multi-Model Enrolled' : 'Photo Purged / Missing',
                                                      style: TextStyle(
                                                        fontSize: 11,
                                                        color: hasPhoto ? AppTheme.statusMatched : Colors.amber.shade900,
                                                        fontWeight: FontWeight.w500,
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                              ],
                                            ),
                                          ),

                                          // Action Arrow / Edit Icon
                                          const Icon(Icons.edit_outlined, size: 20, color: AppTheme.secondaryBlue),
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Modal Sheet providing full developer rewrite and photo replacement powers.
class _StudentEditSheet extends ConsumerStatefulWidget {
  final Map<String, dynamic> student;
  final List<String> departments;
  final List<String> academicYears;
  final VoidCallback onUpdated;

  const _StudentEditSheet({
    required this.student,
    required this.departments,
    required this.academicYears,
    required this.onUpdated,
  });

  @override
  ConsumerState<_StudentEditSheet> createState() => _StudentEditSheetState();
}

class _StudentEditSheetState extends ConsumerState<_StudentEditSheet> {
  late TextEditingController _nameController;
  late TextEditingController _rollController;
  late TextEditingController _emailController;
  late String _selectedDept;
  late String _selectedYear;

  Uint8List? _newPhotoBytes;
  String? _newPhotoFilename;
  bool _isSaving = false;
  String? _statusText;

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    final s = widget.student;
    _nameController = TextEditingController(text: s['full_name'] as String? ?? '');
    _rollController = TextEditingController(text: s['roll_number'] as String? ?? '');
    _emailController = TextEditingController(text: '${(_rollController.text).toLowerCase()}@kucet.ac.in');
    _selectedDept = (s['department_code'] as String? ?? 'CSE').toUpperCase();
    if (!widget.departments.contains(_selectedDept)) {
      _selectedDept = widget.departments.first;
    }
    _selectedYear = '2023-2027';
  }

  @override
  void dispose() {
    _nameController.dispose();
    _rollController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 98,
        preferredCameraDevice: CameraDevice.front,
      );
      if (file == null) return;
      final bytes = await file.readAsBytes();
      setState(() {
        _newPhotoBytes = bytes;
        _newPhotoFilename = file.name;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to pick photo: $e'), backgroundColor: AppTheme.errorRed),
      );
    }
  }

  Future<void> _commitFullUpdate() async {
    final studentId = widget.student['student_id'] as String? ?? widget.student['roll_number'] as String;
    setState(() {
      _isSaving = true;
      _statusText = 'Rewriting student details in PostgreSQL...';
    });

    try {
      final api = ref.read(apiProvider);

      // 1. Update Details
      await api.updateStudentDetails(
        studentId: studentId,
        fullName: _nameController.text.trim(),
        rollNumber: _rollController.text.trim().toUpperCase(),
        departmentCode: _selectedDept,
        academicYear: _selectedYear,
        institutionalEmail: _emailController.text.trim(),
      );

      // 2. If new photo was captured on device, upload to Cloudinary and update embeddings!
      if (_newPhotoBytes != null) {
        setState(() => _statusText = 'Uploading to Cloudinary & recalculating AI embeddings...');
        await api.updateStudentPhoto(
          studentId: _rollController.text.trim().toUpperCase(),
          photoBytes: _newPhotoBytes!,
          filename: _newPhotoFilename ?? 'photo_${_rollController.text.trim()}.jpg',
        );
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Student details & biometrics updated in database successfully.'),
            backgroundColor: AppTheme.statusMatched,
          ),
        );
        widget.onUpdated();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _statusText = null;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Update failed: $e'), backgroundColor: AppTheme.errorRed),
        );
      }
    }
  }

  Future<void> _deletePhoto() async {
    final studentId = widget.student['student_id'] as String? ?? widget.student['roll_number'] as String;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Student Photo'),
        content: const Text(
          'Permanently purge face embeddings and reference photo from PostgreSQL database for this student?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorRed, foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete Photo'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ref.read(apiProvider).deleteStudentPhoto(studentId: studentId);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Photo & embeddings deleted from database.')),
          );
          widget.onUpdated();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed: $e'), backgroundColor: AppTheme.errorRed),
          );
        }
      }
    }
  }

  Future<void> _deleteStudent() async {
    final studentId = widget.student['student_id'] as String? ?? widget.student['roll_number'] as String;
    final roll = widget.student['roll_number'] as String;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Student Record'),
        content: Text(
          'Permanently delete student $roll and all associated biometric records completely from the database?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorRed, foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Confirm Delete Student'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ref.read(apiProvider).deleteStudent(studentId: studentId);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Student deleted permanently from database.')),
          );
          widget.onUpdated();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed: $e'), backgroundColor: AppTheme.errorRed),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final photoB64 = widget.student['reference_photo_base64'] as String?;

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Modal Header
            Row(
              children: [
                const Icon(Icons.edit_note_rounded, color: AppTheme.primaryNavy, size: 24),
                const SizedBox(width: 10),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Developer Rewrite & Photo Control', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text('Direct database rewrite for koushikkatkam@gmail.com', style: TextStyle(fontSize: 11, color: AppTheme.textMutedLight)),
                    ],
                  ),
                ),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
              ],
            ),

            const SizedBox(height: 14),
            const Divider(),
            const SizedBox(height: 10),

            // Photo Management Section
            const Text('Student Biometric Photo', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 8),

            Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Container(
                    width: 72,
                    height: 86,
                    color: Colors.grey.shade200,
                    child: _newPhotoBytes != null
                        ? Image.memory(_newPhotoBytes!, fit: BoxFit.cover)
                        : (photoB64 != null
                            ? Image.memory(base64Decode(photoB64.split(',').last), fit: BoxFit.cover)
                            : const Icon(Icons.person, size: 36, color: Colors.grey)),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _newPhotoBytes != null ? 'New photo ready to commit' : 'Current photo in Cloudinary',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: _newPhotoBytes != null ? AppTheme.statusMatched : AppTheme.textMainLight,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: [
                          OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                            icon: const Icon(Icons.camera_alt_outlined, size: 14),
                            label: const Text('Camera', style: TextStyle(fontSize: 12)),
                            onPressed: () => _pickPhoto(ImageSource.camera),
                          ),
                          OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
                            icon: const Icon(Icons.photo_library_outlined, size: 14),
                            label: const Text('Gallery', style: TextStyle(fontSize: 12)),
                            onPressed: () => _pickPhoto(ImageSource.gallery),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),

            // Student Information Fields
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name *',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),

            TextFormField(
              controller: _rollController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Roll Number *',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedDept,
                    decoration: const InputDecoration(labelText: 'Branch / Dept', border: OutlineInputBorder(), isDense: true),
                    items: widget.departments.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedDept = val);
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedYear,
                    decoration: const InputDecoration(labelText: 'Batch / Year', border: OutlineInputBorder(), isDense: true),
                    items: widget.academicYears.map((y) => DropdownMenuItem(value: y, child: Text(y))).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedYear = val);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            TextFormField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Institutional Email',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),

            const SizedBox(height: 20),

            // Submit Button
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryNavy,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: _isSaving
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.save_rounded, size: 20),
                label: Text(
                  _isSaving ? (_statusText ?? 'Committing Changes...') : 'Commit Database Changes',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                onPressed: _isSaving ? null : _commitFullUpdate,
              ),
            ),

            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),

            // Danger Destruction Actions
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.accentGold,
                      side: const BorderSide(color: AppTheme.accentGold),
                    ),
                    icon: const Icon(Icons.image_not_supported_outlined, size: 16),
                    label: const Text('Purge Photo', style: TextStyle(fontSize: 12)),
                    onPressed: _deletePhoto,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.errorRed,
                      side: const BorderSide(color: AppTheme.errorRed),
                    ),
                    icon: const Icon(Icons.delete_forever_rounded, size: 16),
                    label: const Text('Delete Student', style: TextStyle(fontSize: 12)),
                    onPressed: _deleteStudent,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
